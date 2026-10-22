#!/usr/bin/env python3
"""Optional host C++ test of the generated relay's real setup()/loop()."""
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
ARDUINO = r'''#pragma once
#include <cstdint>
#include <deque>
#include <vector>
#include <cstddef>
using byte = uint8_t;
#define INPUT 0
#define OUTPUT 1
#define INPUT_PULLUP 2
#define LOW 0
#define HIGH 1
#define MOSI 11
#define MISO 12
#define SCK 13
#define MSBFIRST 1
extern int pins[32];
extern int modes[32];
inline void pinMode(int pin,int mode){ modes[pin]=mode; }
inline void digitalWrite(int pin,int value){ pins[pin]=value; }
inline int digitalRead(int pin){ return pins[pin]; }
inline void analogWrite(int,int){}
inline void delay(unsigned long){}
inline void delayMicroseconds(unsigned long){}
inline unsigned long millis(){ static unsigned long t=0;return t+=50; }
struct HardwareSerial {
  std::deque<uint8_t> rx;
  std::vector<uint8_t> tx;
  unsigned long baud=0;
  void begin(unsigned long b){ baud=b; }
  int available(){ return rx.size(); }
  int read(){ if(rx.empty())return -1;auto b=rx.front();rx.pop_front();return b; }
  size_t write(uint8_t b){tx.push_back(b);return 1;}
  template<class T> size_t print(T){return 1;}
};
extern HardwareSerial Serial;
'''
SOFTWARE = r'''#pragma once
#include "Arduino.h"
struct SoftwareSerial {
  std::deque<uint8_t> rx;
  bool listening=false;
  unsigned long baud=0;
  SoftwareSerial(int,int){}
  void begin(unsigned long b){baud=b;listen();}
  bool listen(){if(!listening){rx.clear();listening=true;return true;}return false;}
  bool stopListening(){bool was=listening;listening=false;return was;}
  int available(){return listening?rx.size():0;}
  int read(){if(!available())return -1;auto b=rx.front();rx.pop_front();return b;}
};
'''
TEST = r'''#include <cassert>
#include "Arduino.h"
int pins[32]={0};
int modes[32]={0};
HardwareSerial Serial;
// These declarations stand in for Arduino CLI's generated prototypes.
void avrisp();
uint8_t write_flash_pages(int);
uint8_t write_eeprom_chunk(unsigned int,unsigned int);
#include "relay.ino"
int main(){
  pins[2]=HIGH;
  setup();
  assert(modes[2]==INPUT_PULLUP);
  assert(Serial.baud==19200 && tinySerial.baud==9600);
  assert(!tinySerial.listening);
  loop();
  assert(!tinySerial.listening);
  pins[2]=LOW;
  loop();
  assert(tinySerial.listening);
  tinySerial.rx.push_back('A');tinySerial.rx.push_back('B');
  Serial.rx.push_back('x');Serial.rx.push_back('\r');
  loop();
  assert(Serial.tx.size()==2 && Serial.tx[0]=='A' && Serial.tx[1]=='B');
  assert(Serial.rx.empty());
  pmode=1;
  loop();
  assert(!tinySerial.listening && pmode==1);
  pmode=0;pins[2]=HIGH;
  loop();
  assert(!tinySerial.listening);
}
'''

def main():
    compiler=shutil.which('c++')
    if not compiler:
        raise SystemExit('Host C++ compiler is required only for this optional developer test.')
    with tempfile.TemporaryDirectory(prefix='phase2 firmware ') as t:
        d=Path(t)
        (d/'Arduino.h').write_text(ARDUINO)
        (d/'SoftwareSerial.h').write_text(SOFTWARE)
        (d/'firmware_test.cpp').write_text(TEST)
        shutil.copyfile(ROOT/'phase-2-serial/ArduinoISP_Relay/ArduinoISP_Relay.ino',d/'relay.ino')
        subprocess.run([compiler,'-std=c++11','-I',str(d),str(d/'firmware_test.cpp'),'-o',str(d/'test')],check=True)
        subprocess.run([str(d/'test')],check=True)
    print('PASS: actual relay setup/loop host simulation: baud setup, open-jumper mode, telemetry/keystroke handling, active-programming guard, and return to programmer mode.')

if __name__=='__main__':main()
