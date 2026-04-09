import React, { useState } from "react";

type Post = {
  id: string;
  author: string;
  avatar: string;
  title: string;
  desc: string;
  board: string;
  tags: string[];
  likes: number;
  comments: number;
  date: string;
  liked: boolean;
};

const initialPosts: Post[] = [
  {
    id: "1", author: "Alexandre D.", avatar: "AD",
    title: "Robot suiveur de ligne — ESP32 + caméra OV2640",
    desc: "Mon robot autonome avec détection de ligne par vision artificielle. Utilise un réseau de neurones léger (TensorFlow Lite) directement sur l'ESP32.",
    board: "ESP32", tags: ["IA", "Vision", "Autonome"],
    likes: 84, comments: 12, date: "il y a 2 jours", liked: false
  },
  {
    id: "2", author: "Sofia M.", avatar: "SM",
    title: "Station météo connectée Raspberry Pi + Dashboard",
    desc: "Station météo complète avec DHT22, BMP280, anémomètre. Dashboard web en temps réel avec grafana et InfluxDB.",
    board: "Raspberry Pi", tags: ["IoT", "Météo", "Dashboard"],
    likes: 61, comments: 8, date: "il y a 3 jours", liked: false
  },
  {
    id: "3", author: "Karim B.", avatar: "KB",
    title: "Bras robotique 6 DOF contrôlé par gestes",
    desc: "Bras articulé imprimé en 3D, STM32 + servos + capteur MPU6050 sur gant. Cinématique inverse temps réel.",
    board: "STM32", tags: ["Robotique", "Gestes", "3D Print"],
    likes: 143, comments: 27, date: "il y a 5 jours", liked: false
  },
  {
    id: "4", author: "Léa T.", avatar: "LT",
    title: "Serrure connectée RFID + Arduino + app mobile",
    desc: "Serrure électronique avec MFRC522, buzzer, LED et application React Native pour gérer les accès depuis le téléphone.",
    board: "Arduino Uno", tags: ["RFID", "Sécurité", "Mobile"],
    likes: 39, comments: 5, date: "il y a 1 semaine", liked: false
  },
  {
    id: "5", author: "Marc P.", avatar: "MP",
    title: "Oscilloscope portable avec RP2040 et écran TFT",
    desc: "Oscilloscope 2 canaux, 500kHz d'échantillonnage, écran 2.8 TFT ILI9341. Batterie LiPo intégrée, boitier imprimé 3D.",
    board: "RP2040", tags: ["Mesure", "TFT", "Portable"],
    likes: 212, comments: 43, date: "il y a 2 semaines", liked: false
  },
  {
    id: "6", author: "Yuki R.", avatar: "YR",
    title: "Piano MIDI sur ESP32 avec 49 touches capacitives",
    desc: "Clavier MIDI complet avec touches capacitives MPR121 x4. Sortie MIDI USB + bluetooth. Banque de sons SoundFont embarquée.",
    board: "ESP32", tags: ["MIDI", "Musique", "Capacitif"],
    likes: 97, comments: 19, date: "il y a 3 semaines", liked: false
  },
];

const boardColors: Record<string, string> = {
  "ESP32":        "#00BCD4",
  "Arduino Uno":  "#1565C0",
  "Raspberry Pi": "#E53935",
  "STM32":        "#7C4DFF",
  "RP2040":       "#00897B",
};

const CommunityPage: React.FC = () => {
  const [posts, setPosts] = useState<Post[]>(initialPosts);
  const [filter, setFilter] = useState("Tous");
  const [search, setSearch] = useState("");
  const [newTitle, setNewTitle] = useState("");
  const [newDesc, setNewDesc]   = useState("");
  const [showForm, setShowForm] = useState(false);

  const boards = ["Tous", "Arduino Uno", "ESP32", "Raspberry Pi", "STM32", "RP2040"];

  const filtered = posts.filter(p =>
    (filter === "Tous" || p.board === filter) &&
    (p.title.toLowerCase().includes(search.toLowerCase()) ||
     p.desc.toLowerCase().includes(search.toLowerCase()))
  );

  const toggleLike = (id: string) => {
    setPosts(prev => prev.map(p =>
      p.id === id ? { ...p, liked: !p.liked, likes: p.liked ? p.likes - 1 : p.likes + 1 } : p
    ));
  };

  const share = () => {
    if (!newTitle.trim()) return;
    const p: Post = {
      id: crypto.randomUUID(),
      author: "Vous",
      avatar: "VU",
      title: newTitle,
      desc: newDesc,
      board: filter !== "Tous" ? filter : "Arduino Uno",
      tags: ["Nouveau"],
      likes: 0, comments: 0,
      date: "À l'instant",
      liked: false
    };
    setPosts(prev => [p, ...prev]);
    setNewTitle(""); setNewDesc(""); setShowForm(false);
  };

  return (
    <div className="space-y-5 pb-8">
      {/* Header */}
      <div className="flex items-start justify-between flex-wrap gap-3">
        <div>
          <h1 className="section-title">Communauté CognitoLab</h1>
          <p className="section-sub">Découvrez et partagez vos projets électronique avec la communauté</p>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          className="btn-primary px-4 py-2 text-sm rounded-xl"
        >
          + Partager un projet
        </button>
      </div>

      {/* Share form */}
      {showForm && (
        <div className="glass rounded-2xl p-5 space-y-3"
          style={{ border: "1px solid rgba(33,150,243,0.25)" }}>
          <p className="text-sm font-bold text-white">Partager votre projet</p>
          <input
            value={newTitle}
            onChange={e => setNewTitle(e.target.value)}
            placeholder="Titre du projet"
            className="cl-input"
          />
          <textarea
            value={newDesc}
            onChange={e => setNewDesc(e.target.value)}
            placeholder="Description — parlez de votre projet, de la technologie utilisée..."
            rows={3}
            className="cl-input resize-none"
          />
          <div className="flex gap-2">
            <button onClick={share} disabled={!newTitle.trim()} className="btn-primary text-sm px-4 py-2 rounded-lg">
              Publier
            </button>
            <button onClick={() => setShowForm(false)} className="btn-ghost text-sm px-4 py-2 rounded-lg">
              Annuler
            </button>
          </div>
        </div>
      )}

      {/* Search + filters */}
      <div className="flex flex-wrap gap-3 items-center">
        <input
          value={search}
          onChange={e => setSearch(e.target.value)}
          placeholder="Rechercher un projet..."
          className="cl-input"
          style={{ maxWidth: 300 }}
        />
        <div className="flex flex-wrap gap-2">
          {boards.map(b => (
            <button key={b} onClick={() => setFilter(b)} className={`board-chip ${filter === b ? "active" : ""}`}>
              {b}
            </button>
          ))}
        </div>
      </div>

      {/* Stats bar */}
      <div className="flex items-center gap-6 text-xs text-slate-500 px-2">
        <span><strong className="text-cl-blue-4">{posts.length}</strong> projets partagés</span>
        <span><strong className="text-cl-blue-4">{posts.reduce((s,p) => s+p.likes, 0)}</strong> likes</span>
        <span><strong className="text-cl-cyan">Actif</strong> · Mis à jour récemment</span>
      </div>

      {/* Post grid */}
      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filtered.map(post => (
          <div key={post.id} className="glass rounded-2xl overflow-hidden flex flex-col transition-all hover:border-cl-blue/30"
            style={{ border: "1px solid rgba(33,150,243,0.1)" }}>
            {/* Post header color band */}
            <div className="h-1.5" style={{ background: `linear-gradient(90deg, ${boardColors[post.board] ?? "#1565C0"}, #00BCD4)` }} />

            <div className="p-4 flex flex-col flex-1 space-y-3">
              {/* Author */}
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold text-white"
                  style={{ background: `linear-gradient(135deg, ${boardColors[post.board] ?? "#1565C0"}, #00BCD4)` }}>
                  {post.avatar}
                </div>
                <div>
                  <p className="text-xs font-semibold text-white">{post.author}</p>
                  <p className="text-xs text-slate-500">{post.date}</p>
                </div>
                <div className="ml-auto">
                  <span className="tag" style={{ color: boardColors[post.board] ?? "#64B5F6", borderColor: `${boardColors[post.board]}33` ?? "rgba(33,150,243,0.2)" }}>
                    {post.board}
                  </span>
                </div>
              </div>

              {/* Content */}
              <div className="flex-1">
                <h3 className="text-sm font-bold text-white leading-snug mb-1">{post.title}</h3>
                <p className="text-xs text-slate-400 leading-relaxed line-clamp-3">{post.desc}</p>
              </div>

              {/* Tags */}
              <div className="flex flex-wrap gap-1">
                {post.tags.map(t => (
                  <span key={t} className="tag text-xs">{t}</span>
                ))}
              </div>

              {/* Actions */}
              <div className="flex items-center justify-between pt-1 border-t border-cl-blue/8">
                <button
                  onClick={() => toggleLike(post.id)}
                  className={`flex items-center gap-1.5 text-xs px-2.5 py-1.5 rounded-lg transition-all ${
                    post.liked
                      ? "text-red-400 bg-red-400/10"
                      : "text-slate-500 hover:text-red-400 hover:bg-red-400/10"
                  }`}
                >
                  {post.liked ? "❤" : "🤍"} {post.likes}
                </button>
                <button className="flex items-center gap-1.5 text-xs px-2.5 py-1.5 rounded-lg text-slate-500 hover:text-cl-blue-4 hover:bg-cl-blue/10 transition-all">
                  💬 {post.comments}
                </button>
                <button className="flex items-center gap-1.5 text-xs px-2.5 py-1.5 rounded-lg text-slate-500 hover:text-cl-blue-4 hover:bg-cl-blue/10 transition-all">
                  🔖 Sauvegarder
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {filtered.length === 0 && (
        <div className="text-center py-16 text-slate-500">
          <div className="text-4xl mb-3">🔍</div>
          <p className="text-sm">Aucun projet trouvé</p>
        </div>
      )}
    </div>
  );
};

export default CommunityPage;
