import React, { useEffect, useRef, useState } from "react";

type Message = { role: "user" | "assistant" | "error"; text: string };

const apiBase = (import.meta as any).env.VITE_API_URL?.replace(/\/$/, "") || "";

interface Props {
  board?: string;
  embedded?: boolean;
  onClose?: () => void;
}

const CognitoIcon = () => (
  <svg viewBox="0 0 40 40" fill="none" className="w-full h-full">
    <circle cx="20" cy="20" r="18" stroke="#1976D2" strokeWidth="2" fill="rgba(21,101,192,0.15)"/>
    <circle cx="20" cy="20" r="7" stroke="#42A5F5" strokeWidth="2" fill="none"/>
    <line x1="20" y1="5"  x2="20" y2="13" stroke="#2196F3" strokeWidth="2" strokeLinecap="round"/>
    <line x1="20" y1="27" x2="20" y2="35" stroke="#2196F3" strokeWidth="2" strokeLinecap="round"/>
    <line x1="5"  y1="20" x2="13" y2="20" stroke="#2196F3" strokeWidth="2" strokeLinecap="round"/>
    <line x1="27" y1="20" x2="35" y2="20" stroke="#2196F3" strokeWidth="2" strokeLinecap="round"/>
    <circle cx="20" cy="5"  r="2.5" fill="#1976D2"/>
    <circle cx="20" cy="35" r="2.5" fill="#1976D2"/>
    <circle cx="5"  cy="20" r="2.5" fill="#1976D2"/>
    <circle cx="35" cy="20" r="2.5" fill="#1976D2"/>
  </svg>
);

const AIAssistantPanel: React.FC<Props> = ({ board = "général", embedded = false, onClose }) => {
  const [history, setHistory] = useState<Message[]>([
    { role: "assistant", text: "Bonjour ! Je suis **Cognito**, votre assistant IA CognitoLab 🧠⚡\n\nJe peux vous aider à :\n- Programmer vos microcontrôleurs\n- Déboguer vos circuits\n- Expliquer les composants électroniques\n- Guider vos projets Arduino, ESP32, Raspberry Pi...\n\nQue puis-je faire pour vous ?" }
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [history]);

  const send = async () => {
    const text = input.trim();
    if (!text || loading) return;
    setHistory(prev => [...prev, { role: "user", text }]);
    setInput("");
    setLoading(true);
    try {
      const res = await fetch(`${apiBase}/ai/assist`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt: text, board, context: `Interface: ${embedded ? "panel" : "flottant"}` })
      });
      if (!res.ok) throw new Error((await res.text()) || "Erreur IA");
      const json = await res.json();
      setHistory(prev => [...prev, { role: "assistant", text: json?.answer ?? "Pas de réponse." }]);
    } catch (err: any) {
      setHistory(prev => [...prev, { role: "error", text: `Erreur: ${err?.message ?? "inconnue"}` }]);
    } finally {
      setLoading(false);
    }
  };

  const formatText = (text: string) =>
    text.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
        .replace(/`([^`]+)`/g, "<code style='background:rgba(33,150,243,0.15);padding:1px 5px;border-radius:4px;font-family:monospace;font-size:0.85em'>$1</code>")
        .replace(/\n/g, "<br/>");

  return (
    <div className={embedded ? "flex flex-col h-full" : "flex flex-col h-full"}>
      {/* Header */}
      <div className="flex items-center gap-3 px-4 py-3 border-b border-cl-blue/15"
        style={{ background: "linear-gradient(135deg, rgba(21,101,192,0.2), rgba(0,188,212,0.1))" }}>
        <div className="w-9 h-9 rounded-full p-0.5"
          style={{ background: "linear-gradient(135deg, #1565C0, #00BCD4)" }}>
          <div className="w-full h-full rounded-full bg-cl-dark p-1">
            <CognitoIcon />
          </div>
        </div>
        <div className="flex-1">
          <p className="text-sm font-bold text-white">Cognito</p>
          <p className="text-xs text-cl-blue-4/70">Assistant IA · Propulsé par Claude</p>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse-glow" />
          <span className="text-xs text-emerald-400">En ligne</span>
        </div>
        {onClose && (
          <button onClick={onClose} className="text-slate-500 hover:text-white ml-1 transition-colors text-lg leading-none">×</button>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3"
        style={{ background: "rgba(10,14,26,0.8)" }}>
        {history.map((m, i) => (
          <div key={i} className={`flex gap-2 ${m.role === "user" ? "flex-row-reverse" : "flex-row"}`}>
            {m.role !== "user" && (
              <div className="w-7 h-7 rounded-full flex-shrink-0 p-0.5"
                style={{ background: m.role === "error" ? "#7f1d1d" : "linear-gradient(135deg, #1565C0, #00BCD4)" }}>
                <CognitoIcon />
              </div>
            )}
            <div className={`max-w-[78%] px-3 py-2 rounded-2xl text-xs leading-relaxed ${
              m.role === "user"
                ? "bg-cl-blue/25 text-slate-200 border border-cl-blue/30 rounded-tr-sm"
                : m.role === "error"
                ? "bg-rose-900/30 text-rose-300 border border-rose-700/40"
                : "bg-cl-dark-4/80 text-slate-200 border border-cl-blue/10 rounded-tl-sm"
            }`}
              dangerouslySetInnerHTML={{ __html: formatText(m.text) }}
            />
          </div>
        ))}
        {loading && (
          <div className="flex gap-2">
            <div className="w-7 h-7 rounded-full p-0.5" style={{ background: "linear-gradient(135deg, #1565C0, #00BCD4)" }}>
              <CognitoIcon />
            </div>
            <div className="px-4 py-3 rounded-2xl rounded-tl-sm bg-cl-dark-4/80 border border-cl-blue/10 flex gap-1.5 items-center">
              {[0,1,2].map(n => (
                <span key={n} className="w-1.5 h-1.5 rounded-full bg-cl-blue-3 animate-bounce"
                  style={{ animationDelay: `${n * 0.15}s` }} />
              ))}
            </div>
          </div>
        )}
        <div ref={endRef} />
      </div>

      {/* Input */}
      <div className="p-3 border-t border-cl-blue/10 bg-cl-dark-2/90">
        {board && board !== "général" && (
          <div className="mb-2">
            <span className="tag">
              <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20"><circle cx="10" cy="10" r="8"/></svg>
              {board}
            </span>
          </div>
        )}
        <div className="flex gap-2">
          <textarea
            className="cl-input flex-1 resize-none text-xs"
            rows={2}
            value={input}
            onChange={e => setInput(e.target.value)}
            placeholder="Posez votre question à Cognito..."
            onKeyDown={e => {
              if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
                e.preventDefault();
                send();
              }
            }}
          />
          <button
            onClick={send}
            disabled={!input.trim() || loading}
            className="px-3 py-2 rounded-lg flex flex-col items-center justify-center gap-1 transition-all disabled:opacity-40"
            style={{ background: "linear-gradient(135deg, #1565C0, #1976D2)", minWidth: 42 }}
          >
            <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
            </svg>
          </button>
        </div>
        <p className="text-xs text-slate-600 mt-1.5">Ctrl+Entrée pour envoyer · Propulsé par Claude (Anthropic)</p>
      </div>
    </div>
  );
};

export default AIAssistantPanel;
