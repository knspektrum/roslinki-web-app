#include <dht.h>
#include <Wire.h>
#include <BH1750.h>

BH1750 lightMeter;
dht DHT;

const int pinPipe = 7;
const int pinLight = 4;
const int pinVent = 5;
const int pinExtraVent = 6;
const int pinCameraLEDS = 2; 
#define DHT22_PIN 3

// Zmienne do obsługi światła kamery
bool lightOn = false;
unsigned long lightStartTime = 0;
bool wasPurpleLightOn = false; // Pamięć stanu fioletowego światła

// Zmienne do bezkolizyjnej obsługi pompy (zamiast delay)
bool isPumpOn = false;
unsigned long pumpStartTime = 0;
unsigned long pumpDuration = 0;

void Bump(char command){
  if(command == 'B'){
      // Usunięte Serial.println, żeby nie śmiecić w porcie
  }
}

void Set_ExtraVent(char command){
  if(command == 'V'){
    if(digitalRead(pinExtraVent) == HIGH){
      digitalWrite(pinExtraVent, LOW);
    } else {
      digitalWrite(pinExtraVent, HIGH);
    }
  }
}

void Wake_up_camera(char command) {
  if (!lightOn && command == 'C') {
    // Zapamiętujemy stan fioletowego światła (LOW oznacza, że się świeci)
    wasPurpleLightOn = (digitalRead(pinLight) == LOW);
    
    digitalWrite(pinCameraLEDS, LOW); // Włącz białe LEDy
    digitalWrite(pinLight, HIGH);     // Wyłącz fioletowe światło na czas zdjęcia
    digitalWrite(pinVent, HIGH);      // Wyłącz wentylator
    
    lightStartTime = millis();
    lightOn = true;
  }
}

void Set_light(char command){
  if(command == 'L'){
    // L (Light) - Bezwzględnie WŁĄCZ światło i wentylator (stan LOW)
    digitalWrite(pinLight, LOW);
    digitalWrite(pinVent, LOW);
  }
  else if (command == 'D') {
    // D (Dark) - Bezwzględnie WYŁĄCZ światło i wentylator (stan HIGH)
    digitalWrite(pinLight, HIGH);
    digitalWrite(pinVent, HIGH);
  }
}

void Set_pipe(char command){
  if(command == 'P'){
    float newTime = Serial.parseFloat();
    if(newTime >= 0){
      pumpDuration = newTime * 1000;
      digitalWrite(pinPipe, LOW);
      isPumpOn = true;
      pumpStartTime = millis();
    }
  }
}

void Read_from_sensors(char command){
  if(command == 'R'){
    int chk = DHT.read22(DHT22_PIN);
    float t = DHT.temperature;
    float h = DHT.humidity;
    
    // TYMCZASOWO WYŁĄCZONY FIZYCZNY ODCZYT ŚWIATŁA (zaślepka)
    float lux = 0.0; 
    
    Serial.print(t);
    Serial.print(",");
    Serial.print(h);
    Serial.print(",");
    Serial.println(lux);
  }
}

void setup(){
  Serial.begin(9600);
  Wire.begin();
  
  pinMode(pinPipe, OUTPUT);
  pinMode(pinExtraVent, OUTPUT);
  pinMode(pinVent, OUTPUT);
  pinMode(pinLight, OUTPUT);
  pinMode(pinCameraLEDS, OUTPUT);
  
  digitalWrite(pinPipe, HIGH);
  digitalWrite(pinExtraVent, HIGH);
  digitalWrite(pinVent, HIGH);
  digitalWrite(pinLight, HIGH);
  digitalWrite(pinCameraLEDS, HIGH);
  
  lightMeter.begin(); // Nawet jeśli odczyt zablokowany, inicjalizacja zostaje (nic nie psuje)
}

void loop() {
  if (Serial.available() > 0) {
    char command = Serial.read();
    
    Bump(command);
    Read_from_sensors(command);
    Set_pipe(command);
    Set_light(command);
    Set_ExtraVent(command);
    
    if (!lightOn && command == 'C') {
      Wake_up_camera(command);
    }
    
    // Odbiór potwierdzenia zrobienia zdjęcia (komenda 'X')
    if (command == 'X') {
      digitalWrite(pinCameraLEDS, HIGH); // Zgaś białe LEDy
      
      // Jeśli fioletowe świeciło przed zdjęciem, włącz je z powrotem
      if (wasPurpleLightOn) {
        digitalWrite(pinLight, LOW);
        digitalWrite(pinVent, LOW);
      }
      lightOn = false;
    }
  }

  // Zegar 1: Wyłączenie pompy
  if (isPumpOn && (millis() - pumpStartTime >= pumpDuration)) {
    digitalWrite(pinPipe, HIGH);
    isPumpOn = false;
  }

  // Zegar 2: Awaryjne wyłączenie aparatu po minucie
  if (lightOn && (millis() - lightStartTime >= 1UL * 60UL * 1000UL)) {
    digitalWrite(pinCameraLEDS, HIGH);
    
    if (wasPurpleLightOn) {
      digitalWrite(pinLight, LOW);
      digitalWrite(pinVent, LOW);
    }
    lightOn = false;
  }
}