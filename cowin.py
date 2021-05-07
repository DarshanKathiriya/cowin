import datetime
import time
import tkinter as tk
from datetime import date
from hashlib import sha256
from pprint import pprint
from tkinter import messagebox

import requests


def display_message(center):
    top = tk.Tk()
    top.withdraw()
    messagebox.showinfo("Cowin registration", f"{center}", master=top)
    top.destroy()


class Booking:
    __wanna_book = None
    __base_url = "https://cdn-api.co-vin.in/api/v2/appointment/schedule"

    def __init__(self):
        self.__wanna_book = Configuration.WANNA_BOOK_APPOINTMENT

    def book_with_retry(self, booking_request):
        if not self.__wanna_book:
            return

        response = requests.post(self.__base_url, headers=Configuration.Configuration.request_header(),
                                 json=booking_request)
        if response.status_code == 401:
            print("Token Expired")
            Configuration.update_token()
            response = requests.post(self.__base_url, headers=Configuration.request_header(), json=booking_request)

        booked = response.status_code == 200
        if not booked:
            print(f"Could not book.. Response: {response.json()}")

        return booked


class CalendarFetcher:
    __base_url = None

    class At:
        PIN_CODE_LEVEL = 'pin_code_as_input'
        DISTRICT_LEVEL = 'district_as_input'

    def get_url(self, data_fetching_mode):
        url_fetcher = {
            CalendarFetcher.At.PINCODE: f"https://cdn-api.co-vin.in/api/v2/appointment/sessions/calendarByPin",
            CalendarFetcher.At.DISTRICT_LEVEL: f"https://cdn-api.co-vin.in/api/v2/appointment/sessions/calendarByPin"
        }
        self.__base_url = url_fetcher[data_fetching_mode]

        params_fetcher = {
            CalendarFetcher.At.PINCODE: f"?pincode={PIN_CODE_LEVEL}&date={date.today().strftime('%d-%m-%Y')}",
            CalendarFetcher.At.DISTRICT_LEVEL: ""
        }
        query_params = params_fetcher[data_fetching_mode]
        return f"{self.__base_url}?{query_params}"

    def get_calender(self, data_fetching_mode: str):
        response = requests.get(self.get_url(data_fetching_mode))

        if response.status_code != 200:
            print(
                f"{datetime.datetime.now()} Invalid response code while finding by pincode: {response.status_code}. "
                f"Retrying in {Configuration.TIME_PERIOD} seconds")
            time.sleep(Configuration.TIME_PERIOD)
            return self.get_calender(data_fetching_mode)

        return response.json()


class AppointmentSeeker:
    __base_url = "https://cdn-api.co-vin.in/api/v2/appointment/beneficiaries"

    def get_beneficiary_reference_id(self, ):
        response = requests.get(self.__base_url, headers=Configuration.request_header())

        if response.status_code == 401:
            Configuration.update_token()
            response = requests.get(self.__base_url, headers=Configuration.request_header())

        if response.status_code != 200:
            raise ValueError(f"Invalid response while getting beneficiaries: {response.json()}")

        names = []
        for beneficiary in response.json()["beneficiaries"]:
            if NAME == beneficiary["name"]:
                return beneficiary["beneficiary_reference_id"]
            names.append(beneficiary["name"])

        raise ValueError(f"Input beneficiary name does not match the registered beneficiaries: {names}")

    def execute_internal(self, data_fetching_mode: str):
        beneficiary_reference_id = self.get_beneficiary_reference_id()
        print(f"Beneficiary id is {beneficiary_reference_id}")

        calender_details = CalendarFetcher()
        calendar = calender_details.get_calender(data_fetching_mode)
        if self.check_and_book_appointment(beneficiary_reference_id, calendar):
            return

    def check_and_book_appointment(self, beneficiary_reference_id, calendar):
        pass


class DummySeeker(AppointmentSeeker):

    def execute(self):
        pass


class PinCodeSpecificAppointmentSeeker(AppointmentSeeker):

    def check_and_book_appointment(self, beneficiary_reference_id, calendar):
        slot_retry_count = 0
        center_retry_count = 0

        bookie = Booking()

        for center in calendar["centers"]:

            if center["fee_type"] != "Free":
                continue

            center_retry_count += 1
            center_id = center['center_id']

            if center_retry_count >= Configuration.MAX_CENTER_RETRY_COUNT:
                print("I am done exploring centers for today, arrrghhh!!")
                return False

            print(f"Center details: {pprint(center)}")
            for session in center["sessions"]:

                if session["available_capacity"] > 0 and session["min_age_limit"] == MIN_AGE_LIMIT:

                    session_id = session["session_id"]
                    for slot in session["slots"]:
                        booking_request = {
                            'beneficiaries': [beneficiary_reference_id],
                            'dose': DOSE,
                            'center_id': center_id,
                            'session_id': session_id,
                            'slot': slot
                        }

                        slot_retry_count += 1
                        booked = bookie.book_with_retry(booking_request)
                        if booked:
                            print(f"Appointment booked for {slot}")
                            display_message(f"Appointment booked for {slot}")
                            return True

                        if slot_retry_count >= Configuration.MAX_SLOT_RETRY_COUNT:
                            print("Enough for today, eh!?")
                            return False

        return False

    def execute(self):
        self.execute_internal(CalendarFetcher.At.PINCODE)


class DistrictSpecificAppointmentSeeker(AppointmentSeeker):

    def execute(self):
        self.execute_internal(CalendarFetcher.At.DISTRICT_LEVEL)


class Configuration:
    MAX_SLOT_RETRY_COUNT = 20
    MAX_CENTER_RETRY_COUNT = 100

    WANNA_BOOK_APPOINTMENT = False
    TIME_PERIOD = 10  # Check for slots every N seconds, recommended = 10, do not update

    EXPLORER_COVERAGE = CalendarFetcher.At.DISTRICT_LEVEL

    @staticmethod
    def request_header():
        return {"Authorization": f"Bearer {token}"}

    @staticmethod
    def update_token():
        data = {
            "mobile": NUMBER,
            "secret": "U2FsdGVkX1/3I5UgN1RozGJtexc1kfsaCKPadSux9LY+cVUADlIDuKn0wCN+Y8iB4ceu6gFxNQ5cCfjm1BsmRQ=="
        }

        response = requests.post("https://cdn-api.co-vin.in/api/v2/auth/generateMobileOTP", json=data)
        if response.status_code != 200:
            raise ValueError(f"Invalid response while requesting OTP: {response.json()}")

        txn_id = response.json()["txnId"]
        display_message("Enter OTP in terminal")
        otp = input("Enter OTP: ")

        data = {"otp": sha256(str(otp).encode('utf-8')).hexdigest(), "txnId": txn_id}
        print(f"Validating OTP..")

        response = requests.post(url='https://cdn-api.co-vin.in/api/v2/auth/validateMobileOtp', json=data)
        if response.status_code != 200:
            raise ValueError(f"Invalid response while validating OTP: {response.json()}")

        global token
        token = response.json()["token"]
        print(f"Generated token: {token}")


def run():
    Configuration.update_token()
    explorer_map = {
        CalendarFetcher.At.PINCODE: PinCodeSpecificAppointmentSeeker,
        CalendarFetcher.At.DISTRICT_LEVEL: DistrictSpecificAppointmentSeeker,
    }

    finder_klaaz = explorer_map.get(Configuration.EXPLORER_COVERAGE, DummySeeker)
    finder = finder_klaaz()
    while True:
        finder.execute()
        print(f"{datetime.datetime.now()} Retrying in {Configuration.TIME_PERIOD} seconds")
        time.sleep(Configuration.TIME_PERIOD)


if __name__ == '__main__':
    NUMBER = "enter-your-10-digit-number"  # Enter phone number registered in cowin
    NAME = "enter-your-name"  # Enter the name that was registered in cowin
    DOSE = 1  # first or second dose
    MIN_AGE_LIMIT = 18  # Enter age limit - 18 or 45
    PINCODE = "enter-pincode"  # Enter pincode here

    TIME_PERIOD = 10  # Check for slots every N seconds, recommended = 10, do not update

    token = ""  # Advanced use only, ignore this

    run()
