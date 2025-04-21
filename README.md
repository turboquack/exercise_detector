# exercise_detector
This is port of my last student project, moving it from Arduino Nano 33 BLE Sense to Pico W.<br>
The goal is for the microcontroller placed in the handle of the weight to be able to detect the exercise performed by the user using IMU and tensorflow lite.<br>
# Hardware
Raspberry Pi Pico W<br>
10-DOF IMU Sensor Module for Raspberry Pi Pico, onboard ICM20948 and LPS22HB chip<br>
18650 Battery Shield V3
# Software
[icm20948 and lps22hb](https://www.waveshare.com/wiki/Pico-10DOF-IMU)<br>
# To do list
Send IMU data to server running on pc for futher ML traning :white_check_mark:<br>
Recive data, need to change it to using [flet](https://flet.dev/) :white_check_mark: <br>


![alt text](https://github.com/turboquack/exercise_detector/blob/main/pictures/Screenshot_20250421_224007.png)<br>

Collect data :x:<br>
Train data, old jupyter notebook sketch, need to be adujsted for new data :x:<br>
Running interference on Pico :x:<br>
