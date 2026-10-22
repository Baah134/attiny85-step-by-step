#include <SoftwareSerial.h>

// ATtiny85 Arduino pin 0 = PB0 = physical DIP pin 5 (LED).
// Arduino pin 3 = PB3 = physical DIP pin 2 (TX to Uno D4).
// Arduino pin 4 = PB4 = physical DIP pin 3 (unused RX).
const byte LED_PIN = 0;
SoftwareSerial telemetry(4, 3);
unsigned long packet = 0;

void setup() {
  pinMode(LED_PIN, OUTPUT);
  telemetry.begin(9600);
  for (byte i = 0; i < 5; i++) {
    digitalWrite(LED_PIN, HIGH);
    delay(50);
    digitalWrite(LED_PIN, LOW);
    delay(50);
  }
  telemetry.println(F("ATtiny85 telemetry: 8 MHz, TX 9600 baud"));
}

void loop() {
  digitalWrite(LED_PIN, HIGH);
  telemetry.print(F("[ATtiny85] Packet #"));
  telemetry.print(packet++);
  telemetry.print(F(" | uptime="));
  telemetry.print(millis() / 1000UL);
  telemetry.println(F("s | LED=ON"));
  delay(500);
  digitalWrite(LED_PIN, LOW);
  delay(500);
}
