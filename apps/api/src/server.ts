import express from "express";
import cors from "cors";
import dotenv from "dotenv";
import mongoose from "mongoose";
import { createServer } from "http";
import { WebSocketServer } from "ws";
import authRoutes from "./routes/authRoutes.js";
import courseRoutes from "./routes/courseRoutes.js";
import projectRoutes from "./routes/projectRoutes.js";
import componentRoutes from "./routes/componentRoutes.js";
import robotRoutes from "./routes/robotRoutes.js";
import aiRoutes from "./routes/aiRoutes.js";
import { attachSimulationSocket } from "./sockets/simulationSocket.js";

dotenv.config();
const app = express();

app.use(cors());
app.use(express.json({ limit: "2mb" }));

app.use("/auth", authRoutes);
app.use("/courses", courseRoutes);
app.use("/projects", projectRoutes);
app.use("/components", componentRoutes);
app.use("/robots", robotRoutes);
app.use("/ai", aiRoutes);

const httpServer = createServer(app);
const wss = new WebSocketServer({ server: httpServer, path: "/ws/simulation" });
attachSimulationSocket(wss);

const port = process.env.PORT || 4000;
const mongoUrl = process.env.MONGO_URL || "mongodb://localhost:27017/cognitolab";

mongoose
  .connect(mongoUrl)
  .then(() => {
    httpServer.listen(port, () => {
      console.log(`API running on http://localhost:${port}`);
    });
  })
  .catch((err) => {
    console.error("Mongo connection failed", err);
    process.exit(1);
  });
