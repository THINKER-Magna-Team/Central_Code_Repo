/*********
  Rui Santos
  Complete project details at https://RandomNerdTutorials.com/esp32-hc-sr04-ultrasonic-arduino/
  
  Permission is hereby granted, free of charge, to any person obtaining a copy
  of this software and associated documentation files.
  
  The above copyright notice and this permission notice shall be included in all
  copies or substantial portions of the Software.
*********/

const int trigPin_one = 23;
const int echoPin_one = 22;

const int trigPin_two = 17;
const int echoPin_two = 16;


const int beamBreakPin =26;
//define sound speed in cm/uS
#define SOUND_SPEED 0.034
#define CM_TO_INCH 0.393701

long duration;
float distanceCm;
float distanceInch;
int sensorState=0;

void setup() {
  Serial.begin(115200); // Starts the serial communication
  pinMode(trigPin_one, OUTPUT); // Sets the trigPin as an Output
  pinMode(echoPin_one, INPUT); // Sets the echoPin as an Input
  pinMode(trigPin_two, OUTPUT); // Sets the trigPin as an Output
  pinMode(echoPin_two, INPUT); // Sets the echoPin as an Input
  // initialize the LED pin as an output:
  //pinMode(LEDPIN, OUTPUT);//Attached to 3.3 V 
  // initialize the sensor pin as an input:
  pinMode(beamBreakPin, INPUT_PULLUP);     
  
}

void loop() {
  int shelf_3 = BeamBreak();
//  Serial.println("Shelf Location #1:");
  int shelf_1 = UltraSonicCounter(trigPin_one,echoPin_one,4.3459867,-0.305785545);
//  Serial.println("Shelf Location #2:");
  int shelf_2 = UltraSonicCounter(trigPin_two,echoPin_two,4.482746966,-0.298424437);
  Serial.println(String(shelf_1)+","+String(shelf_2)+","+String(shelf_3));
    //Serial.println(
  delay(1000);
}
int BeamBreak(){
  sensorState = digitalRead(beamBreakPin);
  int beamBroke = 0;
  if (sensorState == LOW) {
    beamBroke = 1;
  }
  return beamBroke;
}

int UltraSonicCounter(int trigPin, int echoPin, float intercept, float slope){
  // Clears the trigPin
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  // Sets the trigPin on HIGH state for 10 micro seconds
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);
  
  // Reads the echoPin, returns the sound wave travel time in microseconds
  duration = pulseIn(echoPin, HIGH);
  
  // Calculate the distance
  distanceCm = duration * SOUND_SPEED/2;
  
  // Convert to inches
  distanceInch = distanceCm * CM_TO_INCH;

  int boxCount = BoxCount(intercept,slope);
  return boxCount;
}
int BoxCount(float intercept, float slope)
{
  int boxCount;
  boxCount = round(intercept+slope*distanceInch);
  if (boxCount < 0)
  {
    boxCount=0;
  }
  return boxCount;
}
