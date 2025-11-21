import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Button, Card } from "@cognitolab/ui";
import "./index.css";

const Home = () => (
  <div className="p-4 space-y-3">
    <Card title="CognitoLab Mobile">
      <p className="text-sm text-slate-600 mb-3">
        Version PWA/mobile légère : progression cours, mini-simulateur et notifications.
      </p>
      <Button size="sm">Ouvrir simulateur</Button>
    </Card>
  </div>
);

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
      </Routes>
    </BrowserRouter>
  </React.StrictMode>
);
