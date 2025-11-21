import { WebSocketServer } from "ws";

type SimulationMessage = {
  type: "state";
  payload: any;
};

export function attachSimulationSocket(wss: WebSocketServer) {
  wss.on("connection", (ws) => {
    ws.on("message", (msg) => {
      try {
        const parsed = JSON.parse(msg.toString()) as SimulationMessage;
        if (parsed.type === "state") {
          // broadcast to all
          wss.clients.forEach((client) => {
            if (client.readyState === ws.OPEN) client.send(msg.toString());
          });
        }
      } catch (err) {
        console.error("WS parse error", err);
      }
    });
  });
}
