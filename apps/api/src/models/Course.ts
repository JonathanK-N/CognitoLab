import mongoose from "mongoose";

const SectionSchema = new mongoose.Schema({
  title: String,
  videoUrl: String,
  pdfUrl: String,
  quiz: [
    {
      question: String,
      options: [String],
      answer: Number
    }
  ]
});

const CourseSchema = new mongoose.Schema(
  {
    title: String,
    description: String,
    sections: [SectionSchema],
    badges: [String],
    finalProject: String
  },
  { timestamps: true }
);

export const CourseModel = mongoose.model("Course", CourseSchema);
