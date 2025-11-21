import { Request, Response, NextFunction } from "express";
import jwt from "jsonwebtoken";

const secret = process.env.JWT_SECRET || "devsecret";

export type AuthRequest = Request & { user?: { id: string; role: string } };

export const authMiddleware = (req: AuthRequest, res: Response, next: NextFunction) => {
  const token = req.headers.authorization?.replace("Bearer ", "");
  if (!token) return res.status(401).json({ message: "Token manquant" });
  try {
    const payload = jwt.verify(token, secret) as { id: string; role: string };
    req.user = payload;
    next();
  } catch (err) {
    return res.status(401).json({ message: "Token invalide" });
  }
};

export const requireRole = (roles: string[]) => {
  return (req: AuthRequest, res: Response, next: NextFunction) => {
    if (!req.user || !roles.includes(req.user.role)) return res.status(403).json({ message: "Accès refusé" });
    next();
  };
};
