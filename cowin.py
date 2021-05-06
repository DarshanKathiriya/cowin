import datetime
import time
import tkinter as tk
from datetime import date
from hashlib import sha256
from tkinter import messagebox

import requests


def get_calendar():
    response = requests.get(
        f"https://cdn-api.co-vin.in/api/v2/appointment/sessions/public/calendarByPin?pincode={PINCODE}&date={date.today().strftime('%d-%m-%Y')}",
        headers=public_request_header())

    if response.status_code != 200:
        print(
            f"{datetime.datetime.now()} Invalid response code while finding by pincode: {response.status_code}. Retrying in {TIME_PERIOD} seconds")
        time.sleep(TIME_PERIOD)
        return get_calendar()

    return response.json()


def display_message(center):
    top = tk.Tk()
    top.withdraw()
    messagebox.showinfo("Cowin registration", f"{center}", master=top)
    top.destroy()


def authenticated_request_header():
    return {
        "Authorization": f"Bearer {token}",
        "user-agent": USER_AGENT
    }


def public_request_header():
    return {
        "user-agent": USER_AGENT
    }


def update_token():
    data = {
        "mobile": int(NUMBER),
        "secret": "U2FsdGVkX1/cvoue2qat3566bxHk79jZlZiy25mf+APCgU9rVOi7mNhAdg3BQfLOWDBsLxU+3VRVX/ZrTO/v9w=="
    }

    response = requests.post("https://cdn-api.co-vin.in/api/v2/auth/generateMobileOTP", json=data,
                             headers=public_request_header())
    if response.status_code != 200:
        raise ValueError(f"Invalid response while requesting OTP: {response.json()}")

    txn_id = response.json()["txnId"]
    display_message("Enter OTP in terminal")
    otp = input("Enter OTP: ")

    data = {"otp": sha256(str(otp).encode('utf-8')).hexdigest(), "txnId": txn_id}
    print(f"Validating OTP..")

    response = requests.post(url='https://cdn-api.co-vin.in/api/v2/auth/validateMobileOtp', json=data,
                             headers=public_request_header())
    if response.status_code != 200:
        raise ValueError(f"Invalid response while validating OTP: {response.json()}")

    global token
    token = response.json()["token"]
    print(f"Generated token: {token}")


def get_beneficiary_reference_id():
    response = requests.get(
        "https://cdn-api.co-vin.in/api/v2/appointment/beneficiaries", headers=authenticated_request_header())

    if response.status_code == 401:
        update_token()
        response = requests.get(
            "https://cdn-api.co-vin.in/api/v2/appointment/beneficiaries", headers=authenticated_request_header())

    if response.status_code != 200:
        raise ValueError(f"Invalid response while getting beneficiaries: {response.json()}")

    names = []
    for beneficiary in response.json()["beneficiaries"]:
        if NAME == beneficiary["name"]:
            return beneficiary["beneficiary_reference_id"]
        names.append(beneficiary["name"])

    raise ValueError(f"Input beneficiary name does not match the registered beneficiaries: {names}")


def check_and_book_appointment(beneficiary_reference_id, calendar):
    for center in calendar["centers"]:

        if center["fee_type"] != "Free":
            continue

        center_id = center['center_id']

        for session in center["sessions"]:

            if session["available_capacity"] > 0 and session["min_age_limit"] == MIN_AGE_LIMIT:

                print(f"Attempting booking in {center['name']}")
                session_id = session["session_id"]

                for slot in session["slots"]:
                    booking_request = {
                        'beneficiaries': [beneficiary_reference_id],
                        'dose': DOSE,
                        'center_id': center_id,
                        'session_id': session_id,
                        'slot': slot
                    }
                    booked = book_with_retry(booking_request)
                    if booked:
                        print(f"Appointment booked for {slot}")
                        display_message(f"Appointment booked for {slot}")
                        return True

    return False


def book_with_retry(booking_request):
    response = requests.post("https://cdn-api.co-vin.in/api/v2/appointment/schedule",
                             headers=authenticated_request_header(),
                             json=booking_request)
    if response.status_code == 401:
        print("Token Expired")
        update_token()
        response = requests.post("https://cdn-api.co-vin.in/api/v2/appointment/schedule",
                                 headers=authenticated_request_header(),
                                 json=booking_request)

    booked = response.status_code == 200
    if not booked:
        print(f"Could not book.. Response: {response.json()}")

    return booked


def run():
    update_token()

    beneficiary_reference_id = get_beneficiary_reference_id()
    print(f"Beneficiary id is {beneficiary_reference_id}")

    while True:
        calendar = get_calendar()
        if check_and_book_appointment(beneficiary_reference_id, calendar):
            return
        print(f"{datetime.datetime.now()} Retrying in {TIME_PERIOD} seconds")
        time.sleep(TIME_PERIOD)


if __name__ == '__main__':
    NUMBER = "enter-your-10-digit-number"  # Enter phone number registered in cowin
    NAME = "enter-your-name"  # Enter the name that was registered in cowin
    DOSE = 1  # first or second dose
    MIN_AGE_LIMIT = 18  # Enter age limit - 18 or 45
    PINCODE = "enter-pincode"  # Enter pincode here

    TIME_PERIOD = 10  # Check for slots every N seconds, recommended = 10, do not update

    token = ""  # Advanced use only, ignore this
    USER_AGENT = "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:77.0) Gecko/20190101 Firefox/77.0"

    run()
