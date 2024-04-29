#include <SoftwareSerial.h>
#include "SparkFun_UHF_RFID_Reader.h"

SoftwareSerial softSerial(2, 3); // RX, TX
RFID nano; // Create instance

String last_pallet_epc; // Variable to store the EPC of the last pallet scanned
int last_pallet_rssi = 0; // Variable to store the RSSI of the last pallet scanned
unsigned long last_pallet_timestamp = 0; // Variable to store the timestamp of the last pallet scanned

String last_shelf_epc; // Variable to store the EPC of the last shelf scanned
int last_shelf_rssi = 0; // Variable to store the RSSI of the last shelf scanned
unsigned long last_shelf_timestamp = 0; // Variable to store the timestamp of the last shelf scanned
int scanning_print_freq_index = 0; // Variable to force "Scanning" to print every 10th iteration
String switchState;

#define BUZZER1 9
#define BUZZER2 10
#define PALLET_LED 6
#define SHELF_LED 13
#define SWITCH_UP 4
#define SWITCH_DOWN 5



void setup() {
  Serial.begin(115200);
  while (!Serial); //Wait for the serial port to come online
  pinMode(BUZZER1, OUTPUT);
  pinMode(BUZZER2, OUTPUT);
  pinMode(PALLET_LED, OUTPUT);
  pinMode(SHELF_LED,OUTPUT);
  pinMode(SWITCH_UP,INPUT_PULLUP);
  pinMode(SWITCH_DOWN,INPUT_PULLUP);

  //digitalWrite(BUZZER2, LOW); //Pull half the buzzer to ground and drive the other half.

  if (setupNano(38400) == false) { //Configure nano to run at 38400bps
    Serial.println(F("Module failed to respond. Please check wiring."));
    while (1); //Freeze!
  }

  nano.setRegion(REGION_NORTHAMERICA); //Set to North America

  nano.setReadPower(1000); //5.00 dBm. Higher values may cause USB port to brown out
  //Max Read TX Power is 27.00 dBm and may cause temperature-limit throttling

  //Serial.println(F("Press a key to begin scanning for tags."));
  //while (!Serial.available()); //Wait for user to send a character
  //Serial.read(); //Throw away the user's character

  nano.startReading(); //Begin scanning for tags
}

void loop() {
  if (nano.check() == true) {
    byte responseType = nano.parseResponse();
    scanning_print_freq_index++;
    if (responseType == RESPONSE_IS_KEEPALIVE) {
      if(scanning_print_freq_index == 1){
      //Serial.println(F("Scanning"));
      scanning_print_freq_index = 0;
      
      }
    }
    else if (responseType == RESPONSE_IS_TAGFOUND) {
      // Update timestamp and print tag info
      //printTagInfo();
      checkSwitchState();
      if (switchState != "C"){
      updateTimestamps(); 
      PrintFormattedTagInfo();
       delay(500);
       //tone(BUZZER1, 2093, 150); //C
      delay(150);
      //tone(BUZZER1, 2349, 150); //D
      delay(150);
      //tone(BUZZER1, 2637, 150); //E
      delay(100);
      }
      else {
      delay(700);
      }
      
      //printLastTagsInfo(); 
      

      digitalWrite(PALLET_LED,LOW);
      digitalWrite(SHELF_LED,LOW);
     
      
    }
    else if (responseType == ERROR_CORRUPT_RESPONSE && switchState != "C") {
      Serial.println(F("Bad CRC"));
    }
  }
}

boolean setupNano(long baudRate) {
  nano.begin(softSerial); //Tell the library to communicate over software serial port

  softSerial.begin(baudRate); // For this test, assume module is already at our desired baud rate
  while (!softSerial.isListening()); //Wait for port to open

  //About 200ms from power on the module will send its firmware version at 115200. We need to ignore this.
  while (softSerial.available()) softSerial.read();

  nano.getVersion();

  if (nano.msg[0] == ERROR_WRONG_OPCODE_RESPONSE) {
    //This happens if the baud rate is correct but the module is doing a continuous read
    nano.stopReading();
    //Serial.println(F("Module continuously reading. Asking it to stop..."));
    delay(1500);
  } else {
    //The module did not respond so assume it's just been powered on and communicating at 115200bps
    softSerial.begin(115200); //Start software serial at 115200
    nano.setBaud(baudRate);
    softSerial.begin(baudRate); //Start the software serial port, this time at user's chosen baud rate
    delay(500);
  }

  //Test the connection
  nano.getVersion();
  if (nano.msg[0] != ALL_GOOD) return false; //Something is not right

  //The M6E has these settings no matter what
  nano.setTagProtocol(); //Set protocol to GEN2
  nano.setAntennaPort(); //Set TX/RX antenna ports to 1

  return true; //We are ready to rock
}
void checkSwitchState(){
  int SWITCH_UP_STATE = digitalRead(SWITCH_UP);
  int SWITCH_DOWN_STATE = digitalRead(SWITCH_DOWN);

  if (SWITCH_UP_STATE == HIGH && SWITCH_DOWN_STATE == HIGH) {
    switchState = "C";
  }
  if (SWITCH_UP_STATE == LOW){
    switchState = "P";
  }
  if (SWITCH_DOWN_STATE == LOW){
    switchState = "D";
  }

}
void updateTimestamps() {
  int rssi = nano.getTagRSSI();
  byte tagEPCBytes = nano.getTagEPCBytes();
  String tagEPC = ""; // Variable to store the EPC as a string

  // Construct the EPC string
  for (byte x = 0; x < tagEPCBytes; x++) {
    if (nano.msg[31 + x] < 0x10) tagEPC += "0"; // Pretty print
    tagEPC += String(nano.msg[31 + x], HEX);
  }

  unsigned long currentMillis = millis();
  
  // Check if the scanned tag is a shelf or pallet tag
  //if (tagEPCBytes > 0) {
    if (tagEPC.startsWith("aa")) {
      
      last_shelf_timestamp = currentMillis;
      //Serial.println("shelf:");
      //Serial.print(last_shelf_timestamp);
      last_shelf_epc = tagEPC;
      last_shelf_rssi = rssi;
      return true;
    } else if (tagEPC.startsWith("bb")) {
      
      last_pallet_timestamp = currentMillis;
      //Serial.println("pallet:");
      //Serial.print(last_shelf_timestamp);
      last_pallet_epc = tagEPC;
      last_pallet_rssi = rssi;
      return true;
    }
  //}
  
  return false;
}

void PrintFormattedTagInfo(){
  // Current Tag
  long timeStamp = nano.getTagTimestamp();
  byte tagEPCBytes = nano.getTagEPCBytes();

  String epcString = "";
  for (byte x = 0 ; x < 3; x++) {
    if (nano.msg[31 + x] < 0x10) epcString += "0"; // Pretty print
    epcString += String(nano.msg[31 + x], HEX);
    epcString += " ";
  }

  epcString.trim();
  Serial.print("Forklift Mode: ");
  Serial.print(switchState);
  Serial.print(" ||| ");
  Serial.print(F("Current Tag -"));
  // Check the first byte of EPC and print class accordingly
  Serial.print(F(" class: "));
  if (tagEPCBytes > 0) {
    if (nano.msg[31] == 0xAA) {
      digitalWrite(SHELF_LED,HIGH);
      Serial.print(F("shelf"));
      last_shelf_epc = epcString; // Store EPC of the last shelf scanned
      //last_shelf_rssi = rssi; // Store RSSI of the last shelf scanned
    } else if (nano.msg[31] == 0xBB) {
      digitalWrite(PALLET_LED,HIGH);
      Serial.print(F("pallet"));
      last_pallet_epc = epcString; // Store EPC of the last pallet scanned
      //last_pallet_rssi = rssi; // Store RSSI of the last pallet scanned
    } else {     Serial.print(F("unknown"));
    }
  } else {
    Serial.print(F("unknown"));
  }
  Serial.print(" UID: ");

  Serial.print(epcString);

  Serial.print(" at time: ");

  String timeStampSTR = String(timeStamp);
  while (timeStampSTR.length() < 3) {
    timeStampSTR = "0" + timeStampSTR;
  }
  Serial.print(timeStampSTR);
  // Last Pallet
  Serial.print(" ||| Last Pallet - ");
  Serial.print("UID: ");
  Serial.print(last_pallet_epc);
  Serial.print(" time since scan: ");
  printElapsedTime(last_pallet_timestamp);
  // Last Shelf
  Serial.print(" ||| Last Shelf - ");
  Serial.print("UID: ");
  Serial.print(last_shelf_epc);
  Serial.print(" time since scan: ");
  printElapsedTime(last_shelf_timestamp);
  Serial.println();
}
void printLastTagsInfo() {
  //Serial.println();
  Serial.println(F("Last Pallet:"));
  Serial.print(F("EPC: "));
  Serial.print(last_pallet_epc);
  Serial.print(F(", RSSI: "));
  Serial.print(last_pallet_rssi);
  Serial.print(F(", Last Scanned Time: "));
  printElapsedTime(last_pallet_timestamp);

  Serial.println(F("Last Shelf:"));
  Serial.print(F("EPC: "));
  Serial.print(last_shelf_epc);
  Serial.print(F(", RSSI: "));
  Serial.print(last_shelf_rssi);
  Serial.print(F(", Last Scanned Time: "));
  printElapsedTime(last_shelf_timestamp);
}

void printTagInfo() {
  //Serial.println();
  Serial.println("Tag Scanned:");
  int rssi = nano.getTagRSSI();
  long freq = nano.getTagFreq();
  long timeStamp = nano.getTagTimestamp();
  byte tagEPCBytes = nano.getTagEPCBytes();

  Serial.print(F(" rssi["));
  Serial.print(rssi);
  Serial.print(F("]"));

  Serial.print(F(" freq["));
  Serial.print(freq);
  Serial.print(F("]"));

  Serial.print(F(" time["));
  Serial.print(timeStamp);
  Serial.print(F("]"));

  // Print EPC bytes, this is a subsection of bytes from the response/msg array
  Serial.print(F(" epc["));
  String epcString = "";
  for (byte x = 0 ; x < tagEPCBytes ; x++) {
    if (nano.msg[31 + x] < 0x10) epcString += "0"; // Pretty print
    epcString += String(nano.msg[31 + x], HEX);
    epcString += " ";
  }
  epcString.trim();
  Serial.print(epcString);
  Serial.print(F("]"));

  // Check the first byte of EPC and print class accordingly
  Serial.print(F(" class: "));
  if (tagEPCBytes > 0) {
    if (nano.msg[31] == 0xAA) {
      Serial.print(F("shelf"));
      last_shelf_epc = epcString; // Store EPC of the last shelf scanned
      last_shelf_rssi = rssi; // Store RSSI of the last shelf scanned
    } else if (nano.msg[31] == 0xBB) {
      Serial.print(F("pallet"));
      last_pallet_epc = epcString; // Store EPC of the last pallet scanned
      last_pallet_rssi = rssi; // Store RSSI of the last pallet scanned
    } else {     Serial.print(F("unknown"));
    }
  } else {
    Serial.print(F("unknown"));
  }

  Serial.println();
  Serial.println();
}

void printElapsedTime(unsigned long startTime) {
  unsigned long elapsedTime = millis() - startTime;
  unsigned long seconds = elapsedTime / 1000;
  unsigned long minutes = seconds / 60;
  seconds %= 60;

  Serial.print(minutes);
  Serial.print(F(" minutes "));
  Serial.print(seconds);
  Serial.print(F(" seconds"));
}
