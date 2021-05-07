import time
from datetime import datetime

from auth import Configuration, DataContext, ScourAt
from slots import AppointmentSeekerFactory


def run():
    data_context = DataContext(phone_no=NUMBER,
                               name=NAME,
                               dose_no=DOSE,
                               state_name=STATE_NAME,
                               district_name=DISTRICT_NAME,
                               pin_code=PINCODE,
                               age_category=MIN_AGE_LIMIT,
                               wanna_book_appointment=WANNA_BOOK_APPOINTMENT)
    data_context.set_scouring_mechanism(ScourAt.DISTRICT_LEVEL)

    while True:

        appointment_seeker = AppointmentSeekerFactory()
        appointment_seeker.execute(data_context)

        print(f"{datetime.now()} Retrying in {Configuration.TIME_PERIOD} seconds")
        time.sleep(Configuration.TIME_PERIOD)


if __name__ == '__main__':
    NUMBER = "9880933521"  # Enter phone number registered in cowin
    NAME = "Yogesh Sharma"  # Enter the name that was registered in cowin
    DOSE = 1  # first or second dose
    MIN_AGE_LIMIT = 18  # Enter age limit - 18 or 45

    # Enter these details
    STATE_NAME = 'Gujarat'
    DISTRICT_NAME = 'Ahmedabad'
    PINCODE = "380063"

    TIME_PERIOD = 10  # Check for slots every N seconds, recommended = 10, do not update

    # Uncomment the line below if want to book and not only explore
    WANNA_BOOK_APPOINTMENT = False

    run()
