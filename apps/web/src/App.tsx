import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { Sidebar, Navbar, Button } from "@cognitolab/ui";
import DashboardPage from "./pages/Dashboard";
import SimulatorPage from "./pages/SimulatorPage";
import CoursesPage from "./pages/CoursesPage";
import ComponentsPage from "./pages/ComponentsPage";
import ProjectsPage from "./pages/ProjectsPage";
import RobotsPage from "./pages/RobotsPage";

const menu = [
  { label: "Dashboard", to: "/" },
  { label: "Simulateur", to: "/simulator" },
  { label: "Cours", to: "/courses" },
  { label: "Composants", to: "/components" },
  { label: "Projets", to: "/projects" },
  { label: "Robotique", to: "/robots" }
];

const App: React.FC = () => {
  return (
    <div className="h-screen flex overflow-hidden">
      <Sidebar
        items={menu}
        footer={<Button variant="secondary" size="sm">Mode PWA</Button>}
      />
      <div className="flex-1 flex flex-col min-w-0">
        <Navbar right={<Button size="sm">Profil</Button>} />
        <main className="flex-1 overflow-y-auto bg-slate-50 p-6">
          <Routes>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/simulator" element={<SimulatorPage />} />
            <Route path="/courses" element={<CoursesPage />} />
            <Route path="/components" element={<ComponentsPage />} />
            <Route path="/projects" element={<ProjectsPage />} />
            <Route path="/robots" element={<RobotsPage />} />
            <Route path="*" element={<Navigate to="/" />} />
          </Routes>
        </main>
      </div>
    </div>
  );
};

export default App;
