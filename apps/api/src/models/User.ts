import mongoose from "mongoose";

export type Role = "admin" | "professeur" | "etudiant" | "invite" | "utilisateur";

const UserSchema = new mongoose.Schema(
  {
    email: { type: String, unique: true, required: true },
    password: { type: String, required: true },
    role: { type: String, default: "utilisateur" },
    name: { type: String },
    progress: { type: Map, of: Number }
  },
  { timestamps: true }
);

export const UserModel = mongoose.model("User", UserSchema);
