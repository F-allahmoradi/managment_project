import { FEATURES } from "@/data/dashboard.js";
import FeatureCard from "./FeatureCard.jsx";
import "./platforms.css";

export default function FeatureGrid() {
  return (
    <section className="feature-grid-wrap">
      <div className="feature-floor" aria-hidden="true">
        <span className="feature-floor-glow" />
        <span className="feature-floor-plate" />
        <span className="feature-floor-ring feature-floor-ring-mid" />
        <span className="feature-floor-ring feature-floor-ring-outer" />
        <span className="feature-floor-ring feature-floor-ring-inner" />
      </div>
      <div className="feature-grid">
        {FEATURES.map((feature) => (
          <FeatureCard key={feature.id} feature={feature} />
        ))}
      </div>
    </section>
  );
}
