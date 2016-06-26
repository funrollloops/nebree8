#if defined(ARDUINO) && ARDUINO >= 100
  #include "Arduino.h"
#else
  #include "WProgram.h"
#endif 
#include <SoftwareSerial.h>
#include <Wire.h>  // Needed by cmake to generate the pressure sensor deps. (Gross!)

#include "../arduinoio/lib/uc_module.h"
#include "../arduinoio/lib/serial_module.h"
#include "../arduinoio/lib/arduinoio.h"
#include "../Adafruit_NeoPixel/Adafruit_NeoPixel.h"
#include "../MS5803-14BA_Breakout/Libraries/Arduino/src/SparkFun_MS5803_I2C.h"
#include "led_module.h"
#include "motor_module.h"
#include "pressure_sensor_module.h"
#include "uc_io_module.h"
#include "servo_module.h"
//#include "uc_servo_module.h"

const int SERIAL_RX_PIN = 0;
const int SERIAL_TX_PIN = 1;
const int LED_SIGNAL_PIN = 51;

//SoftwareSerial *serial;

arduinoio::ArduinoIO arduino_io;
void setup() {
//serial = new SoftwareSerial(SERIAL_RX_PIN, SERIAL_TX_PIN);
//serial->begin(9600);
  const uint16_t kNumLeds = 300;
  nebree8::LedModule *led_module = new nebree8::LedModule(kNumLeds, LED_SIGNAL_PIN);
  arduino_io.Add(led_module);
  //Serial.begin(9600);
  Serial.begin(115200);
  arduino_io.Add(new arduinoio::SerialRXModule(NULL, 0));
  arduino_io.Add(new nebree8::UCIOModule());
  //arduino_io.Add(new nebree8::UCServoModule());
  arduino_io.Add(new nebree8::PressureSensorModule());
  arduino_io.Add(new nebree8::MotorModule());
<<<<<<< HEAD
  // I seem to run out of ram with > 100
  // Try a teal led.
  //led_module->LightRegion(7.0, 4.0, 0, 128, 128);
  pinMode(13, OUTPUT);
  digitalWrite(13, LOW);
//pinMode(6, OUTPUT);
//digitalWrite(6, LOW);
=======
  arduino_io.Add(new nebree8::ServoModule());
>>>>>>> a54f6f261e8594bdc5b133985504194f8ba91104
}

void loop() {
  arduino_io.HandleLoopMessages();
}
