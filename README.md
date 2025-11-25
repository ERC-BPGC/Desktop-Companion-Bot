# IMU-Controlled Animated Face & Media Controller

An interactive desktop companion that displays an animated face on an ESP32-connected TFT screen. It uses an MPU6050 accelerometer to detect physical gestures, allowing you to control media on your computer (Volume, Play/Pause, Tracks) simply by tilting or lifting the device.

##  Features

* **Gesture Control**: Detects tilts and lifts to send media commands via Serial.
* **Animated Interface**: Features smooth eye movements, blinking, and expression changes (Smile, Sad, Normal) based on orientation.
* **Media Actions**: Controls Volume, Track Navigation, and Play/Pause on the host PC.
* **Visuals**: Includes a JPEG startup logo and dynamic facial expressions.

##  Hardware Requirements

* **ESP32 Development Board** 
* **TFT LCD Display** (Compatible with `TFT_eSPI`, e.g., ILI9341, ST7789) 
* **MPU6050** Accelerometer/Gyroscope 
* **USB Cable** (For data connection)

##  Software Dependencies

### Arduino IDE Libraries
Install these via the Arduino Library Manager:
1.  **TFT_eSPI** (by Bodmer) 
2.  **Adafruit MPU6050** (by Adafruit)
3.  **Adafruit Unified Sensor** (by Adafruit)
4.  **TJpg_Decoder** (by Bodmer) 

### Python (Host Computer)
Required for the media control script:
```bash
pip install pyserial pyautogui
