import { Router } from "express";
import bcrypt from "bcryptjs";
import jwt from "jsonwebtoken";
import { UserModel } from "../models/User.js";

const router = Router();
const secret = process.env.JWT_SECRET || "devsecret";

router.post("/register", async (req, res) => {
  const { email, password, role } = req.body;
  const exists = await UserModel.findOne({ email });
  if (exists) return res.status(400).json({ message: "Utilisateur déjà existant" });
  const hash = await bcrypt.hash(password, 10);
  const user = await UserModel.create({ email, password: hash, role: role ?? "utilisateur" });
  const token = jwt.sign({ id: user._id, role: user.role }, secret, { expiresIn: "7d" });
  res.json({ token });
});

router.post("/login", async (req, res) => {
  const { email, password } = req.body;
  const user = await UserModel.findOne({ email });
  if (!user) return res.status(401).json({ message: "Utilisateur introuvable" });
  const ok = await bcrypt.compare(password, user.password);
  if (!ok) return res.status(401).json({ message: "Mot de passe incorrect" });
  const token = jwt.sign({ id: user._id, role: user.role }, secret, { expiresIn: "7d" });
  res.json({ token, role: user.role });
});

export default router;
