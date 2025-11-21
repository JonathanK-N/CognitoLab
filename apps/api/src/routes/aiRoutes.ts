import { Router } from "express";

const router = Router();
const openAiKey = process.env.OPENAI_API_KEY;
const model = process.env.OPENAI_MODEL ?? "gpt-4o-mini";

router.post("/assist", async (req, res) => {
  if (!openAiKey) return res.status(500).json({ message: "OPENAI_API_KEY manquant côté serveur." });
  const { prompt, board } = req.body ?? {};
  if (!prompt) return res.status(400).json({ message: "prompt requis" });

  try {
    const body = {
      model,
      messages: [
        { role: "system", content: "Tu es l'assistant CognitoLab spécialisé Arduino/ESP32/STM32 et robotique." },
        {
          role: "user",
          content: `Carte: ${board ?? "n/a"}\nQuestion: ${prompt}\nRéponds avec des conseils concis et du code si utile.`
        }
      ],
      temperature: 0.4
    };

    const response = await fetch("https://api.openai.com/v1/chat/completions", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${openAiKey}`
      },
      body: JSON.stringify(body)
    });

    if (!response.ok) {
      const errText = await response.text();
      return res.status(502).json({ message: "Erreur OpenAI", detail: errText });
    }

    const json = await response.json();
    const content = json.choices?.[0]?.message?.content ?? "";
    res.json({ answer: content });
  } catch (err) {
    console.error("OpenAI error", err);
    res.status(500).json({ message: "Erreur interne AI" });
  }
});

export default router;
