import React, { useState } from "react";
import { icons } from "@cognitolab/components-svg";

const categories = ["Tous", "Capteurs", "Actionneurs", "Microcontrôleurs", "Affichage", "Communication", "Passifs"];

const extraComponents = [
  { id: "arduino-uno-ext",   name: "Arduino Uno",         category: "Microcontrôleurs", icon: "🔵", voltage: "5V",   desc: "ATmega328P, 14 broches numériques, 6 analogiques, USB" },
  { id: "esp32-ext",         name: "ESP32",               category: "Microcontrôleurs", icon: "📡", voltage: "3.3V", desc: "Xtensa LX6 dual-core, WiFi 802.11b/g/n, Bluetooth 4.2" },
  { id: "rpi-pico-ext",      name: "Raspberry Pi Pico",   category: "Microcontrôleurs", icon: "🟡", voltage: "3.3V", desc: "RP2040, Cortex-M0+ 133MHz, 26 GPIO multifonction" },
  { id: "stm32-ext",         name: "STM32 Blue Pill",     category: "Microcontrôleurs", icon: "💜", voltage: "3.3V", desc: "Cortex-M3 72MHz, 20KB RAM, 64KB Flash" },
  { id: "dht22-ext",         name: "DHT22",               category: "Capteurs",         icon: "🌡", voltage: "3-5V", desc: "Capteur température & humidité. Précision ±0.5°C / ±2%HR" },
  { id: "hcsr04-ext",        name: "HC-SR04",             category: "Capteurs",         icon: "📏", voltage: "5V",   desc: "Capteur ultrason distance, portée 2cm-400cm, précision 3mm" },
  { id: "pir-ext",           name: "PIR (HC-SR501)",      category: "Capteurs",         icon: "👁",  voltage: "5V",   desc: "Capteur de mouvement infrarouge passif, détection jusqu'à 7m" },
  { id: "mpu6050-ext",       name: "MPU-6050",            category: "Capteurs",         icon: "📐", voltage: "3.3V", desc: "Accéléromètre + gyroscope 6 axes, interface I2C" },
  { id: "bmp280-ext",        name: "BMP280",              category: "Capteurs",         icon: "🌬", voltage: "3.3V", desc: "Baromètre + température. Précision ±1 hPa / ±1°C" },
  { id: "servo-ext",         name: "Servo SG90",          category: "Actionneurs",      icon: "⚙",  voltage: "5V",   desc: "Micro-servomoteur 9g, 180°, couple 1.8kg·cm, PWM 50Hz" },
  { id: "stepper-ext",       name: "Moteur Pas à Pas",    category: "Actionneurs",      icon: "🔄", voltage: "5-12V",desc: "NEMA17, 200 pas/tour, couple 40N·cm. Compatible A4988/DRV8825" },
  { id: "oled-ext",          name: "OLED 0.96\" SSD1306", category: "Affichage",        icon: "🖥",  voltage: "3.3V", desc: "128×64 pixels, monochrome, I2C ou SPI, angle vision 160°" },
  { id: "lcd-ext",           name: "LCD 16×2 + I2C",     category: "Affichage",        icon: "📟", voltage: "5V",   desc: "16 colonnes, 2 lignes, rétroéclairage bleu, module I2C PCF8574" },
  { id: "nrf24-ext",         name: "nRF24L01+",           category: "Communication",    icon: "📶", voltage: "3.3V", desc: "Module radio 2.4GHz, vitesse jusqu'à 2Mbps, portée 100m+" },
  { id: "relay-ext",         name: "Module Relais 5V",    category: "Actionneurs",      icon: "⚡", voltage: "5V",   desc: "Commutation 10A/250VAC, isolation optique, actif bas" },
  { id: "resistor-ext",      name: "Résistance",          category: "Passifs",          icon: "🔌", voltage: "—",    desc: "Composant passif limitant le courant. Code couleur selon valeur" },
  { id: "capacitor-ext",     name: "Condensateur",        category: "Passifs",          icon: "🔋", voltage: "—",    desc: "Stockage d'énergie, filtrage, couplage. Électrolytique ou céramique" },
  { id: "ldr-ext",           name: "LDR (Photorésistance)",category: "Capteurs",        icon: "☀",  voltage: "—",    desc: "Résistance variable selon la lumière. 10kΩ obscurité → 1kΩ lumière" },
];

const arduinoCode: Record<string, string> = {
  "dht22-ext": `#include <DHT.h>\n#define DHTPIN 2\n#define DHTTYPE DHT22\nDHT dht(DHTPIN, DHTTYPE);\nvoid setup() {\n  Serial.begin(9600);\n  dht.begin();\n}\nvoid loop() {\n  float h = dht.readHumidity();\n  float t = dht.readTemperature();\n  Serial.print("Temp: "); Serial.print(t);\n  Serial.print("°C  Hum: "); Serial.println(h);\n  delay(2000);\n}`,
  "hcsr04-ext": `const int trigPin = 9, echoPin = 10;\nvoid setup() {\n  Serial.begin(9600);\n  pinMode(trigPin, OUTPUT);\n  pinMode(echoPin, INPUT);\n}\nvoid loop() {\n  digitalWrite(trigPin, LOW);\n  delayMicroseconds(2);\n  digitalWrite(trigPin, HIGH);\n  delayMicroseconds(10);\n  digitalWrite(trigPin, LOW);\n  long dur = pulseIn(echoPin, HIGH);\n  float dist = dur * 0.034 / 2;\n  Serial.print("Distance: "); Serial.print(dist); Serial.println(" cm");\n  delay(500);\n}`,
  "servo-ext": `#include <Servo.h>\nServo myServo;\nvoid setup() {\n  myServo.attach(9);\n}\nvoid loop() {\n  for(int pos=0; pos<=180; pos+=1) {\n    myServo.write(pos);\n    delay(15);\n  }\n  for(int pos=180; pos>=0; pos-=1) {\n    myServo.write(pos);\n    delay(15);\n  }\n}`,
};

const defaultCode = `// Code Arduino / MicroPython\n// Consultez la fiche technique\n// pour les connexions et exemples`;

const ComponentsPage: React.FC = () => {
  const [cat, setCat]       = useState("Tous");
  const [selected, setSelected] = useState<(typeof extraComponents)[0] | null>(null);

  const allComponents = extraComponents;
  const filtered = cat === "Tous"
    ? allComponents
    : allComponents.filter(c => c.category === cat);

  return (
    <div className="space-y-5 pb-8">
      {/* Header */}
      <div>
        <h1 className="section-title">Bibliothèque Composants</h1>
        <p className="section-sub">Explorez chaque composant, capteur et actionneur avec fiches interactives</p>
      </div>

      {/* Categories */}
      <div className="flex flex-wrap gap-2">
        {categories.map(c => (
          <button key={c} onClick={() => setCat(c)} className={`board-chip ${cat === c ? "active" : ""}`}>
            {c}
          </button>
        ))}
      </div>

      <div className="grid md:grid-cols-3 gap-5">
        {/* Component grid */}
        <div className="md:col-span-2">
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            {filtered.map(comp => (
              <button
                key={comp.id}
                onClick={() => setSelected(comp)}
                className={`comp-card text-left transition-all ${selected?.id === comp.id ? "border-cl-cyan/50 bg-cl-cyan/5 shadow-glow-cyan" : ""}`}
              >
                <div className="text-3xl mb-2">{comp.icon}</div>
                <p className="text-xs font-bold text-white leading-snug">{comp.name}</p>
                <p className="text-xs text-slate-500 mt-0.5">{comp.category}</p>
                <div className="mt-2">
                  <span className="badge badge-blue text-xs">{comp.voltage}</span>
                </div>
              </button>
            ))}
          </div>
          {filtered.length === 0 && (
            <div className="text-center py-12 text-slate-500 text-sm">
              Aucun composant dans cette catégorie
            </div>
          )}
        </div>

        {/* Detail panel */}
        <div className="glass rounded-2xl overflow-hidden h-fit sticky top-0">
          {selected ? (
            <div>
              {/* Header */}
              <div className="p-5" style={{ background: "linear-gradient(135deg, rgba(21,101,192,0.2), rgba(0,188,212,0.1))" }}>
                <div className="text-4xl mb-3">{selected.icon}</div>
                <h3 className="text-base font-bold text-white">{selected.name}</h3>
                <p className="text-xs text-cl-blue-4 mt-0.5">{selected.category}</p>
              </div>

              <div className="p-5 space-y-4">
                {/* Description */}
                <div>
                  <p className="text-xs text-slate-400 leading-relaxed">{selected.desc}</p>
                </div>

                {/* Specs */}
                <div>
                  <p className="text-xs font-semibold text-slate-300 mb-2 uppercase tracking-wide">Spécifications</p>
                  <div className="space-y-1.5">
                    <div className="flex justify-between text-xs">
                      <span className="text-slate-500">Tension</span>
                      <span className="text-cl-blue-4">{selected.voltage}</span>
                    </div>
                    <div className="flex justify-between text-xs">
                      <span className="text-slate-500">Catégorie</span>
                      <span className="text-slate-300">{selected.category}</span>
                    </div>
                  </div>
                </div>

                {/* Code snippet */}
                <div>
                  <p className="text-xs font-semibold text-slate-300 mb-2 uppercase tracking-wide">Code exemple</p>
                  <pre className="code-area text-xs overflow-auto max-h-40"
                    style={{ fontSize: "0.7rem" }}>
                    {arduinoCode[selected.id] ?? defaultCode}
                  </pre>
                </div>

                <div className="flex gap-2">
                  <button className="btn-primary flex-1 py-2 text-xs rounded-lg">⚡ Simuler</button>
                  <button className="btn-ghost py-2 px-3 text-xs rounded-lg">🔌 Câblage</button>
                </div>
              </div>
            </div>
          ) : (
            <div className="p-8 text-center text-slate-500">
              <div className="text-4xl mb-3">🧩</div>
              <p className="text-sm">Sélectionnez un composant<br />pour voir sa fiche technique</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ComponentsPage;
