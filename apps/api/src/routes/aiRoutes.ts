import { Router } from "express";

const router = Router();
const anthropicKey = process.env.ANTHROPIC_API_KEY;

router.post("/assist", async (req, res) => {
  if (!anthropicKey) {
    return res.status(500).json({ message: "ANTHROPIC_API_KEY manquant côté serveur." });
  }
  const { prompt, board, context } = req.body ?? {};
  if (!prompt) return res.status(400).json({ message: "prompt requis" });

  try {
    const systemPrompt = `Tu es Cognito, l'assistant IA de CognitoLab — une plateforme spécialisée en électronique, microcontrôleurs et programmation embarquée.
Tu aides les utilisateurs à concevoir des circuits, programmer des microcontrôleurs (Arduino, ESP32, Raspberry Pi, STM32, RP2040, ROS) et comprendre les composants électroniques.
Réponds en français de manière claire, pédagogique et avec des exemples de code si pertinent.
Utilise des explications visuelles quand c'est utile. Sois enthousiaste et encourageant.
Contexte de travail: ${context ?? "général"}`;

    const userContent = board && board !== "n/a"
      ? `Carte/plateforme: ${board}\n\n${prompt}`
      : prompt;

    const body = {
      model: "claude-opus-4-5",
      max_tokens: 1024,
      system: systemPrompt,
      messages: [{ role: "user", content: userContent }]
    };

    const response = await fetch("https://api.anthropic.com/v1/messages", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-api-key": anthropicKey,
        "anthropic-version": "2023-06-01"
      },
      body: JSON.stringify(body)
    });

    if (!response.ok) {
      const errText = await response.text();
      return res.status(502).json({ message: "Erreur Anthropic Claude", detail: errText });
    }

    const json = await response.json();
    const content = json.content?.[0]?.text ?? "";
    res.json({ answer: content });
  } catch (err) {
    console.error("Claude AI error", err);
    res.status(500).json({ message: "Erreur interne IA" });
  }
});

export default router;
