import React, { useState } from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { Sidebar, Navbar } from "@cognitolab/ui";
import DashboardPage    from "./pages/Dashboard";
import SimulatorPage    from "./pages/SimulatorPage";
import CoursesPage      from "./pages/CoursesPage";
import ComponentsPage   from "./pages/ComponentsPage";
import ProjectsPage     from "./pages/ProjectsPage";
import RobotsPage       from "./pages/RobotsPage";
import AboutPage        from "./pages/AboutPage";
import CommunityPage    from "./pages/CommunityPage";
import AIAssistantPanel from "./components/AIAssistantPanel";

// ── Icons ──────────────────────────────────────
const IC = {
  Dashboard: () => (
    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" className="w-5 h-5">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8}
        d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z"/>
    </svg>
  ),
  Circuit: () => (
    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" className="w-5 h-5">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8}
        d="M9 3H5a2 2 0 00-2 2v4m6-6h10a2 2 0 012 2v4M9 3v18m0 0h10a2 2 0 002-2V9M9 21H5a2 2 0 01-2-2V9m0 0h18"/>
    </svg>
  ),
  Book: () => (
    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" className="w-5 h-5">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8}
        d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/>
    </svg>
  ),
  Chip: () => (
    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" className="w-5 h-5">
      <rect x="7" y="7" width="10" height="10" rx="1" strokeWidth={1.8} strokeLinecap="round"/>
      <path strokeLinecap="round" strokeWidth={1.8}
        d="M9 7V4M12 7V4M15 7V4M9 20v-3M12 20v-3M15 20v-3M4 9h3M4 12h3M4 15h3M17 9h3M17 12h3M17 15h3"/>
    </svg>
  ),
  Folder: () => (
    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" className="w-5 h-5">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8}
        d="M3 7a2 2 0 012-2h4l2 2h8a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2V7z"/>
    </svg>
  ),
  Robot: () => (
    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" className="w-5 h-5">
      <rect x="8" y="10" width="8" height="7" rx="1" strokeWidth={1.8}/>
      <circle cx="12" cy="6" r="2" strokeWidth={1.8}/>
      <path strokeLinecap="round" strokeWidth={1.8} d="M12 8v2M9 14h.01M15 14h.01M5 14h3M16 14h3"/>
    </svg>
  ),
  Community: () => (
    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" className="w-5 h-5">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8}
        d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"/>
    </svg>
  ),
  Info: () => (
    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" className="w-5 h-5">
      <circle cx="12" cy="12" r="9" strokeWidth={1.8}/>
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M12 8v4M12 16h.01"/>
    </svg>
  ),
};

const menu = [
  { label: "Tableau de bord",  to: "/",          icon: <IC.Dashboard /> },
  { label: "Simulateur",       to: "/simulator", icon: <IC.Circuit   /> },
  { label: "Cours",            to: "/courses",   icon: <IC.Book      /> },
  { label: "Composants",       to: "/components",icon: <IC.Chip      /> },
  { label: "Projets",          to: "/projects",  icon: <IC.Folder    /> },
  { label: "Robotique 3D",     to: "/robots",    icon: <IC.Robot     /> },
  { label: "Communauté",       to: "/community", icon: <IC.Community /> },
  { label: "À propos",         to: "/about",     icon: <IC.Info      /> },
];

// ── Floating Cognito button ────────────────────
const CognitoFloat: React.FC = () => {
  const [open, setOpen] = useState(false);
  return (
    <>
      {open && (
        <div className="cognito-panel">
          <AIAssistantPanel onClose={() => setOpen(false)} />
        </div>
      )}
      <button className="cognito-bubble" onClick={() => setOpen(o => !o)} title="Ouvrir Cognito IA">
        <svg viewBox="0 0 36 36" fill="none" className="w-7 h-7">
          <circle cx="18" cy="18" r="16" stroke="rgba(255,255,255,0.3)" strokeWidth="1.5" fill="none"/>
          <circle cx="18" cy="18" r="6"  stroke="white" strokeWidth="2.5" fill="none"/>
          <line x1="18" y1="4"  x2="18" y2="12" stroke="white" strokeWidth="2" strokeLinecap="round"/>
          <line x1="18" y1="24" x2="18" y2="32" stroke="white" strokeWidth="2" strokeLinecap="round"/>
          <line x1="4"  y1="18" x2="12" y2="18" stroke="white" strokeWidth="2" strokeLinecap="round"/>
          <line x1="24" y1="18" x2="32" y2="18" stroke="white" strokeWidth="2" strokeLinecap="round"/>
          <circle cx="18" cy="4"  r="2.5" fill="white" opacity="0.8"/>
          <circle cx="18" cy="32" r="2.5" fill="white" opacity="0.8"/>
          <circle cx="4"  cy="18" r="2.5" fill="white" opacity="0.8"/>
          <circle cx="32" cy="18" r="2.5" fill="white" opacity="0.8"/>
        </svg>
      </button>
    </>
  );
};

const App: React.FC = () => {
  return (
    <div className="h-screen flex overflow-hidden circuit-bg" style={{ background: "#0A0E1A" }}>
      <Sidebar items={menu} />
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <Navbar />
        <main className="flex-1 overflow-y-auto p-6 relative z-10">
          <Routes>
            <Route path="/"          element={<DashboardPage  />} />
            <Route path="/simulator" element={<SimulatorPage  />} />
            <Route path="/courses"   element={<CoursesPage    />} />
            <Route path="/components"element={<ComponentsPage />} />
            <Route path="/projects"  element={<ProjectsPage   />} />
            <Route path="/robots"    element={<RobotsPage     />} />
            <Route path="/community" element={<CommunityPage  />} />
            <Route path="/about"     element={<AboutPage      />} />
            <Route path="*"          element={<Navigate to="/" />} />
          </Routes>
        </main>
      </div>
      <CognitoFloat />
    </div>
  );
};

export default App;
