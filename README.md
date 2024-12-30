# c02sensor-w-QTPy-and-TFT-LCD
CircuitPython, QT Py ESP32-S3, and Adafruit 1.44" Color TFT LCD Display with MicroSD Card breakout - ST7735R

https://github.com/user-attachments/assets/07cf616a-4d9e-4513-adb9-7e6271371a87

The SGP-30 only gives an approximate co2 and voc (volitile compounds) reading. This sensor is cheapter, but less accurate & takes more time to calibrate. The code using this sensor is more complex because I save the calibration so it can read in any calibration values (if available) when rebooting, which hopefully gives a more accurate reading if, say, the power goes out & the board needs to be restarted.

Here is a look at the display setup I've created for the 128x128 TFT.
- The large value is co2 ppm/1000.
- The green smile face is when this value is below 1000
- It turns into a red frown face when this value is 1000 or above
- The voc value is in ppb (parts per billion). The VOC label above it is green when value is below 250, red when 250 or above.

![sgp30-and-display](https://github.com/user-attachments/assets/b2a496ca-b645-41b2-90a1-3b481ed8dbde)
