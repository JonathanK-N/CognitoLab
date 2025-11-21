import { Router } from "express";
import { ProjectModel } from "../models/Project.js";
import { authMiddleware } from "../middleware/auth.js";

const router = Router();

router.get("/", authMiddleware, async (req, res) => {
  const projects = await ProjectModel.find({ owner: req.user?.id });
  res.json(projects);
});

router.post("/", authMiddleware, async (req, res) => {
  const project = await ProjectModel.create({ ...req.body, owner: req.user?.id });
  res.json(project);
});

export default router;
