import { Router } from "express";

const router = Router();

const iconSet = [
  "led",
  "resistor",
  "capacitor",
  "diode",
  "bridge-rectifier",
  "transistor-npn",
  "transistor-pnp",
  "mosfet-n",
  "breadboard",
  "potentiometer",
  "servo",
  "motor-dc",
  "relay",
  "lcd",
  "oled",
  "wifi-module",
  "esp32",
  "esp8266",
  "arduino-uno",
  "arduino-nano",
  "arduino-mega",
  "raspberry-pi-pico",
  "stm32-bluepill",
  "sensor-dht22",
  "sensor-hcsr04",
  "sensor-mpu6050",
  "sensor-ldr",
  "sensor-pir",
  "buzzer",
  "stepper"
].map((id) => ({ id, name: id, file: `${id}.svg` }));

router.get("/", (_req, res) => {
  res.json(iconSet);
});

export default router;
