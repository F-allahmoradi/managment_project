import { useId } from "react";
import Pedestal from "./Pedestal.jsx";
import { BADGE_ICONS, FIGURE_ICONS, CalendarNetwork, TargetDart } from "@/components/icons/index.jsx";

const THEME_CLASS = {
  meetings: "feature-card-meetings",
  reports: "feature-card-reports",
  followups: "feature-card-followups",
  members: "feature-card-members",
  notifications: "feature-card-notifications",
};

const PARTICLES = [
  { top: "7%", left: "12%", size: 6, delay: "0s" },
  { top: "16%", left: "88%", size: 4, delay: "2.4s" },
  { top: "38%", left: "6%", size: 5, delay: "4.1s" },
  { top: "48%", left: "92%", size: 8, delay: "1.2s" },
  { top: "70%", left: "14%", size: 4, delay: "3.3s" },
  { top: "24%", left: "78%", size: 5, delay: "5.5s" },
  { top: "82%", left: "86%", size: 7, delay: "6.2s" },
  { top: "58%", left: "8%", size: 5, delay: "0.8s" },
];

export default function FeatureCard({ feature }) {
  const uid = useId().replace(/:/g, "");
  const Figure = FIGURE_ICONS[feature.figure];
  const Badge = BADGE_ICONS[feature.badge];
  const descriptionLines = String(feature.description).split("\n");
  const isMeetings = feature.id === "meetings";
  const isFollowups = feature.id === "followups";
  const isReports = feature.id === "reports";
  const isMembers = feature.id === "members";
  const isNotifications = feature.id === "notifications";
  const themeClass = THEME_CLASS[feature.id];
  const cardClass = ["feature-card", themeClass].filter(Boolean).join(" ");

  return (
    <button
      type="button"
      className={cardClass}
      data-feature={feature.id}
      style={{ "--card-rgb": feature.rgb, "--card-color": feature.color }}
    >
      <span className="feature-card-glow" aria-hidden="true" />
      <span className="feature-local-grid" aria-hidden="true" />
      <span className="feature-horizon" aria-hidden="true" />

      {PARTICLES.map((particle, index) => (
        <span
          key={index}
          className="feature-particle"
          aria-hidden="true"
          style={{
            top: particle.top,
            left: particle.left,
            width: particle.size,
            height: particle.size,
            animationDelay: particle.delay,
          }}
        />
      ))}

      <div className="feature-podium">
        <span className="feature-glow" aria-hidden="true" />
        <span className="feature-glow feature-glow-inner" aria-hidden="true" />
        {isFollowups || isMembers || isNotifications ? (
          <span className="feature-glow feature-glow-outer" aria-hidden="true" />
        ) : null}
        <span className="feature-cone" aria-hidden="true" />
        <span className="feature-beam" aria-hidden="true" />

        <div className="feature-stage">
          <Pedestal color={feature.color} uid={uid} />
        </div>

        <div className="feature-figure">
          {isFollowups || isReports || isMembers || isNotifications ? (
            <>
              <span className="glass-panel glass-panel-back" />
              <span className="glass-panel glass-panel-mid" />
            </>
          ) : null}
          {isMeetings ? <CalendarNetwork gid={uid} /> : null}
          {isFollowups ? <TargetDart gid={uid} /> : null}
          <Figure gid={uid} />
          {feature.count ? <span className="feature-count">{feature.count}</span> : null}
        </div>

        <div className="feature-copy">
          <h3>{feature.title}</h3>
          <p>
            {descriptionLines.map((line) => (
              <span key={line} className="feature-desc-line">
                {line}
              </span>
            ))}
          </p>
        </div>

        <span className="feature-badge neon-ring">
          <Badge />
        </span>
      </div>
    </button>
  );
}
