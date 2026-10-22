// ATtiny85 Arduino pin 0 = PB0 = physical DIP pin 5.
const byte LED_PIN = 0;

void setup() {
  pinMode(LED_PIN, OUTPUT);

  // Seven quick flashes identify the start of this firmware.
  for (byte count = 0; count < 7; count++) {
    digitalWrite(LED_PIN, HIGH);
    delay(50);
    digitalWrite(LED_PIN, LOW);
    delay(50);
  }
}

void loop() {
  digitalWrite(LED_PIN, HIGH);
  delay(500);
  digitalWrite(LED_PIN, LOW);
  delay(500);
}
