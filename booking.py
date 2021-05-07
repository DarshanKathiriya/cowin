import requests

from auth import Configuration, DataContext


class Booking:

    __data_context: DataContext = None
    __base_url = f"{Configuration.SERVER_BASE_URL}/appointment/schedule"

    def __init__(self, context: DataContext):
        self.__data_context = context

    def book_with_retry(self, booking_request):
        if not self.__data_context.wanna_book_appointment:
            return

        response = requests.post(self.__base_url,
                                 headers=Configuration.authenticated_request_header(self.__data_context),
                                 json=booking_request)
        if response.status_code == 401:
            print("Token Expired")
            Configuration.update_token(self.__data_context)
            response = requests.post(self.__base_url,
                                     headers=Configuration.authenticated_request_header(self.__data_context),
                                     json=booking_request)

        booked = response.status_code == 200
        if not booked:
            print(f"Could not book.. Response: {response.json()}")

        return booked
