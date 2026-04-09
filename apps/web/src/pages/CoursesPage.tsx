import React, { useState } from "react";
import { ProgressBar } from "@cognitolab/ui";

const categories = ["Tous", "Arduino", "ESP32", "Raspberry Pi", "STM32", "ROS", "Débutant", "Avancé"];

const courses = [
  {
    id: "arduino-basics",
    title: "Arduino pour débutants",
    platform: "Arduino",
    level: "Débutant",
    sections: 8,
    progress: 72,
    duration: "4h",
    icon: "🔵",
    color: "#1565C0",
    desc: "Maîtrisez les bases d'Arduino: GPIO, PWM, I2C, SPI, UART et vos premiers projets.",
    tags: ["Arduino", "Débutant", "C++"],
    video: "https://www.youtube.com/embed/6mXM-oGggrM"
  },
  {
    id: "esp32-iot",
    title: "ESP32 IoT avancé",
    platform: "ESP32",
    level: "Avancé",
    sections: 10,
    progress: 34,
    duration: "6h",
    icon: "📡",
    color: "#00BCD4",
    desc: "Connectez l'ESP32 en WiFi, BLE, MQTT. Construisez des objets connectés et dashboards.",
    tags: ["ESP32", "WiFi", "MQTT", "IoT"],
    video: "https://www.youtube.com/embed/i3z5V3ZrIgY"
  },
  {
    id: "rpi-linux",
    title: "Raspberry Pi & Linux embarqué",
    platform: "Raspberry Pi",
    level: "Intermédiaire",
    sections: 9,
    progress: 0,
    duration: "5h",
    icon: "🍓",
    color: "#E53935",
    desc: "Découvrez Linux embarqué, Python, GPIO sur Raspberry Pi et construisez un serveur maison.",
    tags: ["Raspberry Pi", "Linux", "Python"],
    video: ""
  },
  {
    id: "stm32-bare",
    title: "STM32 Bare-Metal",
    platform: "STM32",
    level: "Avancé",
    sections: 7,
    progress: 0,
    duration: "7h",
    icon: "💜",
    color: "#7C4DFF",
    desc: "Programmation bas niveau STM32 avec HAL, DMA, interruptions et périphériques avancés.",
    tags: ["STM32", "Bare-metal", "C"],
    video: ""
  },
  {
    id: "ros-intro",
    title: "Introduction à ROS 2",
    platform: "ROS",
    level: "Avancé",
    sections: 12,
    progress: 0,
    duration: "8h",
    icon: "🤖",
    color: "#42A5F5",
    desc: "Nodes, Topics, Services, Actions dans ROS 2. Simulez votre robot avec Gazebo et RViz.",
    tags: ["ROS", "Python", "Robotique"],
    video: "https://www.youtube.com/embed/CNzsPzK0dKk"
  },
  {
    id: "esp32-display",
    title: "ESP32 + Écrans & Capteurs",
    platform: "ESP32",
    level: "Intermédiaire",
    sections: 6,
    progress: 58,
    duration: "3h",
    icon: "📺",
    color: "#00ACC1",
    desc: "OLED, TFT, LCD. Interfacez DHT22, BMP280, MPU6050 avec affichage en temps réel.",
    tags: ["ESP32", "Capteurs", "Affichage"],
    video: ""
  },
  {
    id: "pico-micropython",
    title: "Raspberry Pi Pico & MicroPython",
    platform: "Raspberry Pi",
    level: "Débutant",
    sections: 7,
    progress: 0,
    duration: "3.5h",
    icon: "🟡",
    color: "#F57F17",
    desc: "Démarrez avec MicroPython sur RP2040. Servo, LEDs, capteurs et projets fun.",
    tags: ["Pico", "MicroPython", "Débutant"],
    video: ""
  },
  {
    id: "petit-projets",
    title: "50 Petits Projets Électronique",
    platform: "Arduino",
    level: "Débutant",
    sections: 15,
    progress: 12,
    duration: "10h",
    icon: "⚡",
    color: "#1976D2",
    desc: "LED RGB, thermomètre, serrure RFID, piano, météo... 50 projets guidés pas à pas.",
    tags: ["Arduino", "Projets", "Débutant"],
    video: ""
  },
];

const CoursesPage: React.FC = () => {
  const [cat, setCat]   = useState("Tous");
  const [expanded, setExpanded] = useState<string | null>(null);

  const filtered = cat === "Tous"
    ? courses
    : courses.filter(c => c.tags.includes(cat) || c.level === cat);

  const levelColor = (l: string) =>
    l === "Débutant" ? "badge-green" : l === "Avancé" ? "badge-amber" : "badge-blue";

  return (
    <div className="space-y-6 pb-8">
      {/* Header */}
      <div className="flex items-start justify-between flex-wrap gap-3">
        <div>
          <h1 className="section-title">Cours & eLearning</h1>
          <p className="section-sub">Apprenez l'électronique et la programmation embarquée à votre rythme</p>
        </div>
        <div className="flex items-center gap-2 px-3 py-2 rounded-xl glass text-xs text-cl-blue-4">
          <span>📚</span> {courses.filter(c => c.progress > 0).length} cours en cours
        </div>
      </div>

      {/* Categories */}
      <div className="flex flex-wrap gap-2">
        {categories.map(c => (
          <button
            key={c}
            onClick={() => setCat(c)}
            className={`board-chip ${cat === c ? "active" : ""}`}
          >
            {c}
          </button>
        ))}
      </div>

      {/* Course grid */}
      <div className="grid md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {filtered.map(course => (
          <div key={course.id} className="course-card">
            {/* Cover / video */}
            <div className="relative h-36 overflow-hidden"
              style={{ background: `linear-gradient(135deg, ${course.color}22, rgba(13,20,33,0.9))` }}>
              {course.video && expanded === course.id ? (
                <iframe
                  src={course.video}
                  className="w-full h-full"
                  allow="accelerometer; autoplay; encrypted-media"
                  allowFullScreen
                  title={course.title}
                />
              ) : (
                <div className="w-full h-full flex flex-col items-center justify-center gap-2">
                  <span className="text-5xl">{course.icon}</span>
                  {course.video && (
                    <button
                      onClick={() => setExpanded(course.id)}
                      className="text-xs px-3 py-1 rounded-lg btn-ghost"
                    >
                      ▶ Aperçu
                    </button>
                  )}
                </div>
              )}
              {course.progress > 0 && (
                <div className="absolute bottom-0 left-0 right-0 px-2 pb-1.5">
                  <ProgressBar value={course.progress} color="blue" />
                </div>
              )}
            </div>

            {/* Content */}
            <div className="p-4 space-y-3">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span className={`badge ${levelColor(course.level)}`}>{course.level}</span>
                  <span className="text-xs text-slate-500">{course.duration}</span>
                </div>
                <h3 className="text-sm font-bold text-white leading-snug">{course.title}</h3>
                <p className="text-xs text-slate-400 mt-1 line-clamp-2">{course.desc}</p>
              </div>

              <div className="flex flex-wrap gap-1">
                {course.tags.slice(0,3).map(t => (
                  <span key={t} className="tag text-xs">{t}</span>
                ))}
              </div>

              <div className="flex items-center justify-between text-xs text-slate-500">
                <span>{course.sections} sections</span>
                {course.progress > 0 && <span className="text-cl-blue-4">{course.progress}%</span>}
              </div>

              <div className="flex gap-2">
                <button className="btn-primary flex-1 py-1.5 text-xs rounded-lg">
                  {course.progress > 0 ? "▶ Continuer" : "▶ Commencer"}
                </button>
                <button className="btn-ghost px-3 py-1.5 text-xs rounded-lg">Quiz</button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Learning path CTA */}
      <div className="glass rounded-2xl p-6 text-center"
        style={{ border: "1px solid rgba(33,150,243,0.2)" }}>
        <p className="text-2xl mb-2">🎯</p>
        <h3 className="text-base font-bold text-white mb-1">Parcours personnalisé avec Cognito</h3>
        <p className="text-sm text-slate-400 mb-4">
          Demandez à Cognito de créer un parcours d'apprentissage adapté à votre niveau et vos objectifs.
        </p>
        <button className="btn-primary px-6 py-2 rounded-xl text-sm">
          🧠 Créer mon parcours
        </button>
      </div>
    </div>
  );
};

export default CoursesPage;
