# cowin

`cowin.py` books appointment as soon as a slot is found. **_This will book the first available slot in the first available center in your pincode_**. 

Steps:
1. Update _NUMBER, NAME, DOSE, MIN_AGE_LIMIT, PINCODE_ at the bottom of the file before running this. Instructions are provided on how to update it.
2. Once you receive an alert to enter OTP, you will get the OTP on your phone which you will have to enter in your terminal. Sometimes you might get logged out over time, and you will be prompted to enter OTP again. 
3. Run it as `python cowin.py`. Do not use `python3` in Mac, there is some problem with IDLE and Mac. Ensure that `python --version` gives 3.x version.
4. If you still get a bug where the alert does not disappear after clicking ok (in Mac), you can ignore the error.
