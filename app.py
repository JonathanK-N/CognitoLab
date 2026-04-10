import os
import requests
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for
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

COMPONENTS = [
    {"id":"arduino-uno","name":"Arduino Uno","category":"Microcontrôleurs","icon":"🔵","voltage":"5V","desc":"ATmega328P, 14 broches numériques, 6 analogiques, USB","code":"// Blink\nvoid setup() { pinMode(13, OUTPUT); }\nvoid loop() { digitalWrite(13, HIGH); delay(500); digitalWrite(13, LOW); delay(500); }"},
    {"id":"esp32","name":"ESP32","category":"Microcontrôleurs","icon":"📡","voltage":"3.3V","desc":"Xtensa LX6 dual-core, WiFi 802.11b/g/n, Bluetooth 4.2","code":"#include <WiFi.h>\nWiFi.begin(\"ssid\", \"password\");"},
    {"id":"rpi-pico","name":"Raspberry Pi Pico","category":"Microcontrôleurs","icon":"🟡","voltage":"3.3V","desc":"RP2040, Cortex-M0+ 133MHz, 26 GPIO multifonction","code":"from machine import Pin\nled = Pin(25, Pin.OUT)\nled.toggle()"},
    {"id":"stm32","name":"STM32 Blue Pill","category":"Microcontrôleurs","icon":"💜","voltage":"3.3V","desc":"Cortex-M3 72MHz, 20KB RAM, 64KB Flash","code":"HAL_GPIO_TogglePin(GPIOC, GPIO_PIN_13);"},
    {"id":"dht22","name":"DHT22","category":"Capteurs","icon":"🌡","voltage":"3-5V","desc":"Capteur température & humidité. Précision ±0.5°C / ±2%HR","code":"#include <DHT.h>\nDHT dht(2, DHT22);\nfloat t = dht.readTemperature();"},
    {"id":"hcsr04","name":"HC-SR04","category":"Capteurs","icon":"📏","voltage":"5V","desc":"Capteur ultrason, portée 2cm-400cm, précision 3mm","code":"long dur = pulseIn(echoPin, HIGH);\nfloat dist = dur * 0.034 / 2;"},
    {"id":"pir","name":"PIR HC-SR501","category":"Capteurs","icon":"👁","voltage":"5V","desc":"Capteur mouvement infrarouge passif, détection jusqu'à 7m","code":"if (digitalRead(pirPin) == HIGH) {\n  Serial.println(\"Mouvement!\");\n}"},
    {"id":"mpu6050","name":"MPU-6050","category":"Capteurs","icon":"📐","voltage":"3.3V","desc":"Accéléromètre + gyroscope 6 axes, interface I2C","code":"#include <MPU6050.h>\nMPU6050 mpu;\nmpu.initialize();"},
    {"id":"bmp280","name":"BMP280","category":"Capteurs","icon":"🌬","voltage":"3.3V","desc":"Baromètre + température. Précision ±1 hPa / ±1°C","code":"#include <Adafruit_BMP280.h>\nAdafruit_BMP280 bmp;\nfloat temp = bmp.readTemperature();"},
    {"id":"servo","name":"Servo SG90","category":"Actionneurs","icon":"⚙","voltage":"5V","desc":"Micro-servomoteur 9g, 180°, couple 1.8kg·cm, PWM 50Hz","code":"#include <Servo.h>\nServo s;\ns.attach(9);\ns.write(90);"},
    {"id":"stepper","name":"Moteur Pas à Pas","category":"Actionneurs","icon":"🔄","voltage":"5-12V","desc":"NEMA17, 200 pas/tour, compatible A4988/DRV8825","code":"stepper.step(200); // 1 tour"},
    {"id":"relay","name":"Module Relais 5V","category":"Actionneurs","icon":"⚡","voltage":"5V","desc":"Commutation 10A/250VAC, isolation optique, actif bas","code":"digitalWrite(relayPin, LOW); // Activer\ndigitalWrite(relayPin, HIGH); // Désactiver"},
    {"id":"oled","name":"OLED 0.96\" SSD1306","category":"Affichage","icon":"🖥","voltage":"3.3V","desc":"128×64 pixels, monochrome, I2C ou SPI","code":"#include <Adafruit_SSD1306.h>\ndisplay.println(\"CognitoLab\");\ndisplay.display();"},
    {"id":"lcd","name":"LCD 16×2 + I2C","category":"Affichage","icon":"📟","voltage":"5V","desc":"16 colonnes, 2 lignes, rétroéclairage bleu, module I2C","code":"#include <LiquidCrystal_I2C.h>\nlcd.print(\"Bonjour!\");"},
    {"id":"nrf24","name":"nRF24L01+","category":"Communication","icon":"📶","voltage":"3.3V","desc":"Radio 2.4GHz, vitesse jusqu'à 2Mbps, portée 100m+","code":"#include <RF24.h>\nRF24 radio(9, 10);\nradio.begin();"},
    {"id":"ldr","name":"LDR (Photorésistance)","category":"Passifs","icon":"☀","voltage":"—","desc":"Résistance variable selon la lumière","code":"int val = analogRead(A0); // 0=noir, 1023=lumière"},
    {"id":"resistor","name":"Résistance","category":"Passifs","icon":"🔌","voltage":"—","desc":"Composant passif limitant le courant. Code couleur.","code":"// R = V / I\n// Ex: 220Ω pour LED avec 5V"},
    {"id":"capacitor","name":"Condensateur","category":"Passifs","icon":"🔋","voltage":"—","desc":"Stockage d'énergie, filtrage. Électrolytique ou céramique.","code":"// Filtre RC: t = R * C\n// Ex: 10kΩ * 100µF = 1s"},
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
@app.route("/")
def dashboard():
    projects_count = Project.query.count()
    posts_count    = CommunityPost.query.count()
    progresses     = {p.course_id: p.progress for p in CourseProgress.query.all()}
    recent_projects = Project.query.order_by(Project.created_at.desc()).limit(3).all()
    return render_template("dashboard.html",
        projects_count=projects_count,
        posts_count=posts_count,
        progresses=progresses,
        recent_projects=recent_projects,
        courses=COURSES[:3])

@app.route("/simulator")
def simulator():
    board = request.args.get("board", "arduino-uno")
    return render_template("simulator.html", boards=BOARDS, selected_board=board)

@app.route("/courses")
def courses():
    progresses = {p.course_id: p.progress for p in CourseProgress.query.all()}
    return render_template("courses.html", courses=COURSES, progresses=progresses)

@app.route("/components")
def components():
    cat = request.args.get("cat", "Tous")
    categories = ["Tous", "Capteurs", "Actionneurs", "Microcontrôleurs", "Affichage", "Communication", "Passifs"]
    filtered = COMPONENTS if cat == "Tous" else [c for c in COMPONENTS if c["category"] == cat]
    comp_id = request.args.get("comp", None)
    selected = next((c for c in COMPONENTS if c["id"] == comp_id), None)
    return render_template("components.html",
        components=filtered, categories=categories,
        selected_cat=cat, selected_comp=selected)

@app.route("/projects")
def projects():
    all_projects = Project.query.order_by(Project.created_at.desc()).all()
    return render_template("projects.html", projects=all_projects, boards=BOARDS)

@app.route("/community")
def community():
    board_filter = request.args.get("board", "Tous")
    search = request.args.get("q", "")
    query = CommunityPost.query
    if board_filter != "Tous":
        query = query.filter(CommunityPost.board == board_filter)
    if search:
        query = query.filter(
            CommunityPost.title.ilike(f"%{search}%") |
            CommunityPost.description.ilike(f"%{search}%")
        )
    posts = query.order_by(CommunityPost.created_at.desc()).all()
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
    return jsonify([p.to_dict() for p in Project.query.order_by(Project.created_at.desc()).all()])

@app.route("/api/projects", methods=["POST"])
def api_create_project():
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

@app.route("/api/projects/<int:pid>", methods=["PUT"])
def api_update_project(pid):
    p = Project.query.get_or_404(pid)
    data = request.get_json() or {}
    p.title  = data.get("title", p.title)
    p.board  = data.get("board", p.board)
    p.code   = data.get("code", p.code)
    p.status = data.get("status", p.status)
    db.session.commit()
    return jsonify(p.to_dict())

@app.route("/api/projects/<int:pid>", methods=["DELETE"])
def api_delete_project(pid):
    p = Project.query.get_or_404(pid)
    db.session.delete(p)
    db.session.commit()
    return jsonify({"ok": True})

@app.route("/api/community/posts", methods=["POST"])
def api_create_post():
    data = request.get_json() or {}
    initials = "".join(w[0].upper() for w in data.get("author", "Anonyme").split()[:2])
    post = CommunityPost(
        author=data.get("author", "Anonyme"),
        avatar=initials or "AN",
        title=data.get("title", ""),
        description=data.get("description", ""),
        board=data.get("board", "Arduino"),
        tags=",".join(data.get("tags", [])),
    )
    db.session.add(post)
    db.session.commit()
    return jsonify(post.to_dict()), 201

@app.route("/api/community/posts/<int:pid>/like", methods=["POST"])
def api_like_post(pid):
    post = CommunityPost.query.get_or_404(pid)
    post.likes += 1
    db.session.commit()
    return jsonify({"likes": post.likes})

@app.route("/api/courses/<course_id>/progress", methods=["POST"])
def api_update_progress(course_id):
    data = request.get_json() or {}
    prog = CourseProgress.query.filter_by(course_id=course_id).first()
    if not prog:
        prog = CourseProgress(course_id=course_id, progress=0)
        db.session.add(prog)
    prog.progress = min(100, max(0, data.get("progress", prog.progress)))
    db.session.commit()
    return jsonify({"course_id": course_id, "progress": prog.progress})

# ── Run ────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
