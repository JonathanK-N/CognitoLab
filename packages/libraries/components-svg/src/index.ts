export type IconEntry = {
  id: string;
  name: string;
  file: string;
  category: "passive" | "active" | "module" | "board" | "sensor" | "actuator" | "robotics";
  png: string;
};

export const icons: IconEntry[] = [
  { id: "led", name: "LED", file: "icons/led.svg", category: "active", png: "png/led.png" },
  {
    id: "resistor",
    name: "Résistance",
    file: "icons/resistor.svg",
    category: "passive",
    png: "png/resistor.png"
  },
  {
    id: "capacitor",
    name: "Condensateur",
    file: "icons/capacitor.svg",
    category: "passive",
    png: "png/capacitor.png"
  },
  {
    id: "diode",
    name: "Diode",
    file: "icons/diode.svg",
    category: "active",
    png: "png/diode.png"
  },
  {
    id: "bridge-rectifier",
    name: "Pont de diode",
    file: "icons/bridge-rectifier.svg",
    category: "active",
    png: "png/bridge-rectifier.png"
  },
  {
    id: "transistor-npn",
    name: "Transistor NPN",
    file: "icons/transistor-npn.svg",
    category: "active",
    png: "png/transistor-npn.png"
  },
  {
    id: "transistor-pnp",
    name: "Transistor PNP",
    file: "icons/transistor-pnp.svg",
    category: "active",
    png: "png/transistor-pnp.png"
  },
  {
    id: "mosfet-n",
    name: "MOSFET N",
    file: "icons/mosfet-n.svg",
    category: "active",
    png: "png/mosfet-n.png"
  },
  {
    id: "breadboard",
    name: "Breadboard",
    file: "icons/breadboard.svg",
    category: "module",
    png: "png/breadboard.png"
  },
  {
    id: "potentiometer",
    name: "Potentiomètre",
    file: "icons/potentiometer.svg",
    category: "passive",
    png: "png/potentiometer.png"
  },
  { id: "servo", name: "Servo", file: "icons/servo.svg", category: "actuator", png: "png/servo.png" },
  {
    id: "motor-dc",
    name: "Moteur DC",
    file: "icons/motor-dc.svg",
    category: "actuator",
    png: "png/motor-dc.png"
  },
  { id: "relay", name: "Relais", file: "icons/relay.svg", category: "active", png: "png/relay.png" },
  { id: "lcd", name: "LCD", file: "icons/lcd.svg", category: "module", png: "png/lcd.png" },
  { id: "oled", name: "OLED", file: "icons/oled.svg", category: "module", png: "png/oled.png" },
  {
    id: "wifi-module",
    name: "Module WiFi",
    file: "icons/wifi-module.svg",
    category: "module",
    png: "png/wifi-module.png"
  },
  { id: "esp32", name: "ESP32", file: "icons/esp32.svg", category: "board", png: "png/esp32.png" },
  {
    id: "esp8266",
    name: "ESP8266",
    file: "icons/esp8266.svg",
    category: "board",
    png: "png/esp8266.png"
  },
  {
    id: "arduino-uno",
    name: "Arduino Uno",
    file: "icons/arduino-uno.svg",
    category: "board",
    png: "png/arduino-uno.png"
  },
  {
    id: "arduino-nano",
    name: "Arduino Nano",
    file: "icons/arduino-nano.svg",
    category: "board",
    png: "png/arduino-nano.png"
  },
  {
    id: "arduino-mega",
    name: "Arduino Mega",
    file: "icons/arduino-mega.svg",
    category: "board",
    png: "png/arduino-mega.png"
  },
  {
    id: "raspberry-pi-pico",
    name: "Raspberry Pi Pico",
    file: "icons/raspberry-pi-pico.svg",
    category: "board",
    png: "png/raspberry-pi-pico.png"
  },
  {
    id: "stm32-bluepill",
    name: "STM32 Blue Pill",
    file: "icons/stm32-bluepill.svg",
    category: "board",
    png: "png/stm32-bluepill.png"
  },
  {
    id: "sensor-dht22",
    name: "DHT22",
    file: "icons/sensor-dht22.svg",
    category: "sensor",
    png: "png/sensor-dht22.png"
  },
  {
    id: "sensor-hcsr04",
    name: "HC-SR04",
    file: "icons/sensor-hcsr04.svg",
    category: "sensor",
    png: "png/sensor-hcsr04.png"
  },
  {
    id: "sensor-mpu6050",
    name: "MPU6050",
    file: "icons/sensor-mpu6050.svg",
    category: "sensor",
    png: "png/sensor-mpu6050.png"
  },
  { id: "sensor-ldr", name: "LDR", file: "icons/sensor-ldr.svg", category: "sensor", png: "png/sensor-ldr.png" },
  { id: "sensor-pir", name: "PIR", file: "icons/sensor-pir.svg", category: "sensor", png: "png/sensor-pir.png" },
  { id: "buzzer", name: "Buzzer", file: "icons/buzzer.svg", category: "actuator", png: "png/buzzer.png" },
  { id: "stepper", name: "Moteur pas à pas", file: "icons/stepper.svg", category: "actuator", png: "png/stepper.png" }
];
