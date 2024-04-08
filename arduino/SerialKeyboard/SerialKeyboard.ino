/* 
 * This file is part of the SerialKeyboard distribution
 * Copyright (c) 2019 Foone Turing.
 * 
 * This program is free software: you can redistribute it and/or modify  
 * it under the terms of the GNU General Public License as published by  
 * the Free Software Foundation, version 3.
 *
 * This program is distributed in the hope that it will be useful, but 
 * WITHOUT ANY WARRANTY; without even the implied warranty of 
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU 
 * General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License 
 * along with this program. If not, see <http://www.gnu.org/licenses/>.
 */

#include <Keyboard.h>
#include <PacketSerial.h>
#include <util/crc16.h>

const uint16_t MODFIERKEY_GENERIC = (MODIFIERKEY_CTRL&MODIFIERKEY_SHIFT);

PacketSerial packetized;

void setup() {
  packetized.setPacketHandler(&onPacketReceived);
  packetized.begin(9600);
  // Wait before accepting commands to avoid getting a spurious message on connection
  delay(1000);
}

uint16_t calculate_checksum(const uint8_t* buffer, size_t size){
  uint16_t sum=0xFFFF;
  for(size_t i=0;i<size;i++){
    sum = _crc16_update(sum, buffer[i]);
  }
  return sum;
}

void reset_all_keys(){
  Keyboard.set_key6(0);
  Keyboard.set_key5(0);
  Keyboard.set_key4(0);
  Keyboard.set_key3(0);
  Keyboard.set_key2(0);
  Keyboard.set_key1(0);
  Keyboard.set_modifier(0);
}

void onPacketReceived(const uint8_t* buffer, size_t size){
  
  if(size<6){
    Serial.write(0x01);
    Serial.printf("Got under-length message: %02d bytes\n", size);
    Serial.flush();
    return;
  }
  const uint16_t checksum     =(buffer[0] << 8 )| buffer[1];
  const uint8_t modifiers     =buffer[2];
  const uint8_t timing_down   =buffer[3];
  const uint8_t timing_up     =buffer[4];
  uint16_t calculated_sum = calculate_checksum(&buffer[2], size-2);
#ifdef DEBUG
  Serial.printf("Calculated checksum %02X, sent checksum %04x\n", calculated_sum, checksum);
  Serial.printf("modifiers %02x timing_down %02x timing_up %02x\n", modifiers, timing_down, timing_up);
  
#endif

  if(calculated_sum != checksum){
    Serial.write(0x02);
    Serial.printf("Calculated checksum %02X, sent checksum %04x\n", calculated_sum, checksum);
    Serial.flush();
    return;
  }
  if(timing_down!=0xFF){
    reset_all_keys();
    Keyboard.set_modifier(MODFIERKEY_GENERIC | modifiers);
  
    for(size_t i=5;i<size;i++){
      keyboard_keys[i-5] = buffer[i];
    }
  
    Keyboard.send_now();
    delay(timing_down * 10);
  }
  if(timing_up!=0xFF){
    reset_all_keys();
    delay(timing_up * 10);
    Keyboard.send_now();
  }
  Serial.write(0x00);
}

void loop() {
  packetized.update();
}
