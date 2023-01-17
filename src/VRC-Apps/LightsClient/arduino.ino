const int RELAY_PIN = 3;

void setup() {
  Serial.begin(9600);
  pinMode(RELAY_PIN, OUTPUT);
}

char input;

void loop() {
    if (!Serial.available()) return;
    input = Serial.read();
    if ((input == '1') || (input == 1)) digitalWrite(RELAY_PIN, HIGH);
    else if ((input == '0') || (input == 0)) digitalWrite(RELAY_PIN, LOW);
}