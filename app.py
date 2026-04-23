import os
import uuid
import time
import queue
import socket
import tempfile
import threading
import subprocess
import requests
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, Response, stream_with_context
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# ── Database ───────────────────────────────────────────────────────────────────
db_url = os.environ.get("DATABASE_URL", "sqlite:///cognitolab.db")
# Railway renvoie postgres:// — SQLAlchemy nécessite postgresql://
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = db_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = os.environ.get("SECRET_KEY", "cognitolab-dev-key")

db = SQLAlchemy(app)

# ── Simulation Manager ─────────────────────────────────────────────────────────
# Configs par carte : platform Renode, nom UART, port UART socket, firmware démo
BOARD_SIM_CONFIG = {
    "stm32f103": {
        "platform": "platforms/boards/stm32f4_discovery.repl",
        "uart":     "usart2",
        "demo_fw":  "/app/firmwares/stm32f4_demo.elf",
        "label":    "STM32 Blue Pill",
    },
    "rp2040": {
        "platform": "platforms/boards/rp2040.repl",
        "uart":     "uart0",
        "demo_fw":  "/app/firmwares/rp2040_demo.elf",
        "label":    "RP2040",
    },
    "pico": {
        "platform": "platforms/boards/rp2040.repl",
        "uart":     "uart0",
        "demo_fw":  "/app/firmwares/rp2040_demo.elf",
        "label":    "Raspberry Pi Pico",
    },
    "esp32": {
        "platform": "platforms/cpus/esp32.repl",
        "uart":     "uart0",
        "demo_fw":  "/app/firmwares/esp32_demo.elf",
        "label":    "ESP32",
    },
    "raspberry-pi": {
        "platform": "platforms/boards/rp2040.repl",  # fallback, RPi OS non simulable
        "uart":     "uart0",
        "demo_fw":  "/app/firmwares/rp2040_demo.elf",
        "label":    "Raspberry Pi",
    },
}

class SimulationManager:
    MAX_SESSIONS   = 15        # Railway Pro 8GB → ~20 possible, on garde 15 pour la sécurité
    TIMEOUT_SEC    = 300       # 5 min par session
    PORT_RANGE     = (4100, 4999)

    def __init__(self):
        self.sessions  = {}    # session_id → {process, q, board, created_at, uart_port}
        self.lock      = threading.Lock()
        self._next_port = self.PORT_RANGE[0]

    # ── Port pool ──────────────────────────────────────────────────────────────
    def _alloc_port(self):
        with self.lock:
            port = self._next_port
            self._next_port += 1
            if self._next_port > self.PORT_RANGE[1]:
                self._next_port = self.PORT_RANGE[0]
        return port

    # ── Génère le script Renode (.resc) ───────────────────────────────────────
    def _make_resc(self, board, firmware_path, uart_port, session_id):
        cfg = BOARD_SIM_CONFIG.get(board)
        if not cfg:
            # Fallback générique STM32F4
            cfg = BOARD_SIM_CONFIG["stm32f103"]

        fw = firmware_path or cfg["demo_fw"]
        return f"""\
using sysbus

mach create "sim_{session_id}"
machine LoadPlatformDescription @{cfg['platform']}

sysbus LoadELF @{fw}

# Expose UART via socket TCP — Python s'y connecte pour streamer la sortie
emulation CreateServerSocketTerminal {uart_port} "uart_{session_id}" false
connector Connect sysbus.{cfg['uart']} uart_{session_id}

start
"""

    # ── Lance une simulation ──────────────────────────────────────────────────
    def start(self, board, firmware_path=None):
        with self.lock:
            if len(self.sessions) >= self.MAX_SESSIONS:
                return None, f"Limite de {self.MAX_SESSIONS} simulations simultanées atteinte — réessayez dans quelques instants."

        session_id = uuid.uuid4().hex[:8]
        uart_port  = self._alloc_port()
        q          = queue.Queue(maxsize=1000)

        # Écrire le script .resc dans /tmp
        script_path = f"/tmp/renode_{session_id}.resc"
        with open(script_path, "w") as f:
            f.write(self._make_resc(board, firmware_path, uart_port, session_id))

        with self.lock:
            self.sessions[session_id] = {
                "process":    None,
                "q":          q,
                "board":      board,
                "created_at": time.time(),
                "uart_port":  uart_port,
                "alive":      True,
            }

        t = threading.Thread(target=self._worker, args=(session_id, script_path, uart_port, q), daemon=True)
        t.start()

        # Timeout automatique
        threading.Thread(target=self._auto_timeout, args=(session_id,), daemon=True).start()

        return session_id, None

    # ── Worker thread : lance Renode + lit UART ───────────────────────────────
    def _worker(self, session_id, script_path, uart_port, q):
        proc = None
        sock = None
        try:
            q.put("[CognitoLab] Démarrage de Renode...")

            proc = subprocess.Popen(
                ["renode", "--disable-xwt", "--console", script_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            with self.lock:
                if session_id in self.sessions:
                    self.sessions[session_id]["process"] = proc

            # Attendre que Renode ouvre le socket UART (max 10s)
            q.put("[CognitoLab] Initialisation du circuit...")
            connected = False
            for _ in range(20):
                time.sleep(0.5)
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.connect(("127.0.0.1", uart_port))
                    connected = True
                    break
                except OSError:
                    sock.close()
                    sock = None

            if not connected:
                q.put("[CognitoLab] ⚠ Impossible de connecter au UART — vérifiez le firmware")
                q.put(None)
                return

            q.put("[CognitoLab] ✓ Simulation active — sortie UART :")
            q.put("─" * 48)

            sock.settimeout(1.0)
            buf = b""
            while True:
                with self.lock:
                    if session_id not in self.sessions:
                        break
                try:
                    chunk = sock.recv(256)
                    if not chunk:
                        break
                    buf += chunk
                    # Découper par lignes
                    while b"\n" in buf:
                        line, buf = buf.split(b"\n", 1)
                        text = line.decode("utf-8", errors="replace").rstrip()
                        if text:
                            q.put(text)
                except socket.timeout:
                    continue
                except Exception:
                    break

        except FileNotFoundError:
            q.put("[ERREUR] Renode n'est pas installé dans ce conteneur.")
        except Exception as e:
            q.put(f"[ERREUR] {e}")
        finally:
            q.put(None)
            if sock:
                try: sock.close()
                except: pass
            if proc:
                try: proc.terminate()
                except: pass
            with self.lock:
                self.sessions.pop(session_id, None)
            try: os.remove(script_path)
            except: pass

    # ── SSE generator ─────────────────────────────────────────────────────────
    def stream(self, session_id):
        with self.lock:
            if session_id not in self.sessions:
                yield "data: [Session introuvable ou expirée]\n\n"
                return

        q = self.sessions[session_id]["q"]
        last_ping = time.time()

        while True:
            try:
                line = q.get(timeout=15)
                if line is None:
                    yield "data: [Simulation terminée]\n\n"
                    yield "event: done\ndata: done\n\n"
                    break
                # Échapper pour SSE (pas de newlines dans data:)
                safe = line.replace("\r", "").replace("\n", " ")
                yield f"data: {safe}\n\n"
            except queue.Empty:
                # Keepalive ping toutes les 15s pour éviter timeout Railway
                yield ": ping\n\n"

    # ── Arrêter une session ────────────────────────────────────────────────────
    def stop(self, session_id):
        with self.lock:
            session = self.sessions.pop(session_id, None)
        if session:
            proc = session.get("process")
            if proc:
                try: proc.terminate()
                except: pass

    # ── Timeout auto ──────────────────────────────────────────────────────────
    def _auto_timeout(self, session_id):
        time.sleep(self.TIMEOUT_SEC)
        if session_id in self.sessions:
            with self.lock:
                q = self.sessions.get(session_id, {}).get("q")
            if q:
                q.put("[CognitoLab] ⏱ Timeout 5 min — simulation arrêtée automatiquement.")
                q.put(None)
            self.stop(session_id)

    # ── Statut global ──────────────────────────────────────────────────────────
    def status(self):
        with self.lock:
            return {
                "active": len(self.sessions),
                "max":    self.MAX_SESSIONS,
                "slots_free": self.MAX_SESSIONS - len(self.sessions),
                "sessions": [
                    {"id": sid, "board": s["board"], "age_s": int(time.time() - s["created_at"])}
                    for sid, s in self.sessions.items()
                ],
            }

sim_manager = SimulationManager()

# ── Models ─────────────────────────────────────────────────────────────────────
class Project(db.Model):
    __tablename__ = "projects"
    id         = db.Column(db.Integer, primary_key=True)
    title      = db.Column(db.String(200), nullable=False)
    board      = db.Column(db.String(80), default="arduino-uno")
    code       = db.Column(db.Text, default="")
    status     = db.Column(db.String(20), default="draft")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id, "title": self.title, "board": self.board,
            "code": self.code, "status": self.status,
            "created_at": self.created_at.strftime("%Y-%m-%d")
        }

class CommunityPost(db.Model):
    __tablename__ = "community_posts"
    id          = db.Column(db.Integer, primary_key=True)
    author      = db.Column(db.String(100), default="Anonyme")
    avatar      = db.Column(db.String(5), default="AN")
    title       = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default="")
    board       = db.Column(db.String(80), default="Arduino")
    tags        = db.Column(db.String(300), default="")
    likes       = db.Column(db.Integer, default=0)
    comments    = db.Column(db.Integer, default=0)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id, "author": self.author, "avatar": self.avatar,
            "title": self.title, "description": self.description,
            "board": self.board, "tags": self.tags.split(",") if self.tags else [],
            "likes": self.likes, "comments": self.comments,
            "created_at": self.created_at.strftime("%Y-%m-%d")
        }

class CourseProgress(db.Model):
    __tablename__ = "course_progress"
    id        = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.String(80), unique=True, nullable=False)
    progress  = db.Column(db.Integer, default=0)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# ── Init DB + seed data ────────────────────────────────────────────────────────
def seed_data():
    if CommunityPost.query.count() == 0:
        posts = [
            CommunityPost(author="Alexandre D.", avatar="AD",
                title="Robot suiveur de ligne — ESP32 + caméra OV2640",
                description="Mon robot autonome avec détection de ligne par vision artificielle. Utilise TensorFlow Lite directement sur l'ESP32.",
                board="ESP32", tags="IA,Vision,Autonome", likes=84, comments=12),
            CommunityPost(author="Sofia M.", avatar="SM",
                title="Station météo connectée Raspberry Pi + Dashboard",
                description="Station météo complète avec DHT22, BMP280, anémomètre et dashboard Grafana temps réel.",
                board="Raspberry Pi", tags="IoT,Météo,Dashboard", likes=61, comments=8),
            CommunityPost(author="Karim B.", avatar="KB",
                title="Bras robotique 6 DOF contrôlé par gestes",
                description="Bras articulé imprimé en 3D, STM32 + servos + MPU6050 sur gant. Cinématique inverse temps réel.",
                board="STM32", tags="Robotique,Gestes,3D Print", likes=143, comments=27),
            CommunityPost(author="Léa T.", avatar="LT",
                title="Serrure connectée RFID + Arduino",
                description="Serrure électronique avec MFRC522, buzzer, LED et app mobile React Native.",
                board="Arduino", tags="RFID,Sécurité,Mobile", likes=39, comments=5),
            CommunityPost(author="Marc P.", avatar="MP",
                title="Oscilloscope portable RP2040 + TFT",
                description="Oscilloscope 2 canaux, 500kHz, écran ILI9341, batterie LiPo, boitier 3D.",
                board="RP2040", tags="Mesure,TFT,Portable", likes=212, comments=43),
        ]
        db.session.add_all(posts)

    if Project.query.count() == 0:
        projects = [
            Project(title="ESP32 WiFi + LED blinker", board="esp32", status="done",
                code='#include <WiFi.h>\n\nvoid setup() {\n  Serial.begin(115200);\n  pinMode(2, OUTPUT);\n}\n\nvoid loop() {\n  digitalWrite(2, HIGH);\n  delay(500);\n  digitalWrite(2, LOW);\n  delay(500);\n}'),
            Project(title="Arduino Température DHT22", board="arduino-uno", status="running",
                code='#include <DHT.h>\n#define DHTPIN 2\n#define DHTTYPE DHT22\n\nDHT dht(DHTPIN, DHTTYPE);\n\nvoid setup() {\n  Serial.begin(9600);\n  dht.begin();\n}\n\nvoid loop() {\n  float t = dht.readTemperature();\n  Serial.println(t);\n  delay(2000);\n}'),
        ]
        db.session.add_all(projects)

    if CourseProgress.query.count() == 0:
        progresses = [
            CourseProgress(course_id="arduino-basics", progress=72),
            CourseProgress(course_id="esp32-iot", progress=34),
            CourseProgress(course_id="esp32-display", progress=58),
            CourseProgress(course_id="petit-projets", progress=12),
        ]
        db.session.add_all(progresses)

    db.session.commit()

_db_ready = False

@app.before_request
def init_db():
    global _db_ready
    if not _db_ready:
        try:
            db.create_all()
            seed_data()
            _db_ready = True
        except Exception as e:
            app.logger.error(f"DB init error: {e}")

# ── Static data ────────────────────────────────────────────────────────────────
COURSES = [
    {"id":"arduino-basics","title":"Arduino pour débutants","platform":"Arduino","level":"Débutant","sections":8,"duration":"4h","icon":"🔵","color":"#1565C0","desc":"GPIO, PWM, I2C, SPI, UART et vos premiers projets.","tags":["Arduino","Débutant","C++"],"video":"https://www.youtube.com/embed/6mXM-oGggrM"},
    {"id":"esp32-iot","title":"ESP32 IoT avancé","platform":"ESP32","level":"Avancé","sections":10,"duration":"6h","icon":"📡","color":"#00BCD4","desc":"WiFi, BLE, MQTT. Construisez des objets connectés et dashboards.","tags":["ESP32","WiFi","IoT"],"video":"https://www.youtube.com/embed/i3z5V3ZrIgY"},
    {"id":"rpi-linux","title":"Raspberry Pi & Linux embarqué","platform":"Raspberry Pi","level":"Intermédiaire","sections":9,"duration":"5h","icon":"🍓","color":"#E53935","desc":"Linux embarqué, Python, GPIO sur Raspberry Pi.","tags":["Raspberry Pi","Linux","Python"],"video":""},
    {"id":"stm32-bare","title":"STM32 Bare-Metal","platform":"STM32","level":"Avancé","sections":7,"duration":"7h","icon":"💜","color":"#7C4DFF","desc":"Programmation bas niveau STM32, HAL, DMA, interruptions.","tags":["STM32","Bare-metal","C"],"video":""},
    {"id":"ros-intro","title":"Introduction à ROS 2","platform":"ROS","level":"Avancé","sections":12,"duration":"8h","icon":"🤖","color":"#42A5F5","desc":"Nodes, Topics, Services, Actions. Simulez avec Gazebo.","tags":["ROS","Python","Robotique"],"video":"https://www.youtube.com/embed/CNzsPzK0dKk"},
    {"id":"esp32-display","title":"ESP32 + Écrans & Capteurs","platform":"ESP32","level":"Intermédiaire","sections":6,"duration":"3h","icon":"📺","color":"#00ACC1","desc":"OLED, TFT, LCD. DHT22, BMP280, MPU6050.","tags":["ESP32","Capteurs","Affichage"],"video":""},
    {"id":"pico-micropython","title":"Raspberry Pi Pico & MicroPython","platform":"Raspberry Pi","level":"Débutant","sections":7,"duration":"3.5h","icon":"🟡","color":"#F57F17","desc":"MicroPython sur RP2040. Servo, LEDs, capteurs.","tags":["Pico","MicroPython","Débutant"],"video":""},
    {"id":"petit-projets","title":"50 Petits Projets Électronique","platform":"Arduino","level":"Débutant","sections":15,"duration":"10h","icon":"⚡","color":"#1976D2","desc":"LED RGB, thermomètre, serrure RFID, piano... 50 projets guidés.","tags":["Arduino","Projets","Débutant"],"video":""},
]

COURSE_CONTENT = {
  "arduino-basics": {
    "sections": [
      {"title":"Introduction à Arduino","content":"Arduino est une plateforme open-source basée sur l'ATmega328P. Un sketch Arduino contient deux fonctions : setup() s'exécute une fois au démarrage, loop() se répète en continu. L'IDE Arduino simplifie la compilation et le téléversement via USB.\n\nL'Arduino Uno dispose de 14 GPIO numériques (6 PWM), 6 entrées analogiques 10-bit, un oscillateur 16 MHz et une interface USB via ATmega16U2.","code":"void setup() {\n  Serial.begin(9600);\n  pinMode(LED_BUILTIN, OUTPUT);\n  Serial.println(\"Arduino démarré !\");\n}\n\nvoid loop() {\n  digitalWrite(LED_BUILTIN, HIGH);\n  delay(1000);\n  digitalWrite(LED_BUILTIN, LOW);\n  delay(1000);\n}"},
      {"title":"GPIO Numérique","content":"Les GPIO numériques lisent et écrivent des signaux logiques 0V (LOW) ou 5V (HIGH). pinMode() configure la direction. INPUT_PULLUP active la résistance de rappel interne, inversant la logique : bouton appuyé = LOW.\n\nL'Arduino Uno supporte les résistances pull-up internes sur toutes ses broches d'entrée.","code":"const int LED = 13;\nconst int BTN = 2;\n\nvoid setup() {\n  pinMode(LED, OUTPUT);\n  pinMode(BTN, INPUT_PULLUP);\n}\n\nvoid loop() {\n  if (digitalRead(BTN) == LOW) {\n    digitalWrite(LED, HIGH);\n  } else {\n    digitalWrite(LED, LOW);\n  }\n}"},
      {"title":"GPIO Analogique & PWM","content":"Les entrées analogiques (A0-A5) convertissent 0-5V en 0-1023 (10 bits). Les sorties PWM (~3,~5,~6,~9,~10,~11) génèrent un pseudo-analogique 0-255 avec analogWrite().\n\nLe PWM module la largeur des impulsions à ~490Hz. analogWrite(led, 128) = 50% de luminosité.","code":"const int LED = 9;\nconst int POT = A0;\n\nvoid setup() { Serial.begin(9600); }\n\nvoid loop() {\n  int val = analogRead(POT);          // 0-1023\n  int brightness = val / 4;           // 0-255\n  analogWrite(LED, brightness);\n  float voltage = val * (5.0 / 1023.0);\n  Serial.printf(\"%.2f V\\n\", voltage);\n  delay(50);\n}"},
      {"title":"Communication Série (UART)","content":"La liaison série UART permet à l'Arduino de communiquer avec un PC via USB. Serial.begin(baud) initialise, Serial.print() envoie, Serial.available() et Serial.read() reçoivent.\n\nL'Arduino Uno a un seul UART matériel (D0/D1). SoftwareSerial émule un UART sur n'importe quelle broche.","code":"void setup() {\n  Serial.begin(9600);\n}\n\nvoid loop() {\n  // Envoyer\n  Serial.println(\"CognitoLab\");\n  // Recevoir\n  if (Serial.available()) {\n    char c = Serial.read();\n    Serial.print(\"Reçu : \");\n    Serial.println(c);\n  }\n  delay(500);\n}"},
      {"title":"Protocole I2C","content":"I2C utilise 2 fils (SDA + SCL) pour jusqu'à 127 périphériques adressables. Sur Arduino Uno : A4=SDA, A5=SCL. La bibliothèque Wire.h gère le protocole.\n\nDes résistances pull-up (4.7kΩ) sont nécessaires. i2cdetect liste tous les périphériques connectés.","code":"#include <Wire.h>\n\nvoid setup() {\n  Wire.begin();\n  Serial.begin(9600);\n  Serial.println(\"Scanner I2C\");\n  for (byte addr = 1; addr < 127; addr++) {\n    Wire.beginTransmission(addr);\n    if (Wire.endTransmission() == 0) {\n      Serial.print(\"0x\");\n      Serial.println(addr, HEX);\n    }\n  }\n}"},
      {"title":"Interruptions & Timers","content":"Les interruptions permettent de réagir immédiatement à des événements sans bloquer loop(). Sur Uno, D2 et D3 supportent les interruptions externes. Utilisez millis() au lieu de delay() pour un code non-bloquant.\n\nLes variables partagées entre ISR et loop() doivent être déclarées volatile.","code":"volatile bool triggered = false;\nconst int BTN = 2, LED = 13;\n\nvoid onPress() { triggered = true; }\n\nvoid setup() {\n  pinMode(LED, OUTPUT);\n  pinMode(BTN, INPUT_PULLUP);\n  attachInterrupt(digitalPinToInterrupt(BTN),\n    onPress, FALLING);\n}\n\nvoid loop() {\n  if (triggered) {\n    triggered = false;\n    digitalWrite(LED, !digitalRead(LED));\n  }\n}"},
      {"title":"Protocole SPI","content":"SPI est un bus synchrone haute vitesse 4 fils : MOSI, MISO, SCK, CS. Sur Uno : MOSI=D11, MISO=D12, SCK=D13. Chaque esclave a son propre CS.\n\nSPI peut atteindre plusieurs MHz — idéal pour afficheurs TFT, cartes SD, capteurs haute fréquence.","code":"#include <SPI.h>\n\nconst int CS = 10;\n\nvoid setup() {\n  SPI.begin();\n  pinMode(CS, OUTPUT);\n  digitalWrite(CS, HIGH);\n}\n\nbyte transfer(byte data) {\n  digitalWrite(CS, LOW);\n  byte r = SPI.transfer(data);\n  digitalWrite(CS, HIGH);\n  return r;\n}\n\nvoid loop() {\n  byte result = transfer(0x55);\n  delay(500);\n}"},
      {"title":"Projet : Station météo","content":"Projet complet combinant DHT22 (température/humidité), LCD 16×2 I2C, et communication série. Toutes les compétences du cours en un seul projet.\n\nMatériel : Arduino Uno, DHT22, LCD 16×2 + module I2C PCF8574, résistance 10kΩ.","code":"#include <DHT.h>\n#include <LiquidCrystal_I2C.h>\n\nDHT dht(7, DHT22);\nLiquidCrystal_I2C lcd(0x27, 16, 2);\n\nvoid setup() {\n  dht.begin();\n  lcd.init(); lcd.backlight();\n}\n\nvoid loop() {\n  float t = dht.readTemperature();\n  float h = dht.readHumidity();\n  lcd.clear();\n  lcd.setCursor(0, 0);\n  lcd.print(\"T: \"); lcd.print(t); lcd.print(\" C\");\n  lcd.setCursor(0, 1);\n  lcd.print(\"H: \"); lcd.print(h); lcd.print(\" %\");\n  delay(2000);\n}"}
    ],
    "quiz": [
      {"q":"Quelle fréquence d'horloge a l'Arduino Uno ?","opts":["8 MHz","16 MHz","32 MHz","72 MHz"],"answer":1},
      {"q":"Combien de broches PWM (~) possède l'Arduino Uno ?","opts":["3","4","6","8"],"answer":2},
      {"q":"Quelle fonction lit une valeur numérique sur une broche ?","opts":["analogRead()","digitalRead()","pinMode()","Serial.read()"],"answer":1},
      {"q":"Avec INPUT_PULLUP, un bouton appuyé renvoie quelle valeur ?","opts":["HIGH (1)","LOW (0)","255","-1"],"answer":1},
      {"q":"Sur Arduino Uno, SDA (I2C) est sur quelle broche ?","opts":["A3","A4","A5","D2"],"answer":1},
      {"q":"La fonction delay(1000) attend combien de temps ?","opts":["100 ms","1 seconde","10 secondes","1 microseconde"],"answer":1},
      {"q":"Quelle résolution a l'ADC de l'Arduino Uno ?","opts":["8 bits (0-255)","10 bits (0-1023)","12 bits (0-4095)","16 bits"],"answer":1}
    ]
  },
  "esp32-iot": {
    "sections": [
      {"title":"Introduction à l'ESP32","content":"L'ESP32 est un microcontrôleur Xtensa LX6 dual-core 240MHz avec WiFi 802.11 b/g/n et Bluetooth 4.2 + BLE intégrés. Il est programmable avec Arduino IDE, MicroPython ou ESP-IDF.\n\nL'ESP32 DevKit dispose de 34 GPIO, 18 ADC 12-bit, 2 DAC 8-bit, 10 capteurs tactiles, et une consommation ultra-faible en deep sleep (<10 µA).","code":"void setup() {\n  Serial.begin(115200);\n  Serial.print(\"Cores: \");\n  Serial.println(ESP.getChipCores());\n  Serial.print(\"CPU: \");\n  Serial.print(ESP.getCpuFrequencyMhz());\n  Serial.println(\" MHz\");\n  Serial.print(\"Flash: \");\n  Serial.print(ESP.getFlashChipSize()/1024/1024);\n  Serial.println(\" MB\");\n}"},
      {"title":"Connexion WiFi","content":"L'ESP32 se connecte aux réseaux WiFi avec WiFi.h. Il peut être Station (client), Point d'Accès (AP), ou les deux simultanément. Un client HTTP envoie des données vers des APIs REST ou services cloud.\n\nLe WiFi Manager simplifie la configuration réseau via une page de captive portal.","code":"#include <WiFi.h>\n#include <HTTPClient.h>\n\nconst char* SSID = \"VotreSSID\";\nconst char* PASS = \"MotDePasse\";\n\nvoid setup() {\n  Serial.begin(115200);\n  WiFi.begin(SSID, PASS);\n  while (WiFi.status() != WL_CONNECTED) {\n    delay(500); Serial.print(\".\");\n  }\n  Serial.print(\"\\nIP: \");\n  Serial.println(WiFi.localIP());\n}"},
      {"title":"Protocole MQTT & IoT","content":"MQTT est un protocole léger publish/subscribe idéal pour l'IoT. Un broker (Mosquitto, HiveMQ) reçoit et distribue les messages. L'ESP32 publie ses données et s'abonne aux commandes.\n\nLe topic est une chaîne hiérarchique (ex: cognitolab/salon/temperature). QoS 0/1/2 contrôle la garantie de livraison.","code":"#include <PubSubClient.h>\nWiFiClient espClient;\nPubSubClient mqtt(espClient);\n\nvoid callback(char* topic, byte* payload, unsigned int len) {\n  String msg = String((char*)payload).substring(0, len);\n  Serial.println(\"Reçu: \" + msg);\n}\n\nvoid setup() {\n  mqtt.setServer(\"broker.hivemq.com\", 1883);\n  mqtt.setCallback(callback);\n  mqtt.connect(\"ESP32_Lab\");\n  mqtt.subscribe(\"cognitolab/cmd\");\n}\nvoid loop() {\n  mqtt.loop();\n  mqtt.publish(\"cognitolab/temp\", \"23.5\");\n  delay(5000);\n}"},
      {"title":"Serveur Web embarqué","content":"L'ESP32 héberge un serveur web complet accessible depuis n'importe quel navigateur sur le réseau local. Les routes REST permettent de contrôler des GPIO depuis une interface web.\n\nESPAsyncWebServer est la bibliothèque la plus performante, supportant WebSockets pour les mises à jour en temps réel.","code":"#include <WebServer.h>\nWebServer server(80);\nconst int LED = 2;\n\nvoid handleRoot() {\n  String html = \"<h1>ESP32</h1>\";\n  html += \"<a href='/on'>ON</a> | \";\n  html += \"<a href='/off'>OFF</a>\";\n  server.send(200, \"text/html\", html);\n}\nvoid setup() {\n  pinMode(LED, OUTPUT);\n  server.on(\"/\", handleRoot);\n  server.on(\"/on\",  [](){digitalWrite(LED,HIGH);server.send(200,\"text/plain\",\"ON\");});\n  server.on(\"/off\", [](){digitalWrite(LED,LOW); server.send(200,\"text/plain\",\"OFF\");});\n  server.begin();\n}\nvoid loop() { server.handleClient(); }"},
      {"title":"Deep Sleep & Économie d'énergie","content":"L'ESP32 en deep sleep consomme seulement 10 µA — essentiel pour les projets sur batterie. Le MCU se réveille après un délai ou sur interruption. Seul le RTC reste actif pendant le sommeil.\n\nLes variables RTC_DATA_ATTR survivent au deep sleep, permettant de compter les réveils ou stocker l'état.","code":"#define uS_TO_S_FACTOR 1000000ULL\n#define SLEEP_SECONDS  30\nRTC_DATA_ATTR int bootCount = 0;\n\nvoid setup() {\n  Serial.begin(115200);\n  bootCount++;\n  Serial.print(\"Réveil #\");\n  Serial.println(bootCount);\n  // Lire capteur, envoyer données...\n  float temp = 22.5;\n  Serial.print(\"Temp: \"); Serial.println(temp);\n  Serial.println(\"Deep sleep 30s...\");\n  esp_sleep_enable_timer_wakeup(SLEEP_SECONDS * uS_TO_S_FACTOR);\n  esp_deep_sleep_start();\n}\nvoid loop() {}"},
      {"title":"Bluetooth BLE","content":"L'ESP32 supporte BLE pour communiquer avec smartphones et wearables. En mode serveur GATT, il expose des Services et Characteristics. Les clients BLE peuvent lire et s'abonner aux notifications.\n\nApplications : capteurs portables, domotique, contrôleurs IoT à faible consommation.","code":"#include <BLEDevice.h>\n#include <BLEServer.h>\n#include <BLE2902.h>\n\n#define SVC_UUID \"4fafc201-1fb5-459e-8fcc-c5c9c331914b\"\n#define CHR_UUID \"beb5483e-36e1-4688-b7f5-ea07361b26a8\"\n\nBLECharacteristic* pChar;\n\nvoid setup() {\n  BLEDevice::init(\"ESP32-CognitoLab\");\n  BLEServer* srv = BLEDevice::createServer();\n  BLEService* svc = srv->createService(SVC_UUID);\n  pChar = svc->createCharacteristic(CHR_UUID,\n    BLECharacteristic::PROPERTY_READ |\n    BLECharacteristic::PROPERTY_NOTIFY);\n  pChar->addDescriptor(new BLE2902());\n  svc->start();\n  srv->getAdvertising()->start();\n}\nvoid loop() {\n  pChar->setValue(\"23.5\");\n  pChar->notify();\n  delay(2000);\n}"},
      {"title":"FreeRTOS & Multi-tâches","content":"L'ESP32 intègre FreeRTOS permettant d'exécuter plusieurs tâches en parallèle sur ses deux cœurs. Chaque tâche a sa propre pile et s'exécute indépendamment. Les sémaphores synchronisent l'accès aux ressources partagées.\n\nxTaskCreatePinnedToCore() permet d'assigner une tâche à un cœur spécifique.","code":"TaskHandle_t wifiTask, sensorTask;\n\nvoid TaskWiFi(void* p) {\n  while(1) {\n    Serial.println(\"[Core0] WiFi/MQTT...\");\n    vTaskDelay(pdMS_TO_TICKS(5000));\n  }\n}\nvoid TaskSensor(void* p) {\n  while(1) {\n    Serial.println(\"[Core1] Capteur...\");\n    vTaskDelay(pdMS_TO_TICKS(1000));\n  }\n}\nvoid setup() {\n  Serial.begin(115200);\n  xTaskCreatePinnedToCore(TaskWiFi,   \"WiFi\",   10000, NULL, 1, &wifiTask,   0);\n  xTaskCreatePinnedToCore(TaskSensor, \"Sensor\", 10000, NULL, 1, &sensorTask, 1);\n}\nvoid loop() {}"},
      {"title":"OTA (Over-The-Air) Updates","content":"OTA permet de mettre à jour le firmware de l'ESP32 via WiFi sans connexion physique. ArduinoOTA utilise mDNS pour la découverte et le protocole de téléchargement.\n\nEssentiel pour les projets déployés à distance. L'IDE Arduino peut téléverser directement via le réseau.","code":"#include <ArduinoOTA.h>\n\nvoid setup() {\n  // ... connexion WiFi ...\n  ArduinoOTA.setHostname(\"esp32-cognitolab\");\n  ArduinoOTA.setPassword(\"admin1234\");\n  ArduinoOTA.onStart([]() { Serial.println(\"OTA Start\"); });\n  ArduinoOTA.onEnd([]()   { Serial.println(\"\\nOTA End\"); });\n  ArduinoOTA.onProgress([](unsigned int p, unsigned int t) {\n    Serial.printf(\"OTA: %u%%\\r\", (p/(t/100)));\n  });\n  ArduinoOTA.begin();\n}\nvoid loop() {\n  ArduinoOTA.handle();\n}"},
      {"title":"Dashboard IoT avec ThingSpeak","content":"ThingSpeak est une plateforme cloud gratuite pour visualiser des données IoT. L'ESP32 envoie ses mesures via HTTP GET, ThingSpeak génère des graphiques en temps réel. 8 champs par canal, alertes configurables.\n\nIntervalle minimum entre envois : 15 secondes (compte gratuit).","code":"#include <HTTPClient.h>\n#define THINGSPEAK_KEY \"VOTRE_API_KEY\"\n\nvoid sendToThingSpeak(float temp, float hum) {\n  HTTPClient http;\n  String url = \"http://api.thingspeak.com/update?api_key=\";\n  url += THINGSPEAK_KEY;\n  url += \"&field1=\" + String(temp, 1);\n  url += \"&field2=\" + String(hum, 1);\n  http.begin(url);\n  int code = http.GET();\n  Serial.print(\"ThingSpeak: \");\n  Serial.println(code);\n  http.end();\n}\nvoid loop() {\n  sendToThingSpeak(23.5, 65.0);\n  delay(15000);\n}"},
      {"title":"Projet : Station IoT complète","content":"Projet complet : station de surveillance environnementale avec DHT22 + BMP280, afficheur OLED, MQTT, serveur web local, et deep sleep entre les mesures.\n\nTout ce que vous avez appris dans ce cours, intégré en un seul système cohérent.","code":"// Projet complet disponible sur :\n// github.com/cognitolab/esp32-iot-station\nvoid setup() {\n  initWiFi();\n  initMQTT();\n  initSensors(); // DHT22 + BMP280\n  initDisplay(); // OLED 128x64\n  initWebServer();\n  readAndPublish();\n  goToSleep(300); // 5 minutes\n}\nvoid loop() {}"}
    ],
    "quiz": [
      {"q":"Quelle est la fréquence CPU maximale de l'ESP32 ?","opts":["80 MHz","160 MHz","240 MHz","320 MHz"],"answer":2},
      {"q":"Combien de cœurs possède l'ESP32 ?","opts":["1","2","4","8"],"answer":1},
      {"q":"Quel protocole IoT utilise le modèle publish/subscribe ?","opts":["HTTP","MQTT","I2C","SPI"],"answer":1},
      {"q":"Quelle consommation en deep sleep pour l'ESP32 ?","opts":["100 µA","10 µA","1 mA","50 mA"],"answer":1},
      {"q":"Combien d'ADC l'ESP32 possède-t-il ?","opts":["6","12","18","24"],"answer":2},
      {"q":"Quelle résolution ont les ADC de l'ESP32 ?","opts":["8 bits","10 bits","12 bits","16 bits"],"answer":2},
      {"q":"Comment assigner une tâche FreeRTOS à un cœur ?","opts":["xTaskCreate()","xTaskCreatePinnedToCore()","xTaskRun()","createTask()"],"answer":1}
    ]
  },
  "rpi-linux": {
    "sections": [
      {"title":"Introduction au Raspberry Pi","content":"Le Raspberry Pi est un ordinateur monocarte (SBC) sous Linux complet. Contrairement à Arduino, il exécute un OS complet avec tous les services Linux. Le RPi 4 dispose d'un Cortex-A72 quad-core 1.8GHz, 2-8GB RAM, WiFi, BT, USB 3.0, et 40 broches GPIO.\n\nIl peut faire tourner serveurs web, bases de données, traitement d'image et IA embarquée.","code":"# Vérifier le matériel\ncat /proc/cpuinfo | grep Model\nvcgencmd measure_temp       # Température CPU\nfree -h                      # RAM disponible\ndf -h                        # Espace disque\n\n# Activer I2C, SPI, SSH, Caméra\nsudo raspi-config\n\n# Mise à jour\nsudo apt update && sudo apt upgrade -y\nsudo apt install python3-pip vim git -y"},
      {"title":"GPIO avec Python (gpiozero)","content":"gpiozero offre une API Python intuitive pour les 40 GPIO du Raspberry Pi. LEDs, boutons, capteurs, moteurs, PWM — tout est supporté. Les broches fonctionnent en 3.3V (pas 5V comme Arduino).\n\nLes numéros BCM (GPIO) ou BOARD (physique) identifient les broches. gpiozero utilise BCM par défaut.","code":"from gpiozero import LED, Button, PWMOutputDevice\nfrom signal import pause\nimport time\n\nled = LED(17)           # GPIO17\nbtn = Button(27)        # GPIO27\npwm = PWMOutputDevice(18)  # GPIO18 PWM\n\n# Bouton contrôle LED\nbtn.when_pressed  = led.on\nbtn.when_released = led.off\n\n# Fade in/out\nfor i in range(0, 101, 5):\n    pwm.value = i / 100.0\n    time.sleep(0.05)\n\npause()  # Garder actif"},
      {"title":"Serveur Web Flask sur RPi","content":"Flask est parfait pour créer des APIs REST et interfaces web sur Raspberry Pi. Combinez Flask avec gpiozero pour un dashboard web de contrôle domotique accessible depuis votre smartphone.\n\nAccessible depuis tout appareil sur le réseau local. Nginx comme proxy inverse pour la production.","code":"from flask import Flask, jsonify\nfrom gpiozero import LED, Button\nimport os\n\napp = Flask(__name__)\nled = LED(17)\nbtn = Button(27)\n\n@app.route('/led/<state>', methods=['POST'])\ndef control(state):\n    if state == 'on': led.on()\n    elif state == 'off': led.off()\n    return jsonify({'led': state})\n\n@app.route('/status')\ndef status():\n    temp = os.popen('vcgencmd measure_temp').read().strip()\n    return jsonify({'led': led.is_lit, 'temp': temp})\n\nif __name__ == '__main__':\n    app.run(host='0.0.0.0', port=5000)"},
      {"title":"Traitement d'image avec OpenCV","content":"OpenCV sur Raspberry Pi permet la vision par ordinateur : détection de visages, suivi d'objets, lecture de QR codes, analyse vidéo. La caméra officielle PiCamera2 ou webcam USB sont supportées.\n\nLes modèles TFLite permettent la classification d'images en temps réel sur RPi 4.","code":"import cv2\nfrom picamera2 import Picamera2\n\ncam = Picamera2()\ncam.configure(cam.create_preview_configuration())\ncam.start()\n\nface_cascade = cv2.CascadeClassifier(\n    cv2.data.haarcascades +\n    'haarcascade_frontalface_default.xml')\n\nwhile True:\n    frame = cam.capture_array()\n    gray  = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)\n    faces = face_cascade.detectMultiScale(gray, 1.1, 4)\n    for (x, y, w, h) in faces:\n        cv2.rectangle(frame, (x,y), (x+w,y+h), (0,255,0), 2)\n    cv2.imshow('Détection', frame)\n    if cv2.waitKey(1) & 0xFF == ord('q'): break"},
      {"title":"Systemd & Services automatiques","content":"Pour qu'un script démarre automatiquement au boot, créez un service systemd. Essentiel pour les projets production (serveur domotique, robot). Systemd gère dépendances, redémarrages automatiques et logs.\n\nJournalctl -u service affiche les logs en temps réel.","code":"# /etc/systemd/system/cognitolab.service\n# [Unit]\n# Description=CognitoLab Flask Server\n# After=network.target\n#\n# [Service]\n# Type=simple\n# User=pi\n# WorkingDirectory=/home/pi/cognitolab\n# ExecStart=/usr/bin/python3 /home/pi/cognitolab/app.py\n# Restart=on-failure\n# RestartSec=5\n#\n# [Install]\n# WantedBy=multi-user.target\n\nsudo systemctl daemon-reload\nsudo systemctl enable cognitolab.service\nsudo systemctl start cognitolab.service\nsudo journalctl -u cognitolab -f  # Logs"},
      {"title":"Base de données SQLite","content":"SQLite stocke les données de capteurs sur RPi sans serveur. Légère et fiable, elle convient parfaitement pour l'historique IoT. Flask-SQLAlchemy simplifie l'ORM en Python.\n\nPour des données volumineuses ou des accès concurrents, utilisez PostgreSQL ou InfluxDB (séries temporelles).","code":"import sqlite3\nfrom datetime import datetime\n\nconn = sqlite3.connect('sensors.db')\nc = conn.cursor()\nc.execute('''\n  CREATE TABLE IF NOT EXISTS measurements (\n    id INTEGER PRIMARY KEY AUTOINCREMENT,\n    timestamp TEXT,\n    sensor TEXT,\n    value REAL\n  )\n''')\nconn.commit()\n\ndef log(sensor, value):\n    c.execute('INSERT INTO measurements VALUES (?,?,?,?)',\n      (None, datetime.now().isoformat(), sensor, value))\n    conn.commit()\n\ndef latest(n=10):\n    c.execute('SELECT * FROM measurements ORDER BY id DESC LIMIT ?', (n,))\n    return c.fetchall()\n\nlog('temperature', 23.5)\nprint(latest())"},
      {"title":"I2C et SPI en Python","content":"Le Raspberry Pi supporte I2C et SPI via smbus2 et spidev. Activez ces interfaces dans raspi-config → Interface Options. La commande i2cdetect -y 1 liste tous les périphériques I2C connectés.\n\nMême bibliothèques de capteurs qu'Arduino, portées en Python.","code":"import smbus2, spidev\n\n# I2C\nbus = smbus2.SMBus(1)\n# Lire WHO_AM_I du MPU6050 (addr 0x68, reg 0x75)\nwho = bus.read_byte_data(0x68, 0x75)\nprint(f'MPU6050 WHO_AM_I: 0x{who:02X}')\n\n# SPI\nspi = spidev.SpiDev()\nspi.open(0, 0)\nspi.max_speed_hz = 1000000\nresponse = spi.xfer2([0x55, 0xAA])\nprint(f'SPI réponse: {response}')\nspi.close()\n\n# Scanner I2C (terminal)\n# sudo i2cdetect -y 1"},
      {"title":"Docker sur Raspberry Pi","content":"Docker containerise vos applications pour un déploiement reproductible. Raspberry Pi OS 64-bit supporte Docker nativement. Docker Compose gère des architectures multi-conteneurs (app + base de données + reverse proxy).\n\nHome Assistant, Node-RED, Grafana, Portainer — tous disponibles comme images Docker officielles.","code":"# Installer Docker\ncurl -fsSL https://get.docker.com | sh\nsudo usermod -aG docker pi\n\n# docker-compose.yml\n# version: '3'\n# services:\n#   app:\n#     image: cognitolab/app:latest\n#     ports: [\"5000:5000\"]\n#     depends_on: [db]\n#   db:\n#     image: postgres:15\n#     environment:\n#       POSTGRES_PASSWORD: pass\n#     volumes:\n#       - pgdata:/var/lib/postgresql/data\n# volumes:\n#   pgdata:\n\ndocker compose up -d\ndocker compose logs -f"},
      {"title":"Projet : Hub domotique","content":"Projet complet : hub domotique avec Raspberry Pi, Flask, SQLite, relais GPIO, capteurs DHT22, et caméra de surveillance. Interface web accessible sur tout le réseau local.\n\nAccès distant via Cloudflare Tunnel — HTTPS gratuit sans ouvrir de port.","code":"# Architecture :\n# Flask + gpiozero → contrôle relais\n# DHT22 → température/humidité\n# PiCamera2 → flux MJPEG\n# SQLite → historique mesures\n# Systemd → démarrage automatique\n# Cloudflare Tunnel → accès distant HTTPS\n\n# Accès distant sécurisé\nsudo apt install cloudflared -y\ncloudflared tunnel --url http://localhost:5000\n# → URL HTTPS générée automatiquement"}
    ],
    "quiz": [
      {"q":"Quelle tension utilisent les GPIO du Raspberry Pi ?","opts":["5V","3.3V","1.8V","12V"],"answer":1},
      {"q":"Quelle commande liste les périphériques I2C ?","opts":["i2cscan","i2cdetect -y 1","gpio i2c scan","raspi-config"],"answer":1},
      {"q":"Quel OS de série utilise le Raspberry Pi ?","opts":["Ubuntu","Raspberry Pi OS","Debian Sid","Arch Linux"],"answer":1},
      {"q":"Quel outil gère les services au démarrage sur RPi ?","opts":["crontab","init.d","systemd","launchd"],"answer":2},
      {"q":"Quelle bibliothèque Python GPIO est la plus simple pour RPi ?","opts":["RPi.GPIO","gpiozero","pigpio","wiringpi"],"answer":1}
    ]
  },
  "stm32-bare": {
    "sections": [
      {"title":"Introduction STM32 & HAL","content":"STM32 est une famille ARM Cortex-M par STMicroelectronics. Le STM32F103 (Blue Pill) embarque un Cortex-M3 72MHz, 64KB Flash, 20KB SRAM — bien plus puissant qu'Arduino pour un coût similaire.\n\nLa HAL (Hardware Abstraction Layer) simplifie l'accès aux périphériques. STM32CubeMX génère automatiquement le code d'initialisation.","code":"// Clignotement LED (PC13 sur Blue Pill)\n#include \"main.h\"\n\nint main(void) {\n  HAL_Init();\n  SystemClock_Config();\n  MX_GPIO_Init();\n\n  while (1) {\n    HAL_GPIO_TogglePin(GPIOC, GPIO_PIN_13);\n    HAL_Delay(500);\n  }\n}\n// Dans MX_GPIO_Init() :\n// GPIO_InitStruct.Pin  = GPIO_PIN_13;\n// GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;\n// HAL_GPIO_Init(GPIOC, &GPIO_InitStruct);"},
      {"title":"GPIO et Registres directs","content":"La programmation bare-metal accède directement aux registres du MCU, sans couche d'abstraction. Plus rapide, et permet de comprendre exactement ce qui se passe.\n\nChaque GPIO a : MODER (mode), ODR (output), IDR (input), BSRR (set/reset atomique). Accès via pointeurs CMSIS.","code":"// Bare-metal : LED sur PC13 (Blue Pill)\n#include <stdint.h>\n\n#define RCC_APB2ENR  (*(volatile uint32_t*)0x40021018)\n#define GPIOC_CRH    (*(volatile uint32_t*)0x40011004)\n#define GPIOC_ODR    (*(volatile uint32_t*)0x4001100C)\n\nint main(void) {\n  RCC_APB2ENR  |= (1 << 4);    // Horloge GPIOC\n  GPIOC_CRH    &= ~(0xF<<20); // Clear PC13\n  GPIOC_CRH    |=  (0x2<<20); // Sortie 2MHz PP\n\n  while(1) {\n    GPIOC_ODR ^= (1 << 13);   // Toggle\n    for(volatile int i=0; i<500000; i++);\n  }\n}"},
      {"title":"UART & Communication","content":"L'UART du STM32 offre des vitesses supérieures à Arduino, supporte DMA, et dispose de plusieurs ports UART matériels. La configuration HAL ou bare-metal permet un contrôle total.\n\nLe DMA (Direct Memory Access) transmet des données sans intervention CPU, libérant des cycles de traitement.","code":"UART_HandleTypeDef huart1;\nuint8_t txBuf[] = \"CognitoLab STM32!\\r\\n\";\n\nvoid MX_USART1_UART_Init(void) {\n  huart1.Instance        = USART1;\n  huart1.Init.BaudRate   = 115200;\n  huart1.Init.WordLength = UART_WORDLENGTH_8B;\n  huart1.Init.StopBits   = UART_STOPBITS_1;\n  huart1.Init.Parity     = UART_PARITY_NONE;\n  huart1.Init.Mode       = UART_MODE_TX_RX;\n  HAL_UART_Init(&huart1);\n}\nvoid loop() {\n  HAL_UART_Transmit(&huart1, txBuf,\n    sizeof(txBuf), 100);\n  HAL_Delay(1000);\n}"},
      {"title":"Timers & PWM","content":"Les timers STM32 sont bien plus puissants qu'Arduino. TIM1 (Advanced) supporte 4 canaux PWM avec dead-time pour ponts en H. Les timers déclenchent interruptions, comptent des impulsions et capturent des signaux.\n\nAvec 72MHz et prescaler 72 : comptage à 1MHz — précision microseconde.","code":"// PWM 50Hz pour servo sur TIM3_CH1 (PA6)\n// 72MHz / 72 = 1MHz ; 1MHz/20000 = 50Hz\nvoid MX_TIM3_Init(void) {\n  TIM_HandleTypeDef htim3;\n  htim3.Instance        = TIM3;\n  htim3.Init.Prescaler  = 72 - 1;\n  htim3.Init.Period     = 20000 - 1;\n  HAL_TIM_PWM_Init(&htim3);\n\n  TIM_OC_InitTypeDef oc;\n  oc.OCMode  = TIM_OCMODE_PWM1;\n  oc.Pulse   = 1500; // 1500µs = 90°\n  HAL_TIM_PWM_ConfigChannel(&htim3, &oc,\n    TIM_CHANNEL_1);\n  HAL_TIM_PWM_Start(&htim3, TIM_CHANNEL_1);\n}"},
      {"title":"Interruptions & NVIC","content":"Le NVIC (Nested Vectored Interrupt Controller) Cortex-M gère jusqu'à 240 sources avec 256 niveaux de priorité. N'importe quelle broche GPIO peut déclencher une interruption EXTI (pas seulement D2/D3 comme Arduino).\n\nLes interruptions STM32 sont beaucoup plus flexibles et configurables qu'Arduino.","code":"void MX_GPIO_Init(void) {\n  GPIO_InitTypeDef GPIO_InitStruct = {0};\n  // PC14 en entrée pull-up, interruption front descendant\n  GPIO_InitStruct.Pin  = GPIO_PIN_14;\n  GPIO_InitStruct.Mode = GPIO_MODE_IT_FALLING;\n  GPIO_InitStruct.Pull = GPIO_PULLUP;\n  HAL_GPIO_Init(GPIOC, &GPIO_InitStruct);\n  HAL_NVIC_SetPriority(EXTI15_10_IRQn, 0, 0);\n  HAL_NVIC_EnableIRQ(EXTI15_10_IRQn);\n}\nvoid EXTI15_10_IRQHandler(void) {\n  HAL_GPIO_EXTI_IRQHandler(GPIO_PIN_14);\n}\nvoid HAL_GPIO_EXTI_Callback(uint16_t Pin) {\n  if (Pin == GPIO_PIN_14)\n    HAL_GPIO_TogglePin(GPIOC, GPIO_PIN_13);\n}"},
      {"title":"DMA — Direct Memory Access","content":"Le DMA transfère des données entre mémoire et périphériques (UART, SPI, ADC, I2C) sans impliquer le CPU. Pendant un transfert DMA, le CPU effectue d'autres calculs.\n\nL'ADC en mode DMA scan échantillonne plusieurs canaux en continu et stocke les résultats automatiquement.","code":"// ADC 3 canaux via DMA\nuint16_t adcValues[3]; // [IN0, IN1, IN2]\n\nvoid MX_ADC1_Init(void) {\n  ADC_HandleTypeDef hadc1;\n  hadc1.Init.ScanConvMode = ENABLE;\n  hadc1.Init.NbrOfConversion = 3;\n  hadc1.Init.ContinuousConvMode = ENABLE;\n  hadc1.Init.DMAContinuousRequests = ENABLE;\n  // ... init ...\n\n  ADC_ChannelConfTypeDef ch;\n  ch.Channel = ADC_CHANNEL_0; ch.Rank = 1;\n  HAL_ADC_ConfigChannel(&hadc1, &ch);\n  // + canaux 1 et 2...\n\n  HAL_ADC_Start_DMA(&hadc1,\n    (uint32_t*)adcValues, 3);\n  // adcValues mis à jour automatiquement !"},
      {"title":"Projet : Contrôleur BLDC","content":"Projet avancé : contrôle d'un moteur brushless (BLDC) via PWM, avec MPU6050 en I2C pour la mesure d'inclinaison, et UART pour la télémétrie. Exploite timers avancés TIM1, DMA ADC, interruptions I2C.\n\nApplications : drones, robots, véhicules autonomes.","code":"// Architecture\n// TIM1_CH1 → ESC (PWM 50-400Hz)\n// I2C1 → MPU6050 (gyro/accél)\n// USART1 → Télémétrie\n// TIM2 → Boucle contrôle 1kHz\n\n// Signal ESC : 1000µs=0%, 2000µs=100%\nvoid control_loop() { // @ 1kHz\n  read_mpu6050(&ax, &ay, &az,\n               &gx, &gy, &gz);\n  float pitch = atan2(ay, az) * 180/M_PI;\n  float err   = target - pitch;\n  float corr  = Kp*err + Kd*(err-last_err);\n  set_esc(throttle + corr);\n  last_err = err;\n}"}
    ],
    "quiz": [
      {"q":"Quel cœur ARM utilise le STM32F103 ?","opts":["Cortex-M0","Cortex-M3","Cortex-M4","Cortex-M7"],"answer":1},
      {"q":"Quelle est la fréquence maximale du STM32F103 ?","opts":["48 MHz","72 MHz","120 MHz","168 MHz"],"answer":1},
      {"q":"Que signifie DMA ?","opts":["Data Memory Array","Direct Memory Access","Dynamic Module Allocation","Double Mode ADC"],"answer":1},
      {"q":"Sur quelle broche est la LED intégrée du Blue Pill ?","opts":["PA5","PB12","PC13","PD2"],"answer":2},
      {"q":"Quel outil génère automatiquement le code d'initialisation STM32 ?","opts":["Arduino IDE","STM32CubeMX","Keil MDK","PlatformIO"],"answer":1}
    ]
  },
  "ros-intro": {
    "sections": [
      {"title":"Introduction à ROS 2","content":"ROS 2 (Robot Operating System 2) est un framework open-source pour le développement robotique. Conçu pour les systèmes temps réel et multi-robots. Il utilise DDS (Data Distribution Service) pour la communication.\n\nConceptes clés : Nodes (processus), Topics (pub/sub asynchrone), Services (requête/réponse), Actions (tâches longues avec feedback).","code":"# Installation ROS 2 Humble (Ubuntu 22.04)\nsudo apt install ros-humble-desktop\necho \"source /opt/ros/humble/setup.bash\" >> ~/.bashrc\n\n# Workspace\nmkdir -p ~/ros2_ws/src\ncd ~/ros2_ws && colcon build\nsource install/setup.bash\n\n# Test\nros2 run demo_nodes_cpp talker   # Terminal 1\nros2 run demo_nodes_cpp listener  # Terminal 2"},
      {"title":"Nodes, Topics & Messages","content":"Un Node est un processus ROS 2 communiquant via Topics. Un publisher envoie des messages, un subscriber les reçoit. La communication est asynchrone et découplée.\n\nROS 2 fournit des types standards (geometry_msgs, sensor_msgs, std_msgs). Créez vos propres messages avec des fichiers .msg.","code":"import rclpy\nfrom rclpy.node import Node\nfrom std_msgs.msg import String\n\nclass MinimalPublisher(Node):\n    def __init__(self):\n        super().__init__('minimal_publisher')\n        self.pub = self.create_publisher(\n            String, 'cognitolab/data', 10)\n        self.timer = self.create_timer(\n            1.0, self.callback)\n        self.count = 0\n\n    def callback(self):\n        msg = String()\n        msg.data = f'CognitoLab: {self.count}'\n        self.pub.publish(msg)\n        self.count += 1\n\ndef main():\n    rclpy.init()\n    rclpy.spin(MinimalPublisher())\n    rclpy.shutdown()"},
      {"title":"Services & Actions","content":"Services : communication requête/réponse synchrone pour les opérations ponctuelles (changer un paramètre, interroger l'état). Actions : tâches longues avec feedback (navigation, bras robotique).\n\nRègle : Service pour 'porte ouverte ?' (instantané), Action pour 'aller au point A' (long).","code":"from std_srvs.srv import SetBool\nfrom rclpy.node import Node\nimport rclpy\n\nclass LEDService(Node):\n    def __init__(self):\n        super().__init__('led_service')\n        self.srv = self.create_service(\n            SetBool, 'set_led', self.callback)\n\n    def callback(self, request, response):\n        state = 'ON' if request.data else 'OFF'\n        self.get_logger().info(f'LED: {state}')\n        response.success = True\n        response.message = f'LED: {state}'\n        return response\n\n# ros2 service call /set_led std_srvs/srv/SetBool \"{data: true}\""},
      {"title":"Navigation & Nav2","content":"Nav2 est le stack de navigation ROS 2 : planification de chemin, évitement d'obstacles, localisation (AMCL) et cartographie (SLAM). Gazebo est le simulateur 3D officiel.\n\nPipeline : LIDAR → Carte → Localisation → Planification → Contrôle → Actionneurs.","code":"# TurtleBot3 en simulation Gazebo\nexport TURTLEBOT3_MODEL=burger\n\n# Terminal 1 : Gazebo\nros2 launch turtlebot3_gazebo \\\n  turtlebot3_world.launch.py\n\n# Terminal 2 : Navigation\nros2 launch nav2_bringup \\\n  navigation_launch.py \\\n  use_sim_time:=True map:=./map.yaml\n\n# Terminal 3 : RViz2\nros2 launch nav2_bringup rviz_launch.py\n\n# Envoyer un objectif\nros2 action send_goal /navigate_to_pose \\\n  nav2_msgs/action/NavigateToPose \\\n  \"{pose: {header: {frame_id: 'map'}, pose: {position: {x: 1.0, y: 0.5}}}}\""},
      {"title":"Vision par ordinateur","content":"Le package image_transport échange des flux vidéo entre nodes ROS 2. cv_bridge convertit entre ROS Image et OpenCV. Pipeline typique : caméra → détection → commande.\n\nTopics standards : sensor_msgs/Image pour les images brutes, sensor_msgs/CameraInfo pour la calibration.","code":"from sensor_msgs.msg import Image\nfrom cv_bridge import CvBridge\nimport cv2, rclpy\nfrom rclpy.node import Node\n\nclass VisionNode(Node):\n    def __init__(self):\n        super().__init__('vision_node')\n        self.bridge = CvBridge()\n        self.sub = self.create_subscription(\n            Image, '/camera/image_raw',\n            self.callback, 10)\n\n    def callback(self, msg):\n        cv_img = self.bridge.imgmsg_to_cv2(\n            msg, 'bgr8')\n        gray  = cv2.cvtColor(cv_img,\n            cv2.COLOR_BGR2GRAY)\n        edges = cv2.Canny(gray, 50, 150)\n        cv2.imshow('Edges', edges)\n        cv2.waitKey(1)"},
      {"title":"TF2 — Transformations","content":"TF2 gère les transformations spatiales entre les référentiels du robot (base, capteurs, effecteurs). Il maintient un arbre de transformations dans le temps.\n\nExemple : transformer les coordonnées d'un obstacle détecté par le LIDAR (frame: laser) en coordonnées du robot (frame: base_link) pour la navigation.","code":"from tf2_ros import TransformListener, Buffer\nfrom rclpy.node import Node\nimport rclpy\n\nclass TFNode(Node):\n    def __init__(self):\n        super().__init__('tf_node')\n        self.buf = Buffer()\n        self.tf  = TransformListener(self.buf, self)\n        self.timer = self.create_timer(\n            1.0, self.on_timer)\n\n    def on_timer(self):\n        try:\n            t = self.buf.lookup_transform(\n                'base_link', 'map',\n                rclpy.time.Time())\n            self.get_logger().info(\n                f'X={t.transform.translation.x:.2f}')\n        except Exception as e:\n            self.get_logger().warn(str(e))"},
      {"title":"SLAM — Cartographie autonome","content":"SLAM (Simultaneous Localization And Mapping) permet au robot de construire une carte tout en se localisant. slam_toolbox est la solution ROS 2 recommandée.\n\nCombinez SLAM avec Nav2 pour un robot capable d'explorer une pièce inconnue et naviguer de façon autonome.","code":"# Installer slam_toolbox\nsudo apt install ros-humble-slam-toolbox\n\n# Lancer SLAM (online async)\nros2 launch slam_toolbox \\\n  online_async_launch.py \\\n  use_sim_time:=True\n\n# Téléopération pour explorer\nros2 run turtlebot3_teleop teleop_keyboard\n\n# Sauvegarder la carte\nros2 service call /slam_toolbox/save_map \\\n  slam_toolbox/srv/SaveMap \\\n  \"{name: {data: 'ma_carte'}}\"\n# → ma_carte.pgm + ma_carte.yaml"},
      {"title":"micro-ROS (ESP32 + ROS 2)","content":"micro-ROS étend ROS 2 aux microcontrôleurs. L'ESP32 devient un node ROS 2 complet, publiant des données de capteurs directement dans le graphe ROS sans ordinateur intermédiaire.\n\nmicro-ROS Agent (sur PC) fait le pont entre MCU (UART/WiFi) et le réseau ROS 2 DDS.","code":"// micro-ROS sur ESP32 (PlatformIO)\n#include <micro_ros_arduino.h>\n#include <std_msgs/msg/float32.h>\n#include <rclc/rclc.h>\n\nrcl_publisher_t publisher;\nstd_msgs__msg__Float32 msg;\n\nvoid setup() {\n  set_microros_transports();\n  rcl_allocator_t alloc =\n    rcl_get_default_allocator();\n  rclc_support_t support;\n  rclc_support_init(&support, 0, NULL, &alloc);\n  rcl_node_t node;\n  rclc_node_init_default(&node,\n    \"esp32_node\", \"\", &support);\n  rclc_publisher_init_default(&publisher,\n    &node,\n    ROSIDL_GET_MSG_TYPE_SUPPORT(\n      std_msgs, msg, Float32),\n    \"temperature\");\n}\nvoid loop() {\n  msg.data = 23.5;\n  rcl_publish(&publisher, &msg, NULL);\n  delay(1000);\n}"},
      {"title":"MoveIt 2 — Bras robotique","content":"MoveIt 2 gère la cinématique inverse, la planification de trajectoires et l'évitement de collisions pour bras robotiques. Rviz2 visualise le bras et permet de définir des poses cibles interactivement.\n\nSupporté par les principaux bras industriels et bras éducatifs (Interbotix, UR, Franka).","code":"import rclpy\nfrom moveit.planning import MoveItPy\n\nrclpy.init()\nmoveit = MoveItPy(node_name='moveit_ctl')\narm    = moveit.get_planning_component('manipulator')\n\nfrom geometry_msgs.msg import PoseStamped\ntarget = PoseStamped()\ntarget.header.frame_id = 'base_link'\ntarget.pose.position.x = 0.3\ntarget.pose.position.z = 0.4\ntarget.pose.orientation.w = 1.0\n\narm.set_goal_state(\n  pose_stamped_msg=target,\n  pose_link='tool0')\nplan = arm.plan()\nif plan:\n    moveit.execute(plan, controllers=[])"},
      {"title":"Projet : Robot de livraison autonome","content":"Projet capstone : robot mobile autonome avec ROS 2, Nav2, SLAM, caméra et bras manipulateur. Le robot navigue, détecte un objet, le saisit avec le bras, et livre à destination.\n\nStack : ROS 2 Humble, Nav2, SLAM Toolbox, MoveIt 2, OpenCV, micro-ROS pour actionneurs bas niveau.","code":"# Architecture complète\n# PC (ROS 2) :\n#   nav2          → Navigation autonome\n#   slam_toolbox  → Cartographie\n#   moveit        → Contrôle bras\n#   vision_node   → Détection OpenCV\n#\n# Raspberry Pi :\n#   hardware_interface → Drivers moteurs\n#   lidar_driver       → RPLidar A1\n#   camera_driver      → PiCamera2\n#\n# ESP32 (micro-ROS) :\n#   encoders_publisher  → Odométrie\n#   cmd_vel_subscriber  → Commande moteurs\n\nros2 launch robot_bringup full_system.launch.py"},
      {"title":"Paramètres & Lifecycle Nodes","content":"Les paramètres ROS 2 permettent de configurer les nodes sans recompilation. Les Lifecycle Nodes offrent un contrôle d'état explicite (unconfigured → configured → active → deactivated).\n\nEssentiels pour les systèmes robotiques de production nécessitant un démarrage/arrêt contrôlé.","code":"import rclpy\nfrom rclpy.node import Node\nfrom rcl_interfaces.msg import SetParametersResult\n\nclass ParamNode(Node):\n    def __init__(self):\n        super().__init__('param_node')\n        # Déclarer un paramètre avec valeur par défaut\n        self.declare_parameter('speed', 1.0)\n        self.declare_parameter('debug', False)\n        # Callback si paramètre changé\n        self.add_on_set_parameters_callback(\n            self.on_param_change)\n\n    def on_param_change(self, params):\n        for p in params:\n            self.get_logger().info(\n                f'{p.name} = {p.value}')\n        return SetParametersResult(successful=True)\n\n# Changer depuis terminal :\n# ros2 param set /param_node speed 2.5"},
      {"title":"Sécurité & DDS Configuration","content":"ROS 2 Security (SROS2) utilise DDS-Security pour chiffrer et authentifier les communications entre nodes. Essentiel pour les robots industriels et les véhicules autonomes.\n\nLes politiques de sécurité définissent quels nodes peuvent publier ou souscrire à quels topics.","code":"# Générer les keystore et certificats\nros2 security create_keystore ~/keystore\nros2 security create_enclave \\\n  ~/keystore /my_robot/sensor_node\nros2 security create_permission \\\n  ~/keystore /my_robot/sensor_node \\\n  ~/policies/sensor_policy.xml\n\n# Lancer un node sécurisé\nROS_SECURITY_KEYSTORE=~/keystore \\\nROS_SECURITY_ENABLE=true \\\nROS_SECURITY_STRATEGY=Enforce \\\nros2 run my_pkg sensor_node \\\n  --ros-args --enclave /my_robot/sensor_node"}
    ],
    "quiz": [
      {"q":"Quel protocole de communication utilise ROS 2 ?","opts":["ROS Bridge","DDS","MQTT","WebSocket"],"answer":1},
      {"q":"Pour une tâche longue avec feedback, on utilise...","opts":["Topic","Service","Action","Parameter"],"answer":2},
      {"q":"Quel outil gère les transformations spatiales dans ROS 2 ?","opts":["Nav2","TF2","MoveIt","Gazebo"],"answer":1},
      {"q":"Que signifie SLAM ?","opts":["Single Laser And Mapping","Simultaneous Localization And Mapping","Sensor-based Local Area Movement","System Level Autonomous Mapping"],"answer":1},
      {"q":"Quel outil compile les packages ROS 2 ?","opts":["catkin_make","cmake","colcon","ament"],"answer":2}
    ]
  },
  "esp32-display": {
    "sections": [
      {"title":"OLED SSD1306 avec ESP32","content":"L'OLED SSD1306 128×64 pixels se connecte via I2C (4 fils) avec un excellent contraste sans rétroéclairage. Sur ESP32 : SDA=GPIO21, SCL=GPIO22. La bibliothèque Adafruit GFX fournit des fonctions graphiques complètes.\n\nAdresse I2C : 0x3C (la plupart des modules), 0x3D (certains modules avec A0 à HIGH).","code":"#include <Wire.h>\n#include <Adafruit_GFX.h>\n#include <Adafruit_SSD1306.h>\n\nAdafruit_SSD1306 display(128, 64, &Wire, -1);\n\nvoid setup() {\n  Wire.begin(21, 22); // SDA, SCL\n  display.begin(SSD1306_SWITCHCAPVCC, 0x3C);\n  display.clearDisplay();\n  display.setTextColor(WHITE);\n  display.setTextSize(2);\n  display.setCursor(0, 0);\n  display.println(\"CognitoLab\");\n  display.setTextSize(1);\n  display.println(\"ESP32 + OLED\");\n  display.display();\n}"},
      {"title":"TFT ILI9341 couleur","content":"L'écran TFT ILI9341 2.8\" (320×240 pixels, 65536 couleurs RGB565) utilise SPI pour une communication rapide. TFT_eSPI est optimisé ESP32 avec DMA pour des animations fluides.\n\nAvec 65536 couleurs, vous affichez graphiques, jauges animées et interfaces utilisateur complètes.","code":"#include <TFT_eSPI.h>\nTFT_eSPI tft;\n\nvoid setup() {\n  tft.init();\n  tft.setRotation(1);\n  tft.fillScreen(TFT_BLACK);\n  tft.setTextColor(TFT_CYAN, TFT_BLACK);\n  tft.setTextSize(2);\n  tft.setCursor(10, 10);\n  tft.println(\"CognitoLab\");\n  // Jauge\n  int val = 75;\n  tft.drawRect(10, 40, 200, 20, TFT_WHITE);\n  tft.fillRect(11, 41, val*198/100, 18, TFT_GREEN);\n  tft.setTextColor(TFT_WHITE);\n  tft.setCursor(220, 44);\n  tft.print(val); tft.print(\"%\");\n}"},
      {"title":"DHT22 & BMP280","content":"Associer DHT22 (température/humidité) et BMP280 (pression/altitude) pour une station météo complète. Affichage temps réel sur OLED ou TFT avec graphiques.\n\nLe BMP280 permet aussi de calculer l'altitude relative à partir de la pression barométrique.","code":"#include <DHT.h>\n#include <Adafruit_BMP280.h>\n\nDHT dht(4, DHT22);\nAdafruit_BMP280 bmp;\n\nvoid setup() {\n  Serial.begin(115200);\n  dht.begin();\n  bmp.begin(0x76);\n}\nvoid loop() {\n  float t   = dht.readTemperature();\n  float h   = dht.readHumidity();\n  float p   = bmp.readPressure() / 100.0; // hPa\n  float alt = bmp.readAltitude(1013.25);\n  Serial.printf(\n    \"DHT: %.1f°C %.1f%%  BMP: %.2fhPa %.1fm\\n\",\n    t, h, p, alt);\n  delay(2000);\n}"},
      {"title":"MPU6050 — IMU 6 axes","content":"Le MPU6050 est un IMU 6 axes : accéléromètre ±16g et gyroscope ±2000°/s. Son DMP intégré calcule les angles (roll, pitch, yaw) directement. Adresse I2C : 0x68.\n\nApplications : stabilisation de drone, détection de chute, interface gestuelle, niveau numérique.","code":"#include <Wire.h>\n#include <MPU6050_tockn.h>\n\nMPU6050 mpu(Wire);\n\nvoid setup() {\n  Serial.begin(115200);\n  Wire.begin(21, 22);\n  mpu.begin();\n  mpu.calcGyroOffsets(true); // Calibration\n}\nvoid loop() {\n  mpu.update();\n  Serial.printf(\"Roll:%.1f Pitch:%.1f Yaw:%.1f\\n\",\n    mpu.getAngleX(),\n    mpu.getAngleY(),\n    mpu.getAngleZ());\n  delay(10);\n}"},
      {"title":"Interface web avec graphiques","content":"Servez un dashboard web depuis l'ESP32 avec Chart.js pour visualiser les données en temps réel. fetch() récupère les données JSON périodiquement.\n\nWebSocket permet une mise à jour continue sans rechargement, pour une interface encore plus réactive.","code":"#include <WebServer.h>\nWebServer server(80);\nfloat temperature = 23.5;\n\nconst char* html = R\"(\n<html><body style='background:#0d1421;color:white'>\n<canvas id='c' width='400' height='200'></canvas>\n<script src='https://cdn.jsdelivr.net/npm/chart.js'></script>\n<script>\nconst chart = new Chart(document.getElementById('c'),\n  {type:'line', data:{labels:[],\n   datasets:[{label:'Temp',data:[],\n   borderColor:'#42A5F5'}]}});\nsetInterval(async()=>{\n  const d = await fetch('/data').then(r=>r.json());\n  chart.data.labels.push(new Date().toLocaleTimeString());\n  chart.data.datasets[0].data.push(d.temperature);\n  if(chart.data.labels.length>20){\n    chart.data.labels.shift();\n    chart.data.datasets[0].data.shift();}\n  chart.update();\n}, 2000);\n</script></body></html>)\";\n\nvoid setup() {\n  server.on(\"/\", [](){ server.send(200,\"text/html\",html); });\n  server.on(\"/data\", [](){\n    server.send(200, \"application/json\",\n      \"{\\\"temperature\\\":\" + String(temperature,1) + \"}\");\n  });\n  server.begin();\n}\nvoid loop() { server.handleClient(); }"},
      {"title":"Projet : Station météo complète","content":"Projet final : station météo ESP32 avec DHT22, BMP280, écran OLED 128×64, dashboard web local, et envoi sur ThingSpeak. Autonomie sur batterie 18650 grâce au deep sleep.\n\nBoîtier imprimable 3D disponible sur le repo GitHub CognitoLab.","code":"// Projet disponible sur :\n// github.com/cognitolab/esp32-weather\nvoid setup() {\n  initDisplay();   // OLED SSD1306\n  initSensors();   // DHT22 + BMP280\n  connectWiFi();\n  initWebServer(); // Dashboard local\n  sendToThingSpeak();\n  displayData();   // Afficher sur OLED\n  deepSleep(15 * 60); // 15 min\n}"}
    ],
    "quiz": [
      {"q":"Quelle est la résolution de l'OLED SSD1306 ?","opts":["64×48","128×32","128×64","240×320"],"answer":2},
      {"q":"Quel protocole utilise l'OLED SSD1306 ?","opts":["SPI","I2C","UART","1-Wire"],"answer":1},
      {"q":"Combien d'axes mesure le MPU6050 ?","opts":["3 (accéléro)","6 (accéléro+gyro)","9 (accéléro+gyro+magnéto)","1"],"answer":1},
      {"q":"Sur l'ESP32, quelles broches I2C sont SDA/SCL ?","opts":["D4/D5","GPIO21/GPIO22","A4/A5","GPIO32/GPIO33"],"answer":1},
      {"q":"Quelle bibliothèque TFT est optimisée pour ESP32 ?","opts":["Adafruit_GFX","TFT_eSPI","U8g2","LiquidCrystal"],"answer":1}
    ]
  },
  "pico-micropython": {
    "sections": [
      {"title":"Raspberry Pi Pico & MicroPython","content":"Le Pico est basé sur le RP2040 (dual Cortex-M0+ 133MHz, 264KB SRAM, 2MB Flash). MicroPython est Python 3 pour microcontrôleurs.\n\nFlasher MicroPython : téléchargez le .uf2 sur micropython.org, maintenez BOOTSEL en connectant le Pico, copiez le .uf2 dans le lecteur qui apparaît.","code":"import sys, os, gc\nprint(sys.version)\nprint(os.uname())\nprint(gc.mem_free(), 'B libres')\n\n# Blink LED intégrée (GP25)\nfrom machine import Pin\nimport time\n\nled = Pin(25, Pin.OUT)\nwhile True:\n    led.toggle()\n    time.sleep(0.5)"},
      {"title":"GPIO, PWM et ADC","content":"Le Pico offre 26 GPIO dont 3 entrées ADC 12-bit (GP26, GP27, GP28) et 16 canaux PWM. machine.ADC() et machine.PWM() donnent un accès direct en Python.\n\nLa fréquence PWM est programmable de quelques Hz à 65kHz. Le duty cycle est sur 16 bits (0-65535).","code":"from machine import Pin, PWM, ADC\nimport time\n\npwm = PWM(Pin(0))\npwm.freq(1000)        # 1kHz\n\nadc = ADC(Pin(26))    # GP26 = ADC0\n\nwhile True:\n    val  = adc.read_u16()   # 0-65535\n    duty = val              # Mapper direct\n    pwm.duty_u16(duty)\n    voltage = val * 3.3 / 65535\n    print(f'ADC:{val} ({voltage:.2f}V)')\n    time.sleep(0.1)"},
      {"title":"PIO — Programmable I/O","content":"Le PIO est la fonctionnalité unique du RP2040. 8 machines d'état programmables implémentant n'importe quel protocole série à timing parfait (WS2812, SPI, I2S) sans charger le CPU.\n\nLe langage PIO assembly (9 instructions) permet des protocoles à la nanoseconde près.","code":"import rp2\nfrom machine import Pin\n\n@rp2.asm_pio(\n    sideset_init=rp2.PIO.OUT_LOW,\n    out_shiftdir=rp2.PIO.SHIFT_LEFT,\n    autopull=True, pull_thresh=24)\ndef ws2812():\n    T1 = 2; T2 = 5; T3 = 3\n    wrap_target()\n    label('bitloop')\n    out(x, 1)             .side(0) [T3-1]\n    jmp(not_x, 'do_zero') .side(1) [T1-1]\n    jmp('bitloop')         .side(1) [T2-1]\n    label('do_zero')\n    nop()                  .side(0) [T2-1]\n    wrap()\n\nsm = rp2.StateMachine(0, ws2812,\n    freq=8_000_000, sideset_base=Pin(22))\nsm.active(1)\n# Rouge sur 8 LEDs WS2812B\nfor _ in range(8):\n    sm.put(0xFF0000 << 8, 8)"},
      {"title":"I2C, SPI & UART","content":"MicroPython sur Pico supporte tous les protocoles : 2 bus I2C, 2 bus SPI, 2 UART matériels. La bibliothèque machine fournit des classes Python pour chaque protocole.\n\nmachine.I2C(0) utilise GP4 (SDA) et GP5 (SCL) par défaut sur le Pico.","code":"from machine import I2C, SPI, UART, Pin\n\n# I2C : scanner\ni2c = I2C(0, scl=Pin(5), sda=Pin(4),\n          freq=400_000)\nprint('I2C:', i2c.scan())\n\n# Lire 6 octets MPU6050\nbuf = i2c.readfrom_mem(0x68, 0x3B, 6)\nimport struct\nax, ay, az = struct.unpack('>hhh', buf)\nprint(f'Acc: {ax},{ay},{az}')\n\n# SPI\nspi = SPI(0, baudrate=1_000_000,\n          sck=Pin(18), mosi=Pin(19),\n          miso=Pin(16))\ncs = Pin(17, Pin.OUT)\ncs.value(0)\nspi.write(b'\\x55\\xAA')\ncs.value(1)"},
      {"title":"asyncio & Multicore","content":"Le RP2040 dispose de 2 cœurs. MicroPython supporte asyncio pour les tâches concurrentes IO-bound, et _thread pour le second cœur. asyncio est idéal pour capteurs + réseau + affichage simultanés.\n\nLes coroutines asyncio ne bloquent pas — await asyncio.sleep() cède le contrôle aux autres tâches.","code":"import asyncio\nfrom machine import Pin\n\nled1 = Pin(0, Pin.OUT)\nled2 = Pin(1, Pin.OUT)\n\nasync def blink_slow():\n    while True:\n        led1.toggle()\n        await asyncio.sleep(1.0)\n\nasync def blink_fast():\n    while True:\n        led2.toggle()\n        await asyncio.sleep(0.1)\n\nasync def read_sensor():\n    from machine import ADC\n    adc = ADC(Pin(26))\n    while True:\n        print(f'ADC: {adc.read_u16()}')\n        await asyncio.sleep(0.5)\n\nasync def main():\n    await asyncio.gather(\n        blink_slow(), blink_fast(), read_sensor())\n\nasyncio.run(main())"},
      {"title":"Pico W — WiFi & Web","content":"Le Raspberry Pi Pico W ajoute un module WiFi/Bluetooth (CYW43439). Il héberge un serveur web, appelle des APIs et fait du MQTT — tout en MicroPython.\n\nMicrodot est un framework web léger pour MicroPython, similaire à Flask.","code":"import network, urequests, time\nfrom machine import Pin\n\n# Connexion WiFi\nwlan = network.WLAN(network.STA_IF)\nwlan.active(True)\nwlan.connect('SSID', 'MOT_DE_PASSE')\nwhile not wlan.isconnected():\n    time.sleep(0.5)\nprint('IP:', wlan.ifconfig()[0])\n\n# Serveur web avec Microdot\nfrom microdot import Microdot\napp = Microdot()\nled = Pin('LED', Pin.OUT)\n\n@app.get('/')\nasync def index(req):\n    return '<h1>Pico W!</h1>'\n\n@app.get('/led')\nasync def toggle(req):\n    led.toggle()\n    return {'led': led.value()}\n\napp.run(port=80)"},
      {"title":"Projet : Clavier MIDI USB","content":"Le Pico supporte USB natif, permettant de créer un contrôleur MIDI USB sans pilote. Les boutons déclenchent des notes, le potentiomètre contrôle le volume.\n\nLe Pico apparaît comme un périphérique MIDI USB standard sur Windows, Mac et Linux.","code":"import usb_midi, adafruit_midi\nfrom adafruit_midi.note_on import NoteOn\nfrom adafruit_midi.note_off import NoteOff\nfrom machine import Pin\nimport time\n\nmidi = adafruit_midi.MIDI(\n    midi_out=usb_midi.ports[1], out_channel=0)\n\nbtns  = [Pin(i, Pin.IN, Pin.PULL_UP)\n          for i in range(2, 10)]\nNOTES = [60,62,64,65,67,69,71,72] # Do→Do\n\nwhile True:\n    for i, btn in enumerate(btns):\n        if not btn.value():\n            midi.send(NoteOn(NOTES[i], 100))\n            while not btn.value():\n                time.sleep(0.01)\n            midi.send(NoteOff(NOTES[i], 0))"}
    ],
    "quiz": [
      {"q":"Quel processeur utilise le Raspberry Pi Pico ?","opts":["ATmega2560","ESP32","RP2040","STM32F4"],"answer":2},
      {"q":"Combien de cœurs Cortex-M0+ possède le RP2040 ?","opts":["1","2","4","8"],"answer":1},
      {"q":"Quelle est la fonctionnalité unique du RP2040 ?","opts":["WiFi intégré","PIO (Programmable I/O)","Bluetooth","GPU"],"answer":1},
      {"q":"Comment flasher MicroPython sur le Pico ?","opts":["Arduino IDE","Maintenir BOOTSEL + copier .uf2","STM32CubeProgrammer","apt install"],"answer":1},
      {"q":"Quelle résolution a l'ADC du RP2040 ?","opts":["8 bits","10 bits","12 bits","16 bits"],"answer":2}
    ]
  },
  "petit-projets": {
    "sections": [
      {"title":"Projets LEDs & Affichage","content":"Les projets LED combinent GPIO, PWM, protocoles série et bibliothèques. NeoPixels, matrices LED, bargraphs — chaque projet ajoute une compétence.\n\nProgression : LED simple → LED RGB → Barre 10 segments → NeoPixel anneau → Matrice 8×8.","code":"// NeoPixel effet arc-en-ciel\n#include <Adafruit_NeoPixel.h>\n#define PIN   6\n#define NLEDS 12\n\nAdafruit_NeoPixel ring(NLEDS, PIN,\n    NEO_GRB + NEO_KHZ800);\n\nuint32_t wheel(byte pos) {\n  if (pos < 85)\n    return ring.Color(255-pos*3, 0, pos*3);\n  if (pos < 170) { pos -= 85;\n    return ring.Color(0, pos*3, 255-pos*3); }\n  pos -= 170;\n  return ring.Color(pos*3, 255-pos*3, 0);\n}\nvoid setup() { ring.begin(); ring.show(); }\nvoid loop() {\n  static uint16_t j = 0;\n  for(int i=0; i<NLEDS; i++)\n    ring.setPixelColor(i,\n      wheel((i*256/NLEDS+j)&255));\n  ring.show(); j=(j+1)%256; delay(10);\n}"},
      {"title":"Projets Capteurs","content":"Les capteurs rendent les projets interactifs. Thermomètre, détecteur de mouvement, station météo, mesure de distance — chaque capteur ouvre de nouvelles possibilités.\n\nProgression : LDR photorésistance → DHT22 → HC-SR04 ultrason → PIR mouvement → RFID accès.","code":"// Alarme ultrasonique\n#include <NewPing.h>\n#define TRIG  9\n#define ECHO 10\n#define MAX  200\n#define BUZ   8\n\nNewPing sonar(TRIG, ECHO, MAX);\n\nvoid setup() { pinMode(BUZ, OUTPUT); }\nvoid loop() {\n  int dist = sonar.ping_cm();\n  if (dist > 0 && dist < 50) {\n    // Plus proche = bip plus rapide\n    int freq = map(dist, 5, 50, 2000, 200);\n    tone(BUZ, 880, freq);\n    delay(freq);\n  } else {\n    noTone(BUZ);\n    delay(100);\n  }\n}"},
      {"title":"Projets Domotique","content":"Contrôlez des appareils, lumières et températures avec Arduino — sans abonnement cloud. Relais pour le 220V, capteurs pour la surveillance, contrôleur Arduino Mega ou ESP32.\n\nCombinez plusieurs relais pour une maison intelligente locale complète.","code":"// Thermostat automatique\n#include <DHT.h>\nDHT dht(7, DHT22);\n\nconst int RELAY_HEAT = 8;\nconst float TARGET   = 22.0;\nconst float HYSTERESIS = 0.5;\n\nvoid setup() {\n  dht.begin();\n  pinMode(RELAY_HEAT, OUTPUT);\n  digitalWrite(RELAY_HEAT, HIGH); // OFF\n}\nvoid loop() {\n  float t = dht.readTemperature();\n  if (t < TARGET - HYSTERESIS)\n    digitalWrite(RELAY_HEAT, LOW);  // ON\n  else if (t > TARGET + HYSTERESIS)\n    digitalWrite(RELAY_HEAT, HIGH); // OFF\n  delay(2000);\n}"},
      {"title":"Projets Communication","content":"Bluetooth, IR, NFC, RF 433MHz — contrôlez à distance et échangez des données entre systèmes. Chaque protocole a ses avantages selon la portée et la consommation.\n\nProgression : télécommande IR → Bluetooth HC-05 → RF 433MHz → nRF24L01 bidirectionnel.","code":"// Décodeur télécommande IR\n#include <IRremote.hpp>\n#define IR_PIN 11\n\nvoid setup() {\n  Serial.begin(9600);\n  IrReceiver.begin(IR_PIN,\n    ENABLE_LED_FEEDBACK);\n}\nvoid loop() {\n  if (IrReceiver.decode()) {\n    uint32_t code =\n      IrReceiver.decodedIRData.decodedRawData;\n    Serial.print(\"Code: 0x\");\n    Serial.println(code, HEX);\n    switch(code) {\n      case 0xBF40FF00:\n        Serial.println(\"Play\"); break;\n      case 0xF609FF00:\n        Serial.println(\"Vol+\"); break;\n    }\n    IrReceiver.resume();\n  }\n}"},
      {"title":"Projets Robots","content":"Robots suiveurs de ligne, éviteurs d'obstacles, bras mécaniques — les projets robotiques combinent moteurs, capteurs et algorithmes.\n\nProgression : moteur DC → servo → pont en H L298N → robot 2 roues → suiveur de ligne → éviteur d'obstacles.","code":"// Robot suiveur de ligne\n// IR L=D2, R=D3 | Moteurs L298N\nconst int M1A=8,M1B=9,M2A=10,M2B=11;\nconst int IRL=2, IRR=3;\n\nvoid fwd()  { digitalWrite(M1A,HIGH);digitalWrite(M1B,LOW);digitalWrite(M2A,HIGH);digitalWrite(M2B,LOW); }\nvoid left() { digitalWrite(M1A,LOW);digitalWrite(M1B,HIGH);digitalWrite(M2A,HIGH);digitalWrite(M2B,LOW); }\nvoid rght() { digitalWrite(M1A,HIGH);digitalWrite(M1B,LOW);digitalWrite(M2A,LOW);digitalWrite(M2B,HIGH); }\nvoid stp()  { for(int p:{M1A,M1B,M2A,M2B})digitalWrite(p,LOW); }\n\nvoid setup() {\n  for(int p:{M1A,M1B,M2A,M2B}) pinMode(p,OUTPUT);\n  for(int p:{IRL,IRR}) pinMode(p,INPUT);\n}\nvoid loop() {\n  bool l=!digitalRead(IRL), r=!digitalRead(IRR);\n  if(l&&r) fwd();\n  else if(l) rght();\n  else if(r) left();\n  else stp();\n}"},
      {"title":"Projets Jeux & Interactifs","content":"Piano tactile, Simon Says, machine à sous LED, chrono de réaction — les projets jeux rendent l'électronique accessible à tous. Buzzer, LEDs, boutons et afficheurs créent des expériences interactives.\n\nParfait pour démonstrations et ateliers éducatifs.","code":"// Simon Says simplifié\n#include <Adafruit_NeoPixel.h>\nAdafruit_NeoPixel px(4,6,NEO_GRB+NEO_KHZ800);\nconst int BTN[]={2,3,4,5};\nconst int BUZ=8;\nuint32_t COLORS[]={0xFF0000,0x00FF00,\n                   0x0000FF,0xFFFF00};\nint seq[50], seqLen=0, score=0;\n\nvoid flash(int i) {\n  px.setPixelColor(i, COLORS[i]); px.show();\n  tone(BUZ, 440+i*100, 400); delay(600);\n  px.clear(); px.show(); noTone(BUZ); delay(200);\n}\nvoid setup() {\n  px.begin(); px.show();\n  for(int p:BTN) pinMode(p, INPUT_PULLUP);\n  pinMode(BUZ, OUTPUT);\n  randomSeed(analogRead(A0));\n}\nvoid loop() {\n  seq[seqLen++] = random(4);\n  for(int i=0;i<seqLen;i++) flash(seq[i]);\n  // ... validation saisie utilisateur\n  delay(500);\n}"}
    ],
    "quiz": [
      {"q":"Quelle résistance minimale avec une LED rouge 5mm à 5V ?","opts":["47Ω","150Ω","1kΩ","10kΩ"],"answer":1},
      {"q":"Quel protocole utilise le WS2812B (NeoPixel) ?","opts":["SPI","I2C","1 fil 800kbps","PWM classique"],"answer":2},
      {"q":"Le module relais 5V fonctionne en logique...","opts":["Actif haut (HIGH=ON)","Actif bas (LOW=ON)","PWM","Analogique"],"answer":1},
      {"q":"Quelle bibliothèque pour décoder télécommandes IR ?","opts":["IRLib2","IRremote","RadioHead","NRFLite"],"answer":1},
      {"q":"Un pont en H L298N permet de contrôler...","opts":["Servos","LEDs","Moteurs DC (direction+vitesse)","Capteurs ultrason"],"answer":2}
    ]
  }
}

COMPONENTS = [
  # ── Microcontrôleurs ──────────────────────────────────────────────────────────
  {"id":"arduino-uno","name":"Arduino Uno","category":"Microcontrôleurs","wokwi":"wokwi-arduino-uno","voltage":"5V","current":"50mA","protocol":"USB / UART","package":"DIP / THT",
   "desc":"Microcontrôleur ATmega328P 8-bit 16MHz. 14 GPIO numériques (6 PWM), 6 entrées analogiques 10-bit, 32KB Flash, 2KB SRAM, 1KB EEPROM. Connexion USB via ATmega16U2.",
   "pinout":"VIN, 5V, 3.3V, GND, D0-D13, A0-A5, SCL/SDA, MOSI/MISO/SCK/SS",
   "code":"void setup() {\n  pinMode(LED_BUILTIN, OUTPUT);\n  Serial.begin(9600);\n}\nvoid loop() {\n  digitalWrite(LED_BUILTIN, HIGH);\n  Serial.println(\"CognitoLab!\");\n  delay(1000);\n  digitalWrite(LED_BUILTIN, LOW);\n  delay(1000);\n}"},

  {"id":"arduino-nano","name":"Arduino Nano","category":"Microcontrôleurs","wokwi":"wokwi-arduino-nano","voltage":"5V","current":"40mA","protocol":"USB Mini-B","package":"DIP-30",
   "desc":"ATmega328P format compact (18×45mm). 22 GPIO, 8 entrées analogiques. Idéal breadboard. Compatibilité 100% Uno.",
   "pinout":"VIN, 5V, 3.3V, GND, D0-D13, A0-A7, AREF",
   "code":"void setup() { pinMode(13, OUTPUT); }\nvoid loop() {\n  digitalWrite(13, !digitalRead(13));\n  delay(250);\n}"},

  {"id":"arduino-mega","name":"Arduino Mega 2560","category":"Microcontrôleurs","wokwi":"wokwi-arduino-mega","voltage":"5V","current":"200mA","protocol":"USB / UART×4","package":"THT",
   "desc":"ATmega2560 8-bit 16MHz. 54 GPIO numériques (15 PWM), 16 entrées analogiques, 256KB Flash, 8KB SRAM. 4 UART hardware.",
   "pinout":"D0-D53, A0-A15, SDA/SCL, 4×UART",
   "code":"void setup() {\n  Serial.begin(9600);\n  Serial1.begin(115200); // UART1\n}\nvoid loop() {\n  if(Serial1.available())\n    Serial.write(Serial1.read());\n}"},

  {"id":"esp32","name":"ESP32 DevKit V1","category":"Microcontrôleurs","wokwi":"wokwi-esp32-devkit-v1","voltage":"3.3V","current":"250mA","protocol":"WiFi / BLE / SPI / I2C / UART","package":"Module",
   "desc":"Xtensa LX6 dual-core 240MHz. WiFi 802.11 b/g/n, Bluetooth 4.2 + BLE. 34 GPIO, 18 ADC 12-bit, 2 DAC, 4MB Flash, 520KB SRAM. Hall sensor, touch.",
   "pinout":"3V3, GND, EN, D0-D39 (dont ADC, DAC, Touch), SCL/SDA, MOSI/MISO/SCK",
   "code":"#include <WiFi.h>\nvoid setup() {\n  WiFi.begin(\"ssid\", \"password\");\n  while(WiFi.status()!=WL_CONNECTED) delay(500);\n  Serial.println(WiFi.localIP());\n}"},

  {"id":"rpi-pico","name":"Raspberry Pi Pico","category":"Microcontrôleurs","wokwi":"wokwi-pi-pico","voltage":"3.3V","current":"300mA","protocol":"USB / SPI / I2C / UART / PIO","package":"Module",
   "desc":"RP2040 dual Cortex-M0+ 133MHz. 26 GPIO multifonction, 3 ADC 12-bit, 2MB Flash, 264KB SRAM. 2 PIO programmables. MicroPython natif.",
   "pinout":"GP0-GP28, ADC0-ADC2, 3V3, VSYS, GND, RUN",
   "code":"from machine import Pin\nimport time\nled = Pin(25, Pin.OUT)\nwhile True:\n    led.toggle()\n    time.sleep(0.5)"},

  {"id":"stm32-bluepill","name":"STM32F103 Blue Pill","category":"Microcontrôleurs","wokwi":None,"voltage":"3.3V","current":"150mA","protocol":"USB / SPI×2 / I2C×2 / UART×3","package":"Module",
   "desc":"Cortex-M3 72MHz. 64KB Flash, 20KB SRAM. 37 GPIO, 10 ADC 12-bit, USB 2.0 FS. Compatible Arduino via STM32duino.",
   "pinout":"PA0-PA15, PB0-PB15, PC13-PC15, 3V3, GND, BOOT0",
   "code":"// STM32duino\nvoid setup() { pinMode(PC13, OUTPUT); }\nvoid loop() {\n  digitalWrite(PC13, LOW);  // LED on (actif bas)\n  delay(500);\n  digitalWrite(PC13, HIGH);\n  delay(500);\n}"},

  {"id":"attiny85","name":"ATtiny85","category":"Microcontrôleurs","wokwi":None,"voltage":"1.8-5.5V","current":"5mA","protocol":"SPI / I2C / UART","package":"DIP-8 / SOIC-8",
   "desc":"AVR 8-bit 20MHz. 8KB Flash, 512B SRAM, 512B EEPROM. 6 GPIO dont 4 ADC 10-bit et 2 PWM. Format ultra-compact DIP-8.",
   "pinout":"PB0-PB5, VCC, GND, RESET",
   "code":"// Programmé via Arduino ISP\nvoid setup() { pinMode(1, OUTPUT); }\nvoid loop() {\n  digitalWrite(1, HIGH); delay(1000);\n  digitalWrite(1, LOW);  delay(1000);\n}"},

  {"id":"esp8266","name":"ESP8266 NodeMCU","category":"Microcontrôleurs","wokwi":None,"voltage":"3.3V","current":"170mA","protocol":"WiFi 802.11 b/g/n / UART / SPI / I2C","package":"Module",
   "desc":"Tensilica L106 80/160MHz. WiFi intégré. 4MB Flash, 80KB SRAM. 11 GPIO dont 1 ADC 10-bit. Compatible Arduino IDE.",
   "pinout":"D0-D8, A0, 3V3, GND, EN, RST, TX, RX",
   "code":"#include <ESP8266WiFi.h>\nvoid setup() {\n  WiFi.begin(\"ssid\", \"pass\");\n}\nvoid loop() {\n  if(WiFi.status()==WL_CONNECTED)\n    Serial.println(WiFi.localIP());\n  delay(1000);\n}"},

  # ── Capteurs ──────────────────────────────────────────────────────────────────
  {"id":"dht22","name":"DHT22 (AM2302)","category":"Capteurs","wokwi":"wokwi-dht22","voltage":"3.3-5V","current":"2.5mA","protocol":"1-Wire custom","package":"TO-92 / Module",
   "desc":"Capteur numérique température & humidité. Plage : -40→+80°C (±0.5°C), 0-100%HR (±2%). Résolution 0.1. Période min 2s entre lectures.",
   "pinout":"VCC, DATA, NC, GND",
   "code":"#include <DHT.h>\n#define DHTPIN 2\n#define DHTTYPE DHT22\nDHT dht(DHTPIN, DHTTYPE);\nvoid setup() { dht.begin(); }\nvoid loop() {\n  float h = dht.readHumidity();\n  float t = dht.readTemperature();\n  Serial.printf(\"T=%.1f°C H=%.1f%%\\n\", t, h);\n  delay(2000);\n}"},

  {"id":"hcsr04","name":"HC-SR04","category":"Capteurs","wokwi":"wokwi-hc-sr04","voltage":"5V","current":"15mA","protocol":"Trigger/Echo impulsion","package":"Module",
   "desc":"Capteur ultrasonique de distance. Portée 2cm-400cm, précision ±3mm. Angle effectif 15°. Fréquence 40kHz.",
   "pinout":"VCC, Trig, Echo, GND",
   "code":"const int trig=9, echo=10;\nvoid setup() { pinMode(trig,OUTPUT); pinMode(echo,INPUT); }\nvoid loop() {\n  digitalWrite(trig,LOW); delayMicroseconds(2);\n  digitalWrite(trig,HIGH); delayMicroseconds(10);\n  digitalWrite(trig,LOW);\n  long dur=pulseIn(echo,HIGH);\n  float cm=dur*0.034/2;\n  Serial.print(cm); Serial.println(\" cm\");\n  delay(200);\n}"},

  {"id":"pir","name":"PIR HC-SR501","category":"Capteurs","wokwi":None,"voltage":"5-20V","current":"65mA","protocol":"Sortie digitale","package":"Module",
   "desc":"Capteur mouvement infrarouge passif (PIR). Détection jusqu'à 7m, angle 120°. Temps de délai et sensibilité ajustables par potentiomètre.",
   "pinout":"VCC, OUT, GND",
   "code":"const int pir = 7;\nvoid setup() { pinMode(pir, INPUT); Serial.begin(9600); }\nvoid loop() {\n  if(digitalRead(pir)==HIGH) {\n    Serial.println(\"Mouvement détecté!\");\n    delay(100);\n  }\n}"},

  {"id":"mpu6050","name":"MPU-6050","category":"Capteurs","wokwi":"wokwi-mpu6050","voltage":"3.3V","current":"3.9mA","protocol":"I2C (0x68/0x69)","package":"QFN-24 / Module",
   "desc":"Accéléromètre ±2/4/8/16g + Gyroscope ±250/500/1000/2000°/s, 6 axes. DMP intégré. Thermomètre intégré. Adresse I2C: 0x68.",
   "pinout":"VCC, GND, SCL, SDA, XDA, XCL, ADO, INT",
   "code":"#include <Wire.h>\n#include <MPU6050.h>\nMPU6050 mpu;\nvoid setup() {\n  Wire.begin(); mpu.initialize();\n}\nvoid loop() {\n  int16_t ax,ay,az,gx,gy,gz;\n  mpu.getMotion6(&ax,&ay,&az,&gx,&gy,&gz);\n  Serial.printf(\"A: %d %d %d\\n\", ax,ay,az);\n  delay(100);\n}"},

  {"id":"bmp280","name":"BMP280","category":"Capteurs","wokwi":None,"voltage":"1.8-3.6V","current":"2.7mA","protocol":"I2C / SPI","package":"LGA-8 / Module",
   "desc":"Capteur pression barométrique (300-1100 hPa ±1hPa) + température (-40→+85°C ±1°C). Altitude relative calculable. I2C 0x76 ou 0x77.",
   "pinout":"VCC, GND, SCL/SCK, SDA/SDI, CSB, SDO",
   "code":"#include <Adafruit_BMP280.h>\nAdafruit_BMP280 bmp;\nvoid setup() {\n  bmp.begin(0x76);\n}\nvoid loop() {\n  Serial.printf(\"T=%.2f°C P=%.2fhPa Alt=%.2fm\\n\",\n    bmp.readTemperature(),\n    bmp.readPressure()/100,\n    bmp.readAltitude(1013.25));\n  delay(1000);\n}"},

  {"id":"ds18b20","name":"DS18B20","category":"Capteurs","wokwi":None,"voltage":"3-5V","current":"1mA","protocol":"1-Wire","package":"TO-92 / Waterproof",
   "desc":"Thermomètre numérique précis. Plage -55→+125°C, précision ±0.5°C. Résolution 9-12 bits programmable. Plusieurs capteurs sur 1 fil.",
   "pinout":"GND, DATA, VCC",
   "code":"#include <OneWire.h>\n#include <DallasTemperature.h>\nOneWire ow(2);\nDallasTemperature dt(&ow);\nvoid setup() { dt.begin(); }\nvoid loop() {\n  dt.requestTemperatures();\n  Serial.println(dt.getTempCByIndex(0));\n  delay(1000);\n}"},

  {"id":"mq2","name":"MQ-2 (Gaz/Fumée)","category":"Capteurs","wokwi":"wokwi-gas-sensor","voltage":"5V","current":"150mA","protocol":"Analogique / Digitale","package":"Module",
   "desc":"Capteur gaz combustibles et fumée. Détecte LPG, butane, méthane, alcool, fumée. Sortie analogique (0-5V) et digitale (seuil réglable).",
   "pinout":"VCC, GND, AOUT, DOUT",
   "code":"const int apin=A0, dpin=7;\nvoid setup() { pinMode(dpin,INPUT); Serial.begin(9600); }\nvoid loop() {\n  int val=analogRead(apin);\n  bool alarm=!digitalRead(dpin);\n  Serial.printf(\"Val=%d Alarme=%d\\n\",val,alarm);\n  delay(500);\n}"},

  {"id":"ldr","name":"LDR GL5528","category":"Capteurs","wokwi":None,"voltage":"—","current":"—","protocol":"Analogique","package":"Ø5mm",
   "desc":"Photorésistance GL5528. Résistance : 1MΩ (obscurité) → 10kΩ (lumière vive). Associer à résistance 10kΩ pour diviseur de tension.",
   "pinout":"2 pattes (pas de polarité)",
   "code":"const int ldrPin = A0;\nvoid setup() { Serial.begin(9600); }\nvoid loop() {\n  int val = analogRead(ldrPin); // 0=sombre, 1023=pleine lumière\n  int lux = map(val, 0, 1023, 0, 1000);\n  Serial.print(\"Luminosité: \"); Serial.println(lux);\n  delay(200);\n}"},

  {"id":"mfrc522","name":"MFRC522 RFID","category":"Capteurs","wokwi":None,"voltage":"3.3V","current":"13-26mA","protocol":"SPI / I2C / UART","package":"Module",
   "desc":"Lecteur RFID 13.56MHz. Compatible cartes/badges Mifare (1K, 4K, Ultra). Distance lecture jusqu'à 5cm. Fréquence 13.56MHz.",
   "pinout":"3.3V, RST, GND, IRQ, MISO, MOSI, SCK, SDA(CS)",
   "code":"#include <SPI.h>\n#include <MFRC522.h>\nMFRC522 rfid(10, 9);\nvoid setup() { SPI.begin(); rfid.PCD_Init(); }\nvoid loop() {\n  if(rfid.PICC_IsNewCardPresent() &&\n     rfid.PICC_ReadCardSerial()) {\n    for(byte i=0;i<rfid.uid.size;i++)\n      Serial.printf(\"%02X \", rfid.uid.uidByte[i]);\n    Serial.println();\n  }\n}"},

  {"id":"acs712","name":"ACS712 (Courant)","category":"Capteurs","wokwi":None,"voltage":"5V","current":"10mA","protocol":"Analogique","package":"Module",
   "desc":"Capteur de courant à effet Hall. Modèles 5A, 20A, 30A. Sortie 2.5V au repos ±0.185V/A (5A), ±0.1V/A (20A), ±0.066V/A (30A).",
   "pinout":"VCC, GND, VIOUT (analogique)",
   "code":"const float SENS = 0.185; // V/A pour 5A\nvoid loop() {\n  float v = (analogRead(A0)/1023.0)*5.0;\n  float i = (v - 2.5) / SENS;\n  Serial.print(i); Serial.println(\" A\");\n  delay(100);\n}"},

  {"id":"hx711","name":"HX711 (Cellule charge)","category":"Capteurs","wokwi":None,"voltage":"2.7-5V","current":"1.5mA","protocol":"2 fils custom","package":"Module",
   "desc":"ADC 24-bit pour cellule de charge (balance). 80 SPS ou 10 SPS. Amplification ×32/64/128. Mesure jusqu'à plusieurs centaines de kg.",
   "pinout":"VCC, GND, DOUT, PD_SCK",
   "code":"#include <HX711.h>\nHX711 scale;\nvoid setup() { scale.begin(DOUT, SCK); scale.set_scale(2280); scale.tare(); }\nvoid loop() {\n  Serial.print(\"Poids: \");\n  Serial.print(scale.get_units(), 1);\n  Serial.println(\" g\");\n  delay(500);\n}"},

  {"id":"rotary-encoder","name":"Encodeur Rotatif KY-040","category":"Capteurs","wokwi":"wokwi-rotary-encoder","voltage":"5V","current":"1mA","protocol":"Quadrature + bouton","package":"Module",
   "desc":"Encodeur incrémental 20 pas/tour + bouton poussoir. Sorties A, B en quadrature. Détection sens de rotation et clic.",
   "pinout":"CLK, DT, SW, VCC, GND",
   "code":"int clk=2,dt=3,sw=4,pos=0;\nvoid setup(){\n  pinMode(clk,INPUT); pinMode(dt,INPUT);\n  attachInterrupt(digitalPinToInterrupt(clk),isr,FALLING);\n}\nvoid isr(){\n  if(digitalRead(dt)!=digitalRead(clk)) pos++; else pos--;\n}\nvoid loop(){Serial.println(pos);delay(100);}"},

  # ── Actionneurs ───────────────────────────────────────────────────────────────
  {"id":"servo-sg90","name":"Servo SG90","category":"Actionneurs","wokwi":"wokwi-servo","voltage":"4.8-6V","current":"200mA","protocol":"PWM 50Hz","package":"Module",
   "desc":"Micro-servomoteur 9g. Rotation 0-180°. Couple 1.8kg·cm à 4.8V. Signal PWM : 1ms=0°, 1.5ms=90°, 2ms=180°. Engrenages plastique.",
   "pinout":"Marron=GND, Rouge=VCC, Orange=Signal",
   "code":"#include <Servo.h>\nServo myServo;\nvoid setup() { myServo.attach(9); }\nvoid loop() {\n  for(int ang=0; ang<=180; ang+=5) {\n    myServo.write(ang);\n    delay(50);\n  }\n  for(int ang=180; ang>=0; ang-=5) {\n    myServo.write(ang);\n    delay(50);\n  }\n}"},

  {"id":"buzzer","name":"Buzzer Actif","category":"Actionneurs","wokwi":"wokwi-buzzer","voltage":"3.3-5V","current":"30mA","protocol":"Digitale / PWM","package":"Ø12mm",
   "desc":"Buzzer piézoélectrique actif 3-5V. Fréquence 2.5kHz. Niveau sonore 85dB. Version active : tonalité fixe. Version passive : fréquence variable via PWM.",
   "pinout":"+ (signal), - (GND)",
   "code":"const int bz=8;\nvoid setup(){pinMode(bz,OUTPUT);}\nvoid loop(){\n  // Bip court\n  digitalWrite(bz,HIGH); delay(100);\n  digitalWrite(bz,LOW);  delay(900);\n  // Mélodie (buzzer passif)\n  tone(bz, 440, 200); delay(300); // La\n  tone(bz, 523, 200); delay(300); // Do\n  noTone(bz);\n}"},

  {"id":"relay","name":"Module Relais 5V","category":"Actionneurs","wokwi":"wokwi-relay-module","voltage":"5V","current":"90mA","protocol":"Digitale (actif bas)","package":"Module",
   "desc":"Relais électromécanique 5V avec isolation optique. Contact NO/NC/COM. Commutation 10A/250VAC ou 10A/30VDC. LED indicateur état.",
   "pinout":"VCC, GND, IN (signal)",
   "code":"const int relay=7;\nvoid setup(){pinMode(relay,OUTPUT); digitalWrite(relay,HIGH);} // Repos=HIGH\nvoid loop(){\n  digitalWrite(relay,LOW);  // Fermer\n  delay(5000);\n  digitalWrite(relay,HIGH); // Ouvrir\n  delay(5000);\n}"},

  {"id":"motor-dc","name":"Moteur DC + L298N","category":"Actionneurs","wokwi":None,"voltage":"7-12V","current":"2A","protocol":"PWM + DIR","package":"Module + Moteur",
   "desc":"Pont en H L298N pour 2 moteurs DC jusqu'à 2A chacun. Tension moteur 5-35V. PWM pour contrôle vitesse. Direction via IN1/IN2.",
   "pinout":"ENA, IN1, IN2, IN3, IN4, ENB, 12V, GND, 5V",
   "code":"// Moteur A\nconst int ena=9, in1=8, in2=7;\nvoid setup(){pinMode(ena,OUTPUT); pinMode(in1,OUTPUT); pinMode(in2,OUTPUT);}\nvoid loop(){\n  // Avant 50%\n  analogWrite(ena,128); digitalWrite(in1,HIGH); digitalWrite(in2,LOW);\n  delay(2000);\n  // Stop\n  analogWrite(ena,0); delay(500);\n  // Arrière 75%\n  analogWrite(ena,192); digitalWrite(in1,LOW); digitalWrite(in2,HIGH);\n  delay(2000);\n}"},

  {"id":"stepper-28byj48","name":"Stepper 28BYJ-48 + ULN2003","category":"Actionneurs","wokwi":None,"voltage":"5V","current":"150mA","protocol":"4 fils séquence","package":"Module + Moteur",
   "desc":"Moteur pas à pas 5V 4096 pas/tour (mode demi-pas). Couple 34.3 mN·m. Vitesse max ~15 rpm. Driver ULN2003 intégré avec LEDs indicatrices.",
   "pinout":"IN1, IN2, IN3, IN4, VCC, GND",
   "code":"#include <Stepper.h>\nStepper myStepper(2048, 8,10,9,11);\nvoid setup(){ myStepper.setSpeed(10); }\nvoid loop(){\n  myStepper.step(2048);  // 1 tour\n  delay(500);\n  myStepper.step(-2048); // Retour\n  delay(500);\n}"},

  # ── Affichage ─────────────────────────────────────────────────────────────────
  {"id":"led-red","name":"LED 5mm Rouge","category":"Affichage","wokwi":"wokwi-led","voltage":"2V","current":"20mA","protocol":"Digitale","package":"Ø5mm",
   "desc":"LED rouge diffuse 5mm. Tension directe 2V, courant max 30mA. Intensité lumineuse typique 2000mcd. Ajouter résistance 220Ω avec 5V.",
   "pinout":"Anode (+, patte longue), Cathode (-, patte courte)",
   "code":"// Toujours mettre une résistance série !\n// R = (Vcc - Vled) / Iled = (5 - 2) / 0.02 = 150Ω minimum\nconst int LED = 13;\nvoid setup(){pinMode(LED, OUTPUT);}\nvoid loop(){digitalWrite(LED,HIGH);delay(500);digitalWrite(LED,LOW);delay(500);}"},

  {"id":"led-rgb","name":"LED RGB","category":"Affichage","wokwi":"wokwi-rgb-led","voltage":"2-3.3V","current":"20mA/canal","protocol":"PWM (3 canaux)","package":"Ø5mm / CMS",
   "desc":"LED tricolore cathode commune (ou anode commune). 3 canaux indépendants R/G/B. 16 millions de couleurs avec PWM 8-bit.",
   "pinout":"R, GND (commun), G, B",
   "code":"const int R=9, G=10, B=11;\nvoid setup(){pinMode(R,OUTPUT);pinMode(G,OUTPUT);pinMode(B,OUTPUT);}\nvoid loop(){\n  // Rouge\n  analogWrite(R,255);analogWrite(G,0);analogWrite(B,0);delay(500);\n  // Vert\n  analogWrite(R,0);analogWrite(G,255);analogWrite(B,0);delay(500);\n  // Bleu\n  analogWrite(R,0);analogWrite(G,0);analogWrite(B,255);delay(500);\n  // Blanc\n  analogWrite(R,255);analogWrite(G,255);analogWrite(B,255);delay(500);\n}"},

  {"id":"neopixel","name":"NeoPixel WS2812B","category":"Affichage","wokwi":"wokwi-neopixel","voltage":"5V","current":"60mA/LED","protocol":"1 fil 800kbps","package":"CMS / Anneau / Bande",
   "desc":"LED RGB adressable WS2812B. Contrôleur intégré. Chaînable : 1 seul fil de données pour N LEDs. Intensité et couleur programmables indépendamment.",
   "pinout":"5V, GND, DIN → DOUT (chaîne)",
   "code":"#include <Adafruit_NeoPixel.h>\n#define PIN 6\n#define NLEDS 8\nAdafruit_NeoPixel strip(NLEDS, PIN, NEO_GRB+NEO_KHZ800);\nvoid setup(){strip.begin(); strip.show();}\nvoid loop(){\n  for(int i=0;i<NLEDS;i++){\n    strip.setPixelColor(i, strip.Color(255,0,128));\n    strip.show(); delay(100);\n  }\n  strip.clear(); strip.show(); delay(500);\n}"},

  {"id":"led-bar","name":"Barre LEDs 10 segments","category":"Affichage","wokwi":"wokwi-led-bar-graph","voltage":"2V","current":"20mA/segment","protocol":"10 broches digitales","package":"SIL-20",
   "desc":"Barre de 10 LEDs rouges/vertes/jaunes. Affichage de niveau (batterie, son, VU-mètre). Compatible avec shift register 74HC595.",
   "pinout":"10 anodes + 10 cathodes",
   "code":"// Bargraph de niveau\nconst int LEDS=10;\nint pins[]={2,3,4,5,6,7,8,9,10,11};\nvoid setup(){for(int i=0;i<LEDS;i++) pinMode(pins[i],OUTPUT);}\nvoid showLevel(int level){ // 0-10\n  for(int i=0;i<LEDS;i++)\n    digitalWrite(pins[i], i<level ? HIGH : LOW);\n}\nvoid loop(){for(int i=0;i<=10;i++){showLevel(i);delay(100);}}"},

  {"id":"oled-ssd1306","name":"OLED 0.96\" SSD1306","category":"Affichage","wokwi":"wokwi-ssd1306","voltage":"3.3V","current":"20mA","protocol":"I2C (0x3C) / SPI","package":"Module",
   "desc":"Écran OLED 128×64 pixels monochrome. Angle de vue 160°. Pas de rétroéclairage, excellent contraste. Bibliothèque Adafruit ou U8g2.",
   "pinout":"VCC, GND, SCL, SDA",
   "code":"#include <Adafruit_GFX.h>\n#include <Adafruit_SSD1306.h>\nAdafruit_SSD1306 display(128, 64, &Wire, -1);\nvoid setup(){\n  display.begin(SSD1306_SWITCHCAPVCC, 0x3C);\n  display.clearDisplay();\n  display.setTextColor(WHITE);\n  display.setTextSize(2);\n  display.setCursor(0,0);\n  display.println(\"CognitoLab\");\n  display.display();\n}"},

  {"id":"lcd1602","name":"LCD 16×2 + I2C","category":"Affichage","wokwi":"wokwi-lcd1602","voltage":"5V","current":"200mA","protocol":"I2C via PCF8574 (0x27)","package":"Module",
   "desc":"Afficheur LCD HD44780 16 colonnes × 2 lignes. Module I2C PCF8574 réduit à 4 fils. Rétroéclairage LED bleu ou vert. Contraste réglable.",
   "pinout":"VCC, GND, SDA, SCL",
   "code":"#include <LiquidCrystal_I2C.h>\nLiquidCrystal_I2C lcd(0x27, 16, 2);\nvoid setup(){\n  lcd.init();\n  lcd.backlight();\n  lcd.setCursor(0, 0);\n  lcd.print(\"CognitoLab\");\n  lcd.setCursor(0, 1);\n  lcd.print(\"v2.0 - IA Ready\");\n}"},

  {"id":"7seg","name":"Afficheur 7 segments","category":"Affichage","wokwi":"wokwi-7segment","voltage":"2V","current":"20mA/segment","protocol":"7 broches digitales","package":"0.56\" / 0.36\"",
   "desc":"Afficheur 7 segments + point décimal. Cathode commune ou anode commune. 8 segments (a,b,c,d,e,f,g,dp). Typiquement utilisé avec 74HC595.",
   "pinout":"a,b,c,d,e,f,g,dp + COM",
   "code":"// Via 74HC595\n#include <ShiftRegister74HC595.h>\nShiftRegister74HC595<1> sr(data,clock,latch);\nconst byte digits[]={0x3F,0x06,0x5B,0x4F,0x66,0x6D,0x7D,0x07,0x7F,0x6F};\nvoid loop(){for(int i=0;i<10;i++){sr.set(digits[i]);delay(500);}}"},

  {"id":"tm1637","name":"TM1637 4 digits","category":"Affichage","wokwi":"wokwi-tm1637-7segment","voltage":"3.3-5V","current":"80mA","protocol":"2 fils CLK/DIO","package":"Module",
   "desc":"Afficheur 7 segments 4 digits + 2 points. Contrôleur TM1637 intégré. Interface 2 fils simplifiée. Luminosité 8 niveaux. Idéal horloge/chrono.",
   "pinout":"CLK, DIO, VCC, GND",
   "code":"#include <TM1637Display.h>\nTM1637Display disp(CLK, DIO);\nvoid setup(){disp.setBrightness(5);}\nvoid loop(){\n  int h=12, m=30;\n  disp.showNumberDecEx(h*100+m, 0b01000000, true); // 12:30\n  delay(1000);\n}"},

  # ── Communication ─────────────────────────────────────────────────────────────
  {"id":"hc05","name":"HC-05 Bluetooth","category":"Communication","wokwi":None,"voltage":"3.3-5V","current":"40mA","protocol":"UART / SPP Bluetooth 2.0","package":"Module",
   "desc":"Module Bluetooth classique SPP. Maître ou Esclave configurable. Portée 10m. Vitesse UART jusqu'à 1382400 baud. AT commands.",
   "pinout":"VCC, GND, TXD, RXD, EN, STATE",
   "code":"// Remplace Serial par Bluetooth\nvoid setup(){\n  Serial.begin(9600); // Communication USB\n  Serial1.begin(9600); // HC-05 sur UART1\n}\nvoid loop(){\n  if(Serial1.available())\n    Serial.write(Serial1.read());\n  if(Serial.available())\n    Serial1.write(Serial.read());\n}"},

  {"id":"nrf24","name":"nRF24L01+","category":"Communication","wokwi":"wokwi-nrf24l01","voltage":"1.9-3.6V","current":"11.3mA RX","protocol":"SPI + 2.4GHz radio","package":"Module 8 pins",
   "desc":"Transceiver radio 2.4GHz. 125 canaux. Vitesse 250kbps/1Mbps/2Mbps. Portée 100m (antenne PCB), 1km (antenne externe). Protocole ShockBurst.",
   "pinout":"GND, VCC, CE, CSN, SCK, MOSI, MISO, IRQ",
   "code":"#include <RF24.h>\nRF24 radio(9, 10);\nconst byte addr[]=\"00001\";\nvoid setup(){\n  radio.begin();\n  radio.openWritingPipe(addr);\n  radio.setPALevel(RF24_PA_LOW);\n  radio.stopListening();\n}\nvoid loop(){\n  const char txt[]=\"CognitoLab\";\n  radio.write(&txt, sizeof(txt));\n  delay(1000);\n}"},

  {"id":"lora","name":"LoRa SX1276","category":"Communication","wokwi":None,"voltage":"3.3V","current":"120mA TX","protocol":"SPI + LoRa 868/915MHz","package":"Module",
   "desc":"Transceiver LoRa longue portée (jusqu'à 15km en espace libre). 868MHz (Europe) / 915MHz (USA). Spreading Factor 6-12. Excellent en IoT faible consommation.",
   "pinout":"VCC, GND, SCK, MISO, MOSI, NSS, RESET, DIO0",
   "code":"#include <LoRa.h>\nvoid setup(){\n  LoRa.begin(868E6); // 868MHz\n}\nvoid loop(){\n  LoRa.beginPacket();\n  LoRa.print(\"Hello LoRa!\");\n  LoRa.endPacket();\n  delay(5000);\n}"},

  {"id":"ir-receiver","name":"Récepteur IR 1838T","category":"Communication","wokwi":"wokwi-ir-receiver","voltage":"3.3-5V","current":"1mA","protocol":"NEC / RC5 / Sony IR","package":"TO-92 / Module",
   "desc":"Photorécepteur infrarouge 38kHz. Décode télécommandes NEC, RC5, Sony. Intégré avec démodulateur et amplificateur.",
   "pinout":"OUT, GND, VCC",
   "code":"#include <IRremote.h>\nIRrecv receiver(7);\nvoid setup(){receiver.enableIRIn();}\nvoid loop(){\n  if(receiver.decode()){\n    Serial.println(receiver.decodedIRData.decodedRawData, HEX);\n    receiver.resume();\n  }\n}"},

  {"id":"keypad","name":"Clavier 4×4","category":"Communication","wokwi":"wokwi-membrane-keypad","voltage":"5V","current":"1mA","protocol":"Matrix 8 fils","package":"Membrane",
   "desc":"Clavier matriciel 4×4 membranaire. 16 touches (0-9, A-D, *, #). Interface 8 fils (4 lignes + 4 colonnes). Scan matriciel polling ou interruption.",
   "pinout":"R1,R2,R3,R4 (lignes) + C1,C2,C3,C4 (colonnes)",
   "code":"#include <Keypad.h>\nconst byte ROWS=4, COLS=4;\nchar keys[4][4]={{'1','2','3','A'},{'4','5','6','B'},\n                 {'7','8','9','C'},{'*','0','#','D'}};\nbyte rPins[]={9,8,7,6}, cPins[]={5,4,3,2};\nKeypad kp=Keypad(makeKeymap(keys),rPins,cPins,ROWS,COLS);\nvoid loop(){char k=kp.getKey();if(k) Serial.println(k);}"},

  # ── Passifs ───────────────────────────────────────────────────────────────────
  {"id":"resistor","name":"Résistance","category":"Passifs","wokwi":"wokwi-resistor","voltage":"—","current":"—","protocol":"—","package":"0207 / 0805 / 0603",
   "desc":"Composant passif limitant le courant. Loi d'Ohm : V=R×I. Code couleur 4 bandes. Séries E12/E24. Valeurs : 1Ω à 10MΩ. Puissance 1/4W typique.",
   "pinout":"2 bornes (pas de polarité)",
   "code":"// Calcul résistance LED\n// R = (Vcc - Vled) / Iled\n// LED rouge 5V : R = (5 - 2) / 0.020 = 150Ω → choisir 220Ω\n\n// Diviseur de tension\n// Vout = Vcc × R2 / (R1 + R2)\n// Ex: 5V → 3.3V avec R1=1kΩ, R2=2kΩ"},

  {"id":"potentiometer","name":"Potentiomètre 10kΩ","category":"Passifs","wokwi":"wokwi-potentiometer","voltage":"—","current":"—","protocol":"Analogique","package":"9mm / 16mm",
   "desc":"Résistance variable 3 bornes. Valeurs 100Ω à 1MΩ. Type linéaire (B) ou logarithmique (A audio). Utilisé pour diviseur de tension réglable.",
   "pinout":"1=GND, 2=curseur (OUT), 3=VCC",
   "code":"void loop(){\n  int val = analogRead(A0); // 0-1023\n  float voltage = val * (5.0 / 1023.0);\n  int angle = map(val, 0, 1023, 0, 180);\n  Serial.printf(\"Val=%d V=%.2fV Angle=%d°\\n\",val,voltage,angle);\n  delay(100);\n}"},

  {"id":"cap-electro","name":"Condensateur Électrolytique","category":"Passifs","wokwi":None,"voltage":"6.3-450V","current":"—","protocol":"—","package":"Cylindrique",
   "desc":"Condensateur polarisé. Capacités 1µF-10000µF. Filtrage alimentation, découplage. ATTENTION à la polarité ! Bande blanche = borne négative.",
   "pinout":"+ (patte longue), - (bande blanche, patte courte)",
   "code":"// Filtre RC passe-bas\n// fc = 1 / (2π × R × C)\n// Ex: R=10kΩ, C=100µF → fc=0.16Hz (filtrage lent)\n\n// Énergie stockée :\n// E = 0.5 × C × V²\n// Ex: 1000µF à 5V → E = 0.0125 Joules"},

  {"id":"cap-ceram","name":"Condensateur Céramique","category":"Passifs","wokwi":None,"voltage":"50V","current":"—","protocol":"—","package":"0805 / 0402 / Disque",
   "desc":"Condensateur non-polarisé. Capacités 1pF-100nF typique. Découplage haute fréquence, filtrage HF. Mettre 100nF près de chaque CI.",
   "pinout":"2 bornes (pas de polarité)",
   "code":"// Découplage alimentation (indispensable !)\n// Placer 100nF entre VCC et GND de chaque CI\n// + 10µF électrolytique en parallèle\n\n// Filtre RC HF :\n// R=100Ω, C=100nF → fc=15.9kHz"},

  {"id":"inductor","name":"Inductance","category":"Passifs","wokwi":None,"voltage":"—","current":"—","protocol":"—","package":"Toroïde / Axiale",
   "desc":"Composant inductif stockant l'énergie magnétique. Valeurs 1µH-100mH. Utilisé dans filtres LC, convertisseurs DC-DC (boost/buck), antennes.",
   "pinout":"2 bornes",
   "code":"// Fréquence de résonance LC :\n// f = 1 / (2π × √(L×C))\n// Ex: L=100µH, C=100nF → f=50.3kHz\n\n// Convertisseur boost (MT3608) :\n// L=22µH typique pour sortie 5V→12V"},

  {"id":"transistor-npn","name":"Transistor NPN 2N2222","category":"Passifs","wokwi":None,"voltage":"30V max","current":"600mA max","protocol":"Analogique / Commutation","package":"TO-92",
   "desc":"Transistor NPN bipolaire. Gain β=75-300. Ic max 600mA. Vceo 40V. Excellent pour commutation de charges et étages amplificateurs.",
   "pinout":"E (émetteur), B (base), C (collecteur)",
   "code":"// Commutation d'une charge (LED, relais...)\n// R_base = (Vcc - 0.7) / Ib = (5-0.7) / (Ic/β)\n// Ex: LED 20mA, β=100 → Ib=0.2mA → R=21kΩ → choisir 10kΩ\nconst int base=7;\nvoid setup(){pinMode(base,OUTPUT);}\nvoid loop(){\n  digitalWrite(base,HIGH); delay(1000); // ON\n  digitalWrite(base,LOW);  delay(1000); // OFF\n}"},

  {"id":"mosfet","name":"MOSFET N-ch IRLZ44N","category":"Passifs","wokwi":None,"voltage":"55V max","current":"47A max","protocol":"PWM / Digitale","package":"TO-220",
   "desc":"MOSFET logic-level N-canal. Vgs_th = 1-2V (commandable avec 3.3V/5V). Rds_on = 22mΩ. Idéal pour commuter moteurs, strips LED, charges 12V.",
   "pinout":"G (grille), D (drain), S (source)",
   "code":"// Contrôle strip LED 12V via Arduino 5V\nconst int gate=9;\nvoid setup(){pinMode(gate,OUTPUT);}\nvoid loop(){\n  // Allumage progressif\n  for(int i=0;i<=255;i++){\n    analogWrite(gate,i);\n    delay(10);\n  }\n}"},

  {"id":"diode-1n4007","name":"Diode 1N4007","category":"Passifs","wokwi":None,"voltage":"1000V PIV","current":"1A max","protocol":"—","package":"DO-41",
   "desc":"Diode redresseuse silicium. Tension inverse 1000V, courant 1A. Tension directe 0.7V. Utilisée pour protection anti-retour et redressement.",
   "pinout":"Anode (A), Cathode (K, bande)",
   "code":"// Protection anti-retour alimentation\n// Toujours en série côté + entre source et circuit\n\n// Diode roue libre (protection moteur/relais) :\n// Placer en anti-parallèle sur la bobine\n// Anode → GND, Cathode → alimentation bobine"},

  {"id":"zener","name":"Diode Zener BZX55C5V1","category":"Passifs","wokwi":None,"voltage":"5.1V Zener","current":"5-500mA","protocol":"—","package":"DO-35",
   "desc":"Diode Zener 5.1V. Régulation tension de référence. En inverse, maintient Vz aux bornes. Valeurs courantes : 3.3V, 5.1V, 6.2V, 9.1V, 12V.",
   "pinout":"Anode (A), Cathode (K, bande)",
   "code":"// Régulateur simple avec Zener 5.1V\n// R_série = (Vin - Vz) / (Iz + Icharge)\n// Ex: 12V→5.1V, charge 10mA : R=(12-5.1)/(0.01+0.005)=460Ω → 470Ω"},

  {"id":"lm7805","name":"Régulateur LM7805","category":"Alimentation","wokwi":None,"voltage":"7-35V → 5V","current":"1.5A max","protocol":"—","package":"TO-220",
   "desc":"Régulateur linéaire +5V fixe. Entrée 7-35V. Sortie 5V ±4%. Courant 1.5A. Protection thermique et court-circuit intégrée. Ajouter condensateurs.",
   "pinout":"IN, GND, OUT",
   "code":"// Schéma typique LM7805\n// IN: condensateur 0.33µF vers GND\n// OUT: condensateur 0.1µF vers GND\n// Dissipation : P = (Vin-5) × I\n// Ex: 12V, 500mA → P=3.5W → dissipateur requis"},

  {"id":"ams1117","name":"Régulateur AMS1117 3.3V","category":"Alimentation","wokwi":None,"voltage":"4.75-12V → 3.3V","current":"800mA max","protocol":"—","package":"SOT-223 / TO-252",
   "desc":"Régulateur LDO 3.3V. Chute de tension minimale 1.3V max. 800mA. Utilisé sur la plupart des modules ESP32, ESP8266, RPi Pico. Protection thermique.",
   "pinout":"GND, OUT, IN",
   "code":"// Tension d'entrée minimale : 3.3 + 1.3 = 4.6V\n// Condensateur entrée : 10µF + 0.1µF\n// Condensateur sortie : 22µF + 0.1µF\n// Dissipation : P = (Vin - 3.3) × I"},
]

BOARDS = [
    {"id":"arduino-uno","label":"Arduino Uno","icon":"🔵","desc":"ATmega328P · 14 I/O"},
    {"id":"arduino-nano","label":"Arduino Nano","icon":"🔷","desc":"ATmega328P · compact"},
    {"id":"arduino-mega","label":"Arduino Mega","icon":"💠","desc":"ATmega2560 · 54 I/O"},
    {"id":"esp32","label":"ESP32","icon":"📡","desc":"WiFi/BT · dual-core"},
    {"id":"stm32f103","label":"STM32 Blue Pill","icon":"🟣","desc":"Cortex-M3 · 72MHz"},
    {"id":"rp2040","label":"RP2040","icon":"🟢","desc":"Dual Cortex-M0+ · 133MHz"},
    {"id":"pico","label":"Raspberry Pico","icon":"🟡","desc":"MicroPython"},
]

# ── Page routes ────────────────────────────────────────────────────────────────
def safe_db(fn, default):
    """Execute a DB query, return default on any error."""
    try:
        return fn()
    except Exception as e:
        app.logger.warning(f"DB query skipped: {e}")
        return default

@app.route("/")
def dashboard():
    projects_count  = safe_db(lambda: Project.query.count(), 0)
    posts_count     = safe_db(lambda: CommunityPost.query.count(), 0)
    progresses      = safe_db(lambda: {p.course_id: p.progress for p in CourseProgress.query.all()}, {})
    recent_projects = safe_db(lambda: Project.query.order_by(Project.created_at.desc()).limit(3).all(), [])
    return render_template("dashboard.html",
        projects_count=projects_count,
        posts_count=posts_count,
        progresses=progresses,
        recent_projects=recent_projects,
        courses=COURSES[:3])

RENODE_SCRIPTS = {
    "stm32f103": """\
# Renode script — STM32F103 (Blue Pill)
using sysbus
mach create "stm32f103"
machine LoadPlatformDescription @platforms/boards/stm32f103c8.repl

# Charger votre firmware compilé (.elf)
sysbus LoadELF @firmware.elf

# UART → console
showAnalyzer sysbus.usart1

# Démarrer
start""",
    "rp2040": """\
# Renode script — RP2040 (Raspberry Pi Pico)
using sysbus
mach create "rp2040"
machine LoadPlatformDescription @platforms/boards/rp2040.repl

# Charger votre firmware (.elf)
sysbus LoadELF @firmware.elf

# UART0 → console
showAnalyzer sysbus.uart0

start""",
    "pico": """\
# Renode script — Raspberry Pi Pico (RP2040)
using sysbus
mach create "pico"
machine LoadPlatformDescription @platforms/boards/rp2040.repl

sysbus LoadELF @firmware.elf
showAnalyzer sysbus.uart0
start""",
    "raspberry-pi": """\
# Renode ne simule pas Raspberry Pi OS complet.
# Utilisez QEMU pour émuler le Raspberry Pi :
#
#   qemu-system-aarch64 \\
#     -M raspi3b \\
#     -kernel kernel8.img \\
#     -drive file=raspi.img,format=raw \\
#     -serial stdio
#
# Téléchargez QEMU : https://www.qemu.org/download/""",
}

DEFAULT_RENODE_SCRIPT = """\
# Renode script générique
using sysbus
mach create "{board}"
# machine LoadPlatformDescription @platforms/boards/VOTRE_CARTE.repl

# Chargez votre firmware compilé :
# sysbus LoadELF @firmware.elf

# Consultez : https://renode.readthedocs.io/en/latest/basic/machines.html
start"""

@app.route("/simulator")
def simulator():
    board = request.args.get("board", "arduino-uno")
    script = RENODE_SCRIPTS.get(board, DEFAULT_RENODE_SCRIPT.format(board=board))
    return render_template("simulator.html", boards=BOARDS, selected_board=board, renode_script=script)

@app.route("/courses")
def courses():
    progresses = safe_db(lambda: {p.course_id: p.progress for p in CourseProgress.query.all()}, {})
    return render_template("courses.html", courses=COURSES, progresses=progresses)

@app.route("/courses/<course_id>")
def course_detail(course_id):
    course = next((c for c in COURSES if c["id"] == course_id), None)
    if not course:
        return redirect(url_for("courses"))
    content = COURSE_CONTENT.get(course_id, {"sections": [], "quiz": []})
    progress_obj = safe_db(lambda: CourseProgress.query.filter_by(course_id=course_id).first(), None)
    progress = progress_obj.progress if progress_obj else 0
    tab = request.args.get("tab", "cours")
    section_idx = int(request.args.get("s", 0))
    section_idx = max(0, min(section_idx, len(content["sections"]) - 1)) if content["sections"] else 0
    return render_template("course_detail.html",
        course=course, content=content, progress=progress,
        tab=tab, section_idx=section_idx)

@app.route("/components")
def components():
    cat    = request.args.get("cat", "Tous")
    search = request.args.get("q", "").lower()
    categories = ["Tous", "Microcontrôleurs", "Capteurs", "Actionneurs", "Affichage", "Communication", "Passifs", "Alimentation"]
    filtered = COMPONENTS if cat == "Tous" else [c for c in COMPONENTS if c["category"] == cat]
    if search:
        filtered = [c for c in filtered if search in c["name"].lower() or search in c["desc"].lower()]
    comp_id  = request.args.get("comp", None)
    selected = next((c for c in COMPONENTS if c["id"] == comp_id), None)
    return render_template("components.html",
        components=filtered, categories=categories,
        selected_cat=cat, selected_comp=selected,
        search=search, total=len(COMPONENTS))

@app.route("/projects")
def projects():
    all_projects = safe_db(lambda: Project.query.order_by(Project.created_at.desc()).all(), [])
    return render_template("projects.html", projects=all_projects, boards=BOARDS)

@app.route("/community")
def community():
    board_filter = request.args.get("board", "Tous")
    search = request.args.get("q", "")
    def get_posts():
        q = CommunityPost.query
        if board_filter != "Tous":
            q = q.filter(CommunityPost.board == board_filter)
        if search:
            q = q.filter(
                CommunityPost.title.ilike(f"%{search}%") |
                CommunityPost.description.ilike(f"%{search}%")
            )
        return q.order_by(CommunityPost.created_at.desc()).all()
    posts = safe_db(get_posts, [])
    boards = ["Tous", "Arduino", "ESP32", "Raspberry Pi", "STM32", "RP2040"]
    return render_template("community.html",
        posts=posts, boards=boards, board_filter=board_filter, search=search)

@app.route("/about")
def about():
    return render_template("about.html")

# ── API routes ─────────────────────────────────────────────────────────────────
@app.route("/api/ai/assist", methods=["POST"])
def ai_assist():
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    if not anthropic_key:
        return jsonify({"error": "ANTHROPIC_API_KEY manquant"}), 500

    data   = request.get_json() or {}
    prompt = data.get("prompt", "").strip()
    board  = data.get("board", "général")
    if not prompt:
        return jsonify({"error": "prompt requis"}), 400

    system_prompt = (
        "Tu es Cognito, l'assistant IA expert de CognitoLab — une plateforme d'électronique, "
        "microcontrôleurs et programmation embarquée. Tu aides les utilisateurs à concevoir des circuits, "
        "programmer des microcontrôleurs (Arduino, ESP32, Raspberry Pi, STM32, RP2040, ROS) et comprendre "
        "les composants électroniques. Réponds en français, de manière claire et pédagogique. "
        "Inclus du code si pertinent, bien formaté. Sois enthousiaste et encourageant."
    )
    user_content = f"Carte/plateforme: {board}\n\n{prompt}" if board != "général" else prompt

    try:
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": anthropic_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            json={
                "model": "claude-opus-4-5",
                "max_tokens": 1024,
                "system": system_prompt,
                "messages": [{"role": "user", "content": user_content}],
            },
            timeout=30,
        )
        resp.raise_for_status()
        answer = resp.json()["content"][0]["text"]
        return jsonify({"answer": answer})
    except Exception as e:
        return jsonify({"error": str(e)}), 502

@app.route("/api/projects", methods=["GET"])
def api_projects():
    try:
        return jsonify([p.to_dict() for p in Project.query.order_by(Project.created_at.desc()).all()])
    except Exception as e:
        return jsonify({"error": str(e)}), 503

@app.route("/api/projects", methods=["POST"])
def api_create_project():
    try:
        data = request.get_json() or {}
        p = Project(
            title=data.get("title", "Nouveau projet"),
            board=data.get("board", "arduino-uno"),
            code=data.get("code", ""),
            status="draft",
        )
        db.session.add(p)
        db.session.commit()
        return jsonify(p.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 503

@app.route("/api/projects/<int:pid>", methods=["PUT"])
def api_update_project(pid):
    try:
        p = Project.query.get_or_404(pid)
        data = request.get_json() or {}
        p.title  = data.get("title", p.title)
        p.board  = data.get("board", p.board)
        p.code   = data.get("code", p.code)
        p.status = data.get("status", p.status)
        db.session.commit()
        return jsonify(p.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 503

@app.route("/api/projects/<int:pid>", methods=["DELETE"])
def api_delete_project(pid):
    try:
        p = Project.query.get_or_404(pid)
        db.session.delete(p)
        db.session.commit()
        return jsonify({"ok": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 503

@app.route("/api/community/posts", methods=["POST"])
def api_create_post():
    try:
        data = request.get_json() or {}
        author = data.get("author", "Anonyme")
        initials = "".join(w[0].upper() for w in author.split()[:2]) or "AN"
        # accept both 'content' and 'description' from frontend
        description = data.get("content") or data.get("description", "")
        post = CommunityPost(
            author=author,
            avatar=initials,
            title=data.get("title", ""),
            description=description,
            board=data.get("board", "Arduino"),
            tags=",".join(data.get("tags", [])),
        )
        db.session.add(post)
        db.session.commit()
        return jsonify(post.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 503

@app.route("/api/community/posts/<int:pid>/like", methods=["POST"])
def api_like_post(pid):
    try:
        post = CommunityPost.query.get_or_404(pid)
        post.likes += 1
        db.session.commit()
        return jsonify({"likes": post.likes})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 503

@app.route("/api/courses/<course_id>/progress", methods=["POST"])
def api_update_progress(course_id):
    try:
        data = request.get_json() or {}
        prog = CourseProgress.query.filter_by(course_id=course_id).first()
        if not prog:
            prog = CourseProgress(course_id=course_id, progress=0)
            db.session.add(prog)
        prog.progress = min(100, max(0, data.get("progress", prog.progress)))
        db.session.commit()
        return jsonify({"course_id": course_id, "progress": prog.progress})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 503

# ── Arduino Compilation API ────────────────────────────────────────────────────
@app.route("/api/compile/arduino", methods=["POST"])
def compile_arduino():
    import tempfile, subprocess, glob
    data = request.get_json() or {}
    code = data.get("code", "").strip()
    fqbn = data.get("fqbn", "arduino:avr:uno")

    if not code:
        return jsonify({"error": "Code vide"}), 400

    # Whitelist FQBN
    allowed = {"arduino:avr:uno", "arduino:avr:nano", "arduino:avr:mega"}
    if fqbn not in allowed:
        return jsonify({"error": f"FQBN non supporté: {fqbn}"}), 400

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            sketch_dir = os.path.join(tmpdir, "sketch")
            os.makedirs(sketch_dir)
            with open(os.path.join(sketch_dir, "sketch.ino"), "w") as f:
                f.write(code)

            result = subprocess.run(
                ["arduino-cli", "compile", "--fqbn", fqbn,
                 "--output-dir", tmpdir, sketch_dir],
                capture_output=True, text=True, timeout=120
            )

            if result.returncode != 0:
                err = result.stderr or result.stdout or "Erreur inconnue"
                # Nettoyer le chemin tmp du message d'erreur
                err = err.replace(tmpdir, "sketch")
                return jsonify({"error": err}), 400

            hex_files = glob.glob(os.path.join(tmpdir, "*.hex"))
            if not hex_files:
                return jsonify({"error": "Aucun fichier .hex produit"}), 500

            with open(hex_files[0], "r") as f:
                hex_content = f.read()

            return jsonify({"hex": hex_content, "fqbn": fqbn})

    except subprocess.TimeoutExpired:
        return jsonify({"error": "Compilation timeout (>120s)"}), 504
    except FileNotFoundError:
        return jsonify({"error": "Arduino CLI non disponible dans ce conteneur"}), 503
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ── Simulation API ─────────────────────────────────────────────────────────────
@app.route("/api/simulate/start", methods=["POST"])
def api_sim_start():
    data     = request.get_json() or {}
    board    = data.get("board", "stm32f103")
    firmware = data.get("firmware_path")  # optionnel, chemin local après upload
    session_id, error = sim_manager.start(board, firmware)
    if error:
        return jsonify({"error": error}), 503
    return jsonify({"session_id": session_id, "board": board})

@app.route("/api/simulate/stream/<session_id>")
def api_sim_stream(session_id):
    def generate():
        yield from sim_manager.stream(session_id)
    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control":     "no-cache",
            "X-Accel-Buffering": "no",   # désactive le buffering Nginx/Railway
            "Connection":        "keep-alive",
        },
    )

@app.route("/api/simulate/stop/<session_id>", methods=["POST"])
def api_sim_stop(session_id):
    sim_manager.stop(session_id)
    return jsonify({"ok": True})

@app.route("/api/simulate/upload", methods=["POST"])
def api_sim_upload():
    if "firmware" not in request.files:
        return jsonify({"error": "Champ 'firmware' manquant"}), 400
    f = request.files["firmware"]
    if not f.filename.lower().endswith(".elf"):
        return jsonify({"error": "Seuls les fichiers .elf sont acceptés"}), 400
    safe_name = f"fw_{uuid.uuid4().hex[:8]}.elf"
    path = os.path.join(tempfile.gettempdir(), safe_name)
    f.save(path)
    return jsonify({"firmware_path": path, "filename": f.filename})

@app.route("/api/simulate/status")
def api_sim_status():
    return jsonify(sim_manager.status())

# ── Run ────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
