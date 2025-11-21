import { Router } from "express";
import { CourseModel } from "../models/Course.js";
import { authMiddleware, requireRole } from "../middleware/auth.js";

const router = Router();

router.get("/", async (_req, res) => {
  const courses = await CourseModel.find();
  res.json(courses);
});

router.post("/", authMiddleware, requireRole(["admin", "professeur"]), async (req, res) => {
  const course = await CourseModel.create(req.body);
  res.json(course);
});

export default router;
