import React from "react";
import { Card, Section, ProgressBar, Button } from "@cognitolab/ui";

const courses = [
  {
    id: "arduino-basics",
    title: "Arduino pour débutants",
    sections: 8,
    progress: 72,
    video: "https://www.youtube.com/embed/6mXM-oGggrM"
  },
  {
    id: "esp32-iot",
    title: "ESP32 IoT avancé",
    sections: 10,
    progress: 34,
    video: "https://www.youtube.com/embed/i3z5V3ZrIgY"
  },
  {
    id: "robotique-industrielle",
    title: "Robotique industrielle (UR5/KUKA)",
    sections: 6,
    progress: 20,
    video: "https://www.youtube.com/embed/CNzsPzK0dKk"
  }
];

const CoursesPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <Section
        title="Cours & LMS"
        description="Sections vidéo, PDF, quiz, exercices, progression utilisateur, badges."
      >
        <div className="grid md:grid-cols-3 gap-4">
          {courses.map((course) => (
            <Card key={course.id} title={course.title} subtitle={`${course.sections} sections`}>
              <div className="space-y-3 text-sm text-slate-600">
                <div className="aspect-video rounded-lg overflow-hidden bg-black/5">
                  <iframe
                    src={course.video}
                    className="w-full h-full"
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                    allowFullScreen
                    title={course.title}
                  />
                </div>
                <div>
                  <p>Progression</p>
                  <ProgressBar value={course.progress} />
                  <p className="text-xs text-slate-500 mt-1">{course.progress}% complété</p>
                </div>
                <div className="flex gap-2">
                  <Button size="sm">Continuer</Button>
                  <Button size="sm" variant="ghost">
                    Quiz
                  </Button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      </Section>
    </div>
  );
};

export default CoursesPage;
