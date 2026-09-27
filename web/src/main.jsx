import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App.jsx";
import { leaveWebIndexOnMobile } from "@/lib/mobileGate.js";
import "./styles/tokens.css";
import "./styles/global.css";

if (!leaveWebIndexOnMobile()) {
  createRoot(document.getElementById("root")).render(
    <StrictMode>
      <App />
    </StrictMode>,
  );
}
