import mongoose from "mongoose";

const ProjectSchema = new mongoose.Schema(
  {
    title: String,
    board: String,
    code: String,
    owner: { type: mongoose.Schema.Types.ObjectId, ref: "User" },
    shared: { type: Boolean, default: false },
    files: [{ path: String, content: String }]
  },
  { timestamps: true }
);

export const ProjectModel = mongoose.model("Project", ProjectSchema);
