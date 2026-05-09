# c02sensor-w-QTPy-and-TFT-LCD
CircuitPython, QT Py ESP32-S3, and Adafruit 1.44" Color TFT LCD Display with MicroSD Card breakout - ST7735R

https://github.com/user-attachments/assets/07cf616a-4d9e-4513-adb9-7e6271371a87

The SGP-30 provides approximate CO₂ and VOC (volatile organic compound) readings. It is an inexpensive sensor, but less accurate than dedicated CO₂ sensors and requires a 12-hour calibration period for best results. To handle power interruptions gracefully, the code saves calibration baseline values to the board and reloads them on restart — giving more accurate readings sooner if the board reboots unexpectedly.

Note: If you move the sensor to a new location, delete sgp30_baseline.json from the CIRCUITPY drive to force a fresh 12-hour recalibration.

Here is a look at the display setup for the 128×128 TFT:

- The large center value is CO₂ in ppm (parts per million). Typical indoor air ranges from 400–800 ppm; above 1000 ppm indicates poor ventilation.
- A green smile icon appears when CO₂ is below 1000 ppm.
- It becomes a red frown when CO₂ reaches 1000 ppm or above.
- The smaller value is TVOC in ppb (parts per billion). The VOC label above it is green when below 660 ppb and red at 660 ppb or above.
- The onboard LED lights up when either threshold is exceeded.

![sgp30-and-display](https://github.com/user-attachments/assets/b2a496ca-b645-41b2-90a1-3b481ed8dbde)
