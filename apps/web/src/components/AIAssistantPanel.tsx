import React, { useMemo, useState } from "react";
import { Button, Card } from "@cognitolab/ui";

type Message = { role: "user" | "assistant" | "error"; text: string };

const apiBase = (import.meta as any).env.VITE_API_URL?.replace(/\/$/, "") || "";

const AIAssistantPanel: React.FC<{ board: string }> = ({ board }) => {
  const [history, setHistory] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const disabled = useMemo(() => !input.trim() || loading, [input, loading]);

  const send = async () => {
    if (!input.trim()) return;
    const userMsg: Message = { role: "user", text: input.trim() };
    setHistory((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);
    try {
      const res = await fetch(`${apiBase}/ai/assist`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt: userMsg.text, board })
      });
      if (!res.ok) {
        const text = await res.text();
        throw new Error(text || "Erreur AI");
      }
      const json = await res.json();
      const answer = (json?.answer as string) ?? "Aucune réponse AI.";
      setHistory((prev) => [...prev, { role: "assistant", text: answer }]);
    } catch (err: any) {
      setHistory((prev) => [
        ...prev,
        { role: "error", text: `Erreur assistant: ${err?.message ?? "inconnue"}` }
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card title="Assistant IA" subtitle="Explications et débogage Arduino/ESP32/STM32 par OpenAI">
      <div className="space-y-3">
        <div className="h-48 overflow-auto border rounded bg-slate-50 p-2 text-sm">
          {history.length === 0 && <p className="text-slate-500">Pose une question sur {board}...</p>}
          {history.map((m, i) => (
            <p
              key={i}
              className={
                m.role === "assistant"
                  ? "text-emerald-700"
                  : m.role === "error"
                  ? "text-rose-700"
                  : "text-slate-800"
              }
            >
              <strong>
                {m.role === "assistant" ? "IA: " : m.role === "error" ? "Erreur: " : "Toi: "}
              </strong>
              {m.text}
            </p>
          ))}
        </div>
        <textarea
          className="w-full border rounded px-3 py-2 text-sm"
          rows={3}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={`Question pour ${board} ...`}
          onKeyDown={(e) => {
            if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
              e.preventDefault();
              !disabled && send();
            }
          }}
        />
        <div className="flex justify-between items-center">
          <p className="text-xs text-slate-500">OpenAI model côté serveur</p>
          <Button size="sm" onClick={send} disabled={disabled} loading={loading}>
            Générer
          </Button>
        </div>
      </div>
    </Card>
  );
};

export default AIAssistantPanel;
