import { Router } from "express";
import fs from "fs";
import path from "path";

const router = Router();

router.get("/catalog", (_req, res) => {
  const catalogPath = path.resolve(process.cwd(), "robots/robotCatalog.json");
  if (!fs.existsSync(catalogPath)) return res.status(404).json({ message: "robotCatalog.json absent" });
  const json = JSON.parse(fs.readFileSync(catalogPath, "utf-8"));
  res.json(json);
});

export default router;
