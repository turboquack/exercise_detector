# exercise_detector
This is port of my last student project, moving it from Arduino Nano 33 BLE Sense to Pico W.<br>
The goal is for the microcontroller placed in the handle of the weight to be able to detect the exercise performed by the user using IMU and tensorflow lite.<br>
# Hardware
Raspberry Pi Pico W<br>
10-DOF IMU Sensor Module for Raspberry Pi Pico, onboard ICM20948 and LPS22HB chip<br>
18650 Battery Shield V3
# To do list
Send IMU data to server running on pc for futher ML traning :white_check_mark:<br>
Recive data, need to change it to using [flet](https://flet.dev/) :x: <br>
Train data, old jupyter notebook sketch, need to be adujsted for new data :x:<br>
Running interference on Pico :x:<br>
