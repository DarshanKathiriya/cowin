import time
from datetime import date, datetime
from pprint import pprint

import requests

from auth import Configuration, DataContext, ScourAt
from booking import Booking
from utils import display_message


class CalendarFetcher:

    __base_url = None
    __data_context: DataContext = None

    def __init__(self, context: DataContext):
        self.__data_context = context

    def get_url(self):
        data_fetching_mode = self.__data_context.scouring_mechanism
        url_fetcher = {
            ScourAt.PIN_CODE_LEVEL: f"{Configuration.SERVER_BASE_URL}/appointment/sessions/calendarByPin",
            ScourAt.DISTRICT_LEVEL: f"{Configuration.SERVER_BASE_URL}/appointment/sessions/calendarByDistrict"
        }
        self.__base_url = url_fetcher[data_fetching_mode]

        params_fetcher = {
            ScourAt.PIN_CODE_LEVEL: f"?pincode={self.__data_context.pin_code}",
            ScourAt.DISTRICT_LEVEL: f"?district_id={self.__data_context.district_id}"
        }
        query_params = params_fetcher[data_fetching_mode]
        return f"{self.__base_url}?{query_params}&date={date.today().strftime('%d-%m-%Y')}"

    def get_calender(self):
        if self.__data_context.get_scouring_counter() >= Configuration.MAX_AREA_EXPLORING_RETRIES:
            self.change_scouring_mechanism()

        response = requests.get(self.get_url(), headers=Configuration.public_request_header(self.__data_context))

        if response.status_code != 200:
            self.__data_context.increase_scouring_counter()
            print(
                f"{datetime.now()} Invalid response code while finding details using {self.__data_context.scouring_mechanism.replace('_', ' ')}:"
                f" {response.status_code}. Retrying in {Configuration.TIME_PERIOD} seconds")
            time.sleep(Configuration.TIME_PERIOD)
            return self.get_calender()
        else:
            self.__data_context.reset_scouring_counter()

        return response.json()

    def change_scouring_mechanism(self):
        if self.__data_context.scouring_mechanism == ScourAt.PIN_CODE_LEVEL:
            self.__data_context.set_scouring_mechanism(ScourAt.DISTRICT_LEVEL)
        else:
            self.__data_context.set_scouring_mechanism(ScourAt.PIN_CODE_LEVEL)


class AppointmentSeeker:

    __data_context: DataContext = None
    __base_url = f"{Configuration.SERVER_BASE_URL}/appointment/beneficiaries"

    def __init__(self, data_context: DataContext):
        self.__data_context = data_context

    def get_beneficiary_reference_id(self):

        if not self.__data_context.wanna_book_appointment:
            return None

        response = requests.get(self.__base_url, headers=Configuration.authenticated_request_header(self.__data_context))
        if response.status_code == 401:
            Configuration.update_token(self.__data_context)
            response = requests.get(self.__base_url, headers=Configuration.authenticated_request_header(self.__data_context))

        if response.status_code != 200:
            raise ValueError(f"Invalid response while getting beneficiaries: {response.json()}")

        names = []
        for beneficiary in response.json()["beneficiaries"]:
            if self.__data_context.name == beneficiary["name"]:
                beneficiary_reference_id = beneficiary["beneficiary_reference_id"]
                print(f"Beneficiary id is {beneficiary_reference_id}")
                return beneficiary_reference_id
            names.append(beneficiary["name"])

        raise ValueError(f"Input beneficiary name does not match the registered beneficiaries: {names}")

    def check_and_book_appointment(self, beneficiary_reference_id, calendar):
        raise NotImplemented('Implement me')

    def execute(self):
        beneficiary_reference_id = self.get_beneficiary_reference_id()

        calender_details = CalendarFetcher(self.__data_context)
        calendar = calender_details.get_calender()
        if self.check_and_book_appointment(beneficiary_reference_id, calendar):
            return


class DummySeeker(AppointmentSeeker):

    def execute(self):
        return True


class PinCodeSpecificAppointmentSeeker(AppointmentSeeker):

    def check_and_book_appointment(self, beneficiary_reference_id, calendar):
        slot_retry_count = 0
        center_retry_count = 0

        bookie = Booking(self.__data_context)

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

                if session["available_capacity"] > 0 and session["min_age_limit"] == self.__data_context.age_category:

                    session_id = session["session_id"]
                    for slot in session["slots"]:
                        booking_request = {
                            'beneficiaries': [beneficiary_reference_id],
                            'dose': self.__data_context.dose_no,
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


class DistrictSpecificAppointmentSeeker(AppointmentSeeker):

    def check_and_book_appointment(self, beneficiary_reference_id, calendar):
        pass


class AppointmentSeekerFactory:

    def execute(self, data_context: DataContext):
        if data_context.wanna_book_appointment:
            Configuration.update_token(data_context)

        explorer_map = {
            ScourAt.PIN_CODE_LEVEL: PinCodeSpecificAppointmentSeeker,
            ScourAt.DISTRICT_LEVEL: DistrictSpecificAppointmentSeeker,
        }

        finder_klaaz = explorer_map.get(data_context.scouring_mechanism, DummySeeker)
        finder = finder_klaaz(data_context)
        return finder.execute()
