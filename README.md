# Driver Drowsiness Detection System

- A system which alarms the driver as soon as it detects that the driver is becoming drowsy to prevent any road accident.
- Drowsiness is detected by calculating eye aspect ratio and mouth aspect ratio and comparing it with the threshold value.
- The threshold value of the eye aspect ratio is calculated dynamically from the maximum and minimum eye aspect ratios.
- An alarm is triggered if a driver is drowsy for 20 consecutive frames.

## How to run Application:

1. Clone/download repository in local machine.
2. Open the terminal in the project repository.
3. Run the command: py manage.py runserver
