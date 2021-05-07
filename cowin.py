import time
from datetime import datetime

from auth import Configuration, DataContext, ScourAt
from slots import AppointmentSeeker

WANNA_BOOK_APPOINTMENT = False


def run():
    data_context = DataContext(phone_no=NUMBER,
                               name=NAME,
                               dose_no=DOSE,
                               state_name=STATE_NAME,
                               district_name=DISTRICT_NAME,
                               pin_code=PINCODE,
                               age_category=MIN_AGE_LIMIT,
                               wanna_book_appointment=WANNA_BOOK_APPOINTMENT)
    data_context.set_scouring_mechanism(ScourAt.PIN_CODE_LEVEL)

    while True:

        appointment_seeker = AppointmentSeeker(data_context)
        appointment_seeker.execute()

        print(f"{datetime.now()} Retrying in {Configuration.TIME_PERIOD} seconds")
        time.sleep(Configuration.TIME_PERIOD)


if __name__ == '__main__':
    NUMBER = "enter-your-10-digit-number"  # Enter phone number registered in cowin
    NAME = "enter-your-name"  # Enter the name that was registered in cowin
    DOSE = 1  # first or second dose
    MIN_AGE_LIMIT = 18  # Enter age limit - 18 or 45

    # Enter these details
    PINCODE = "enter-pincode"
    STATE_NAME = 'enter-state-name'
    DISTRICT_NAME = 'enter-district-name'

    TIME_PERIOD = 10  # Check for slots every N seconds, recommended = 10, do not update

    # Uncomment the line below if want to book and not only explore
    # WANNA_BOOK_APPOINTMENT = True

    run()
