from hashlib import sha256

import requests

from utils import display_message


class ScourAt:
    PIN_CODE_LEVEL = 'pin_code_as_input'
    DISTRICT_LEVEL = 'district_as_input'


class DataContext:

    __token = None
    __exploring_counter = 0

    name = None
    dose_no = None
    phone_no = None

    pin_code = None
    state_name = None
    district_name = None

    state_id = None
    district_ids = None

    age_category = None
    scouring_mechanism = ScourAt.PIN_CODE_LEVEL
    wanna_book_appointment = False

    user_agent = "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:77.0) Gecko/20190101 Firefox/77.0"

    def __init__(self, phone_no, name, dose_no, state_name, district_name, pin_code, age_category,
                 wanna_book_appointment=False) -> None:
        super().__init__()
        self.phone_no = phone_no
        self.name = name
        self.dose_no = dose_no
        self.state_name = str(state_name).lower()
        self.district_name = str(district_name).lower()
        self.pin_code = pin_code
        self.age_category = age_category
        self.wanna_book_appointment = wanna_book_appointment

        self.district_ids = list()

    def get_token(self):
        return self.__token

    def set_token(self, token):
        self.__token = token

    def append_district_id(self, district_id):
        self.district_ids.append(district_id)

    def reset_district_details(self):
        self.state_id = None
        self.district_ids = list()

    def set_state_id(self, state_id):
        self.state_id = state_id

    def set_scouring_mechanism(self, scouring_mechanism):
        self.scouring_mechanism = scouring_mechanism

    def set_user_agent(self, user_agent):
        self.user_agent = user_agent

    def get_scouring_counter(self):
        return self.__exploring_counter

    def increase_scouring_counter(self):
        self.__exploring_counter += 1

    def reset_scouring_counter(self):
        self.__exploring_counter = 0

    def get_area_ids(self):
        return self.district_ids if self.scouring_mechanism == ScourAt.DISTRICT_LEVEL else [self.pin_code]


class Configuration:

    SERVER_BASE_URL = "https://cdn-api.co-vin.in/api/v2"

    MAX_SLOT_RETRY_COUNT = 20
    MAX_CENTER_RETRY_COUNT = 100
    MAX_AREA_EXPLORING_RETRIES = 5

    TIME_PERIOD = 10  # Check for slots every N seconds, recommended = 10, do not update

    @staticmethod
    def update_token(context: DataContext):
        data = {
            "mobile": context.phone_no,
            "secret": "U2FsdGVkX1/3I5UgN1RozGJtexc1kfsaCKPadSux9LY+cVUADlIDuKn0wCN+Y8iB4ceu6gFxNQ5cCfjm1BsmRQ=="
        }

        response = requests.post(f"{Configuration.SERVER_BASE_URL}/auth/generateMobileOTP", json=data,
                                 headers=Configuration.public_request_header())
        if response.status_code != 200:
            raise ValueError(f"Invalid response while requesting OTP: {response.json()}")

        txn_id = response.json()["txnId"]
        display_message("Enter OTP in terminal")
        otp = input("Enter OTP: ")

        data = {"otp": sha256(str(otp).encode('utf-8')).hexdigest(), "txnId": txn_id}
        print(f"Validating OTP..")

        response = requests.post(url=f"{Configuration.SERVER_BASE_URL}/auth/validateMobileOtp", json=data,
                                 headers=Configuration.public_request_header())
        if response.status_code != 200:
            raise ValueError(f"Invalid response while validating OTP: {response.json()}")

        token = response.json()["token"]
        context.set_token(token)
        print(f"Generated token: {token}")

    @staticmethod
    def public_request_header(context: DataContext):
        return {
            "user-agent": context.user_agent
        }

    @staticmethod
    def authenticated_request_header(context: DataContext):
        return {
            "Authorization": f"Bearer {context.get_token()}",
            "user-agent": context.user_agent
        }
