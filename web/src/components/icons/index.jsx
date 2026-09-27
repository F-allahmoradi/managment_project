function strokeProps(color = "currentColor") {
  return {
    fill: "none",
    stroke: color,
    strokeWidth: 2,
    strokeLinecap: "round",
    strokeLinejoin: "round",
  };
}

export function NetworkLogo() {
  return (
    <svg className="brand-logo" viewBox="0 0 50 50" aria-hidden="true">
      <defs>
        <linearGradient id="logo-g" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#00b4ff" />
          <stop offset="100%" stopColor="#0066cc" />
        </linearGradient>
        <filter id="logo-glow" x="-50%" y="-50%" width="200%" height="200%">
          <feGaussianBlur stdDeviation="1.6" result="b" />
          <feMerge>
            <feMergeNode in="b" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>
      <circle cx="25" cy="25" r="18" fill="none" stroke="url(#logo-g)" strokeWidth="1.4" opacity="0.7" />
      <circle cx="25" cy="25" r="10" fill="none" stroke="#00b4ff" strokeWidth="1.1" opacity="0.5" />
      <g filter="url(#logo-glow)" stroke="#00b4ff" strokeWidth="1.3">
        <line x1="25" y1="7" x2="25" y2="43" />
        <line x1="8" y1="18" x2="42" y2="32" />
        <line x1="8" y1="32" x2="42" y2="18" />
      </g>
      <circle cx="25" cy="8" r="2.4" fill="#00b4ff" />
      <circle cx="25" cy="42" r="2.4" fill="#7ee8ff" />
      <circle cx="9" cy="18" r="2.2" fill="#00b4ff" />
      <circle cx="41" cy="18" r="2.2" fill="#bf00ff" />
      <circle cx="9" cy="32" r="2.2" fill="#00ffcc" />
      <circle cx="41" cy="32" r="2.2" fill="#00b4ff" />
      <circle cx="25" cy="25" r="3.4" fill="#00b4ff" />
    </svg>
  );
}

export function ChartIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" aria-hidden="true">
      <path d="M3 16 V9 M8 16 V5 M13 16 V8 M18 16 V3" {...strokeProps("currentColor")} />
    </svg>
  );
}

export function UserSilhouette() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" aria-hidden="true">
      <circle cx="12" cy="8" r="4" fill="#ffffff" />
      <path d="M4.2 20 C5.2 15.8 8 13.5 12 13.5 C16 13.5 18.8 15.8 19.8 20 Z" fill="#ffffff" />
    </svg>
  );
}

export function HeaderBellIcon() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" aria-hidden="true">
      <path
        d="M6 8a6 6 0 1 1 12 0c0 7 3 9 3 9H3s3-2 3-9"
        {...strokeProps("currentColor")}
      />
      <path d="M10.3 21a1.94 1.94 0 0 0 3.4 0" {...strokeProps("currentColor")} />
    </svg>
  );
}

export function GearIcon() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" aria-hidden="true">
      <circle cx="12" cy="12" r="3.2" {...strokeProps("currentColor")} />
      <path
        d="M12 3.2 L13.2 3.4 L13.5 6.2 L15 6.7 L17.2 5.1 L18.5 6.4 L16.9 8.6 L17.4 10.1 L20.2 10.4 L20.4 12 L20.2 13.6 L17.4 13.9 L16.9 15.4 L18.5 17.6 L17.2 18.9 L15 17.3 L13.5 17.8 L13.2 20.6 L12 20.8 L10.8 20.6 L10.5 17.8 L9 17.3 L6.8 18.9 L5.5 17.6 L7.1 15.4 L6.6 13.9 L3.8 13.6 L3.6 12 L3.8 10.4 L6.6 10.1 L7.1 8.6 L5.5 6.4 L6.8 5.1 L9 6.7 L10.5 6.2 L10.8 3.4 Z"
        {...strokeProps("currentColor")}
      />
    </svg>
  );
}

export function FullscreenIcon() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" aria-hidden="true">
      <path d="M4 9 V4 H9 M15 4 H20 V9 M20 15 V20 H15 M9 20 H4 V15" {...strokeProps("currentColor")} />
    </svg>
  );
}

export function CalendarIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" aria-hidden="true">
      <rect x="3" y="4.5" width="14" height="12.5" rx="2" {...strokeProps("currentColor")} />
      <path d="M3 8 H17 M7 3 V6 M13 3 V6" {...strokeProps("currentColor")} />
    </svg>
  );
}

export function ChevronDownIcon({ className }) {
  return (
    <svg className={className} width="20" height="20" viewBox="0 0 20 20" aria-hidden="true">
      <path d="M5 7.5 L10 12.5 L15 7.5" {...strokeProps("currentColor")} />
    </svg>
  );
}

export function FileTabIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true">
      <path d="M4 2.5 H9 L12.5 6 V13.5 H4 Z" {...strokeProps("currentColor")} />
      <path d="M9 2.5 V6 H12.5" {...strokeProps("currentColor")} />
    </svg>
  );
}

export function VideoRecIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 14 14" aria-hidden="true">
      <rect x="1.5" y="3.5" width="7.5" height="7" rx="1.4" {...strokeProps("currentColor")} />
      <path d="M9 6 L12.5 4.2 V9.8 L9 8 Z" {...strokeProps("currentColor")} />
    </svg>
  );
}

export function MenuIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 18 18" aria-hidden="true">
      <path d="M3 5h12M3 9h12M3 13h12" {...strokeProps("#00b4ff")} />
    </svg>
  );
}

export function ShieldCheckIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" aria-hidden="true">
      <path d="M10 2.2 L16.5 5 V10.2 C16.5 14 13.6 16.8 10 17.8 C6.4 16.8 3.5 14 3.5 10.2 V5 Z" {...strokeProps("#00b4ff")} />
      <path d="M7 10.1 L9.1 12.2 L13.2 7.8" {...strokeProps("#00b4ff")} />
    </svg>
  );
}

export function TextTabIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true">
      <rect x="3" y="2.5" width="10" height="11" rx="1.6" {...strokeProps("currentColor")} />
      <path d="M5.5 6h5M5.5 8.5h5M5.5 11h3" {...strokeProps("currentColor")} />
    </svg>
  );
}

export function VideoTabIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true">
      <rect x="2" y="4" width="8.5" height="8" rx="1.5" {...strokeProps("currentColor")} />
      <path d="M10.5 7 L14 5.2 V10.8 L10.5 9 Z" {...strokeProps("currentColor")} />
    </svg>
  );
}

export function AudioTabIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true">
      <rect x="6" y="3" width="4" height="7" rx="2" {...strokeProps("currentColor")} />
      <path d="M4.5 8.2 A3.5 3.5 0 0 0 11.5 8.2 M8 10.2 V13" {...strokeProps("currentColor")} />
    </svg>
  );
}

export function ClipIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 14 14" aria-hidden="true">
      <path d="M8.6 3.4 L4.2 7.8 A2.1 2.1 0 1 0 7.2 10.8 L12 6" {...strokeProps("currentColor")} />
    </svg>
  );
}

export function MicIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 14 14" aria-hidden="true">
      <rect x="5.2" y="2" width="3.6" height="6" rx="1.8" {...strokeProps("currentColor")} />
      <path d="M3.6 6.6 A3.4 3.4 0 0 0 10.4 6.6 M7 10.1 V12.2" {...strokeProps("currentColor")} />
    </svg>
  );
}

export function ImageIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 14 14" aria-hidden="true">
      <rect x="2" y="3" width="10" height="8" rx="1.4" {...strokeProps("currentColor")} />
      <circle cx="5" cy="6" r="1" fill="currentColor" />
      <path d="M3.4 10 L6.2 7.6 L8.1 9.2 L10.8 6.6 L11.8 10" {...strokeProps("currentColor")} />
    </svg>
  );
}

export function SendIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 18 18" aria-hidden="true">
      <path d="M3.2 9 L14.8 3.4 L10.4 14.6 L8.6 9.8 Z" fill="#fff" />
    </svg>
  );
}

export function ArrowLeftIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true">
      <path d="M11 8 H5 M7 5 L4 8 L7 11" {...strokeProps("currentColor")} />
    </svg>
  );
}

export function DotsIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true">
      <circle cx="8" cy="3.5" r="1.2" fill="currentColor" />
      <circle cx="8" cy="8" r="1.2" fill="currentColor" />
      <circle cx="8" cy="12.5" r="1.2" fill="currentColor" />
    </svg>
  );
}

export function KindIcon({ kind }) {
  if (kind === "video") {
    return (
      <svg width="20" height="20" viewBox="0 0 20 20" aria-hidden="true">
        <rect x="2.5" y="5" width="10" height="10" rx="2" fill="#fff" opacity="0.92" />
        <path d="M13 8 L17.5 5.8 V14.2 L13 12 Z" fill="#fff" />
      </svg>
    );
  }
  if (kind === "audio") {
    return (
      <svg width="20" height="20" viewBox="0 0 20 20" aria-hidden="true">
        <rect x="7.2" y="3.5" width="5.6" height="8.4" rx="2.8" fill="#fff" />
        <path d="M4.6 9.2 A5.4 5.4 0 0 0 15.4 9.2 M10 13.2 V16.4" {...strokeProps("#fff")} />
      </svg>
    );
  }
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" aria-hidden="true">
      <rect x="4" y="3" width="10.5" height="14" rx="1.8" fill="#fff" />
      <path d="M7 8h5.2M7 11h5.2M7 14h3.4" stroke="rgba(0,40,70,0.45)" strokeWidth="1.3" />
    </svg>
  );
}

export function TAB_ICONS() {
  return { text: TextTabIcon, video: VideoTabIcon, audio: AudioTabIcon, file: FileTabIcon };
}

export function ACTION_ICONS() {
  return { clip: ClipIcon, mic: MicIcon, image: ImageIcon, video: VideoRecIcon };
}

export function FolderBadge() {
  return (
    <svg width="50" height="50" viewBox="0 0 50 50" aria-hidden="true">
      <rect
        x="11"
        y="18"
        width="28"
        height="20"
        rx="4"
        fill="none"
        stroke="currentColor"
        strokeWidth="3"
        strokeLinejoin="round"
      />
      <path
        d="M20 18 V14.5 C20 12.6 21.6 11 23.5 11 H26.5 C28.4 11 30 12.6 30 14.5 V18"
        fill="none"
        stroke="currentColor"
        strokeWidth="3"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export function CalendarBadge() {
  const cells = [0, 1, 2].flatMap((row) =>
    [0, 1, 2].map((col) => ({ key: `${row}-${col}`, x: 12 + col * 11, y: 26 + row * 9 })),
  );

  return (
    <svg width="50" height="50" viewBox="0 0 55 55" aria-hidden="true">
      <rect
        x="5"
        y="10"
        width="45"
        height="40"
        rx="4"
        fill="none"
        stroke="currentColor"
        strokeWidth="3"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path d="M5 22 h45" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
      <circle cx="18" cy="8" r="4" fill="none" stroke="currentColor" strokeWidth="2" />
      <circle cx="37" cy="8" r="4" fill="none" stroke="currentColor" strokeWidth="2" />
      {cells.map((cell) => (
        <rect
          key={cell.key}
          x={cell.x}
          y={cell.y}
          width="8"
          height="7"
          rx="1"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.6"
        />
      ))}
    </svg>
  );
}

export function DocumentBadge() {
  return (
    <svg width="50" height="50" viewBox="0 0 55 55" aria-hidden="true">
      <rect
        x="7.5"
        y="3.5"
        width="40"
        height="48"
        rx="4"
        fill="none"
        stroke="currentColor"
        strokeWidth="3"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M35.5 3.5 V11.5 C35.5 13.7 37.3 15.5 39.5 15.5 H47.5"
        fill="none"
        stroke="currentColor"
        strokeWidth="3"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M16 22 h22 M16 30 h16 M16 38 h19 M16 46 h12"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
      />
    </svg>
  );
}

export function UsersBadge() {
  return (
    <svg width="24" height="24" viewBox="0 0 55 55" aria-hidden="true">
      <g fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="16" cy="22" r="6" strokeWidth="2" />
        <path d="M7 43 C8.2 35.5 11.5 32 16 32 C20.2 32 23 35 24.2 41" strokeWidth="2" />
        <circle cx="39" cy="22" r="6" strokeWidth="2" />
        <path d="M30.8 41 C32 35 35 32 39 32 C43.5 32 47 35.5 48 43" strokeWidth="2" />
        <circle cx="27.5" cy="16.5" r="8" strokeWidth="2.5" />
        <path d="M14 44 C15.2 34 20.2 29 27.5 29 C34.8 29 39.8 34 41 44" strokeWidth="2.5" />
      </g>
    </svg>
  );
}

export function TargetBadge() {
  return (
    <svg width="50" height="50" viewBox="0 0 60 60" aria-hidden="true">
      <circle
        cx="30"
        cy="30"
        r="22"
        fill="none"
        stroke="currentColor"
        strokeWidth="2.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <circle cx="30" cy="30" r="15" fill="none" stroke="currentColor" strokeWidth="2" />
      <circle cx="30" cy="30" r="8" fill="none" stroke="currentColor" strokeWidth="1.5" />
      <circle cx="30" cy="30" r="3" fill="currentColor" />
      <line x1="45" y1="15" x2="31" y2="29" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
      <polygon points="30,30 34.8,25.4 27.6,27.8" fill="currentColor" />
      <line x1="45" y1="15" x2="50.5" y2="10" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
      <line x1="45" y1="15" x2="51.4" y2="19.2" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
    </svg>
  );
}

export function BellBadge() {
  return (
    <svg width="50" height="50" viewBox="0 0 24 24" aria-hidden="true">
      <path
        d="M6 8a6 6 0 1 1 12 0c0 7 3 9 3 9H3s3-2 3-9"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M10.3 21a1.94 1.94 0 0 0 3.4 0"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
      />
    </svg>
  );
}

export const BADGE_ICONS = {
  folder: FolderBadge,
  calendar: CalendarBadge,
  document: DocumentBadge,
  users: UsersBadge,
  target: TargetBadge,
  bell: BellBadge,
};

export function DocumentsFigure({ gid }) {
  return (
    <svg width="72" height="72" viewBox="0 0 72 72" aria-hidden="true">
      <defs>
        <linearGradient id={`${gid}-back`} x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#0077b6" />
          <stop offset="100%" stopColor="#005f8a" />
        </linearGradient>
        <linearGradient id={`${gid}-mid`} x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#0096c7" />
          <stop offset="100%" stopColor="#0077b6" />
        </linearGradient>
        <linearGradient id={`${gid}-front`} x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#00b4d8" />
          <stop offset="100%" stopColor="#0096c7" />
        </linearGradient>
        <radialGradient id={`${gid}-badge`} cx="50%" cy="38%" r="62%">
          <stop offset="0%" stopColor="#7ee8ff" />
          <stop offset="55%" stopColor="#00b4d8" />
          <stop offset="100%" stopColor="#0096c7" />
        </radialGradient>
        <filter id={`${gid}-glow`} x="-50%" y="-50%" width="200%" height="200%">
          <feGaussianBlur stdDeviation="1.4" result="b" />
          <feMerge>
            <feMergeNode in="b" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>
      <rect x="6" y="16" width="38" height="42" rx="10" fill={`url(#${gid}-back)`} opacity="0.7" transform="rotate(-8 25 37)" />
      <rect x="14" y="12" width="40" height="44" rx="10" fill={`url(#${gid}-mid)`} opacity="0.85" transform="rotate(-4 34 34)" />
      <rect x="22" y="8" width="42" height="46" rx="11" fill={`url(#${gid}-front)`} />
      <rect x="22" y="8" width="42" height="46" rx="11" fill="rgba(255,255,255,0.08)" />
      <rect x="30" y="18" width="22" height="3.5" rx="1.6" fill="rgba(255,255,255,0.32)" />
      <rect x="30" y="26" width="16" height="3.5" rx="1.6" fill="rgba(255,255,255,0.24)" />
      <circle
        cx="50"
        cy="42"
        r="11"
        fill={`url(#${gid}-badge)`}
        stroke="rgba(255,255,255,0.85)"
        strokeWidth="1.7"
      />
      <path
        d="M45.2 42.2 L48.6 45.6 L55.6 38.2"
        fill="none"
        stroke="#fff"
        strokeWidth="2.6"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export function CalendarNetwork({ gid }) {
  const nodes = [
    { x: 130, y: 16 },
    { x: 70, y: 42 },
    { x: 118, y: 78 },
    { x: 28, y: 58 },
    { x: 48, y: 18 },
  ];
  const links = [
    [0, 1],
    [1, 2],
    [1, 3],
    [0, 4],
    [4, 1],
  ];

  return (
    <svg className="feature-network" viewBox="0 0 150 150" aria-hidden="true">
      <defs>
        <radialGradient id={`${gid}-node`} cx="40%" cy="35%" r="65%">
          <stop offset="0%" stopColor="rgba(220, 180, 255, 0.95)" />
          <stop offset="100%" stopColor="rgba(160, 100, 240, 0.4)" />
        </radialGradient>
        <filter id={`${gid}-node-glow`} x="-80%" y="-80%" width="260%" height="260%">
          <feGaussianBlur stdDeviation="1.6" result="b" />
          <feMerge>
            <feMergeNode in="b" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>
      <g fill="none" stroke="rgba(180, 120, 255, 0.42)" strokeWidth="1.5" strokeDasharray="4 4">
        {links.map(([a, b]) => (
          <line
            key={`${a}-${b}`}
            className="network-line"
            x1={nodes[a].x}
            y1={nodes[a].y}
            x2={nodes[b].x}
            y2={nodes[b].y}
          />
        ))}
      </g>
      <g>
        {nodes.map((node, index) => (
          <circle
            key={`${node.x}-${node.y}`}
            className="network-node"
            cx={node.x}
            cy={node.y}
            r="6"
            fill={`url(#${gid}-node)`}
            style={{ animationDelay: `${index * 0.35}s` }}
          />
        ))}
      </g>
    </svg>
  );
}

export function CalendarFigure({ gid }) {
  const cells = [0, 1, 2].flatMap((row) =>
    [0, 1, 2].map((col) => ({
      key: `${row}-${col}`,
      x: 16 + col * 15,
      y: 36 + row * 14,
    })),
  );

  return (
    <svg width="92" height="92" viewBox="0 0 92 92" aria-hidden="true">
      <defs>
        <linearGradient id={`${gid}-cal`} x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="rgba(160, 80, 255, 0.72)" />
          <stop offset="100%" stopColor="rgba(120, 50, 220, 0.38)" />
        </linearGradient>
        <linearGradient id={`${gid}-head`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="rgba(200, 150, 255, 0.72)" />
          <stop offset="100%" stopColor="rgba(140, 80, 230, 0.38)" />
        </linearGradient>
        <linearGradient id={`${gid}-ring`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="rgba(200, 150, 255, 0.75)" />
          <stop offset="100%" stopColor="rgba(160, 100, 240, 0.45)" />
        </linearGradient>
        <linearGradient id={`${gid}-cell`} x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="rgba(200, 150, 255, 0.55)" />
          <stop offset="100%" stopColor="rgba(160, 100, 240, 0.22)" />
        </linearGradient>
        <radialGradient id={`${gid}-clock`} cx="50%" cy="42%" r="58%">
          <stop offset="0%" stopColor="rgba(220, 180, 255, 0.42)" />
          <stop offset="100%" stopColor="rgba(160, 100, 240, 0.16)" />
        </radialGradient>
        <radialGradient id={`${gid}-face`} cx="50%" cy="40%" r="62%">
          <stop offset="0%" stopColor="rgba(100, 50, 200, 0.55)" />
          <stop offset="100%" stopColor="rgba(60, 20, 150, 0.28)" />
        </radialGradient>
        <filter id={`${gid}-glow`} x="-45%" y="-45%" width="190%" height="190%">
          <feGaussianBlur stdDeviation="1.5" result="b" />
          <feMerge>
            <feMergeNode in="b" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
        <clipPath id={`${gid}-body`}>
          <rect x="6" y="14" width="64" height="58" rx="12" />
        </clipPath>
      </defs>

      <g transform="rotate(-5 38 44)">
        <rect
          x="24"
          y="2"
          width="9"
          height="16"
          rx="4.5"
          fill={`url(#${gid}-ring)`}
          stroke="rgba(220, 180, 255, 0.55)"
          strokeWidth="1"
        />
        <rect
          x="47"
          y="2"
          width="9"
          height="16"
          rx="4.5"
          fill={`url(#${gid}-ring)`}
          stroke="rgba(220, 180, 255, 0.55)"
          strokeWidth="1"
        />
        <rect
          x="6"
          y="14"
          width="64"
          height="58"
          rx="12"
          fill={`url(#${gid}-cal)`}
          stroke="rgba(180, 120, 255, 0.62)"
          strokeWidth="1.8"
        />
        <rect
          x="6"
          y="14"
          width="64"
          height="14"
          fill={`url(#${gid}-head)`}
          clipPath={`url(#${gid}-body)`}
        />
        <path d="M6 28 H70" stroke="rgba(180, 120, 255, 0.4)" strokeWidth="1" />
        {cells.map((cell) => (
          <rect
            key={cell.key}
            x={cell.x}
            y={cell.y}
            width="11"
            height="10"
            rx="2.4"
            fill={`url(#${gid}-cell)`}
            stroke="rgba(200, 150, 255, 0.5)"
            strokeWidth="0.9"
          />
        ))}
      </g>

      <g transform="translate(66 64)">
        <circle
          r="22"
          fill="rgba(28, 8, 64, 0.72)"
          stroke="rgba(220, 180, 255, 0.9)"
          strokeWidth="2.8"
        />
        <circle
          r="17"
          fill={`url(#${gid}-face)`}
          stroke="rgba(200, 150, 255, 0.4)"
          strokeWidth="0.9"
        />
        <circle cx="0" cy="-13.2" r="1.4" fill="rgba(255,255,255,0.78)" />
        <circle cx="13.2" cy="0" r="1.4" fill="rgba(255,255,255,0.78)" />
        <circle cx="0" cy="13.2" r="1.4" fill="rgba(255,255,255,0.78)" />
        <circle cx="-13.2" cy="0" r="1.4" fill="rgba(255,255,255,0.78)" />
        <line x1="0" y1="0" x2="0" y2="-10" stroke="rgba(255,255,255,0.95)" strokeWidth="2.4" strokeLinecap="round" />
        <line x1="0" y1="0" x2="12" y2="0" stroke="rgba(255,255,255,0.95)" strokeWidth="1.8" strokeLinecap="round" />
        <circle r="2.4" fill="#fff" />
      </g>
    </svg>
  );
}

export function ChartDocFigure({ gid }) {
  const bars = [
    { x: 18, h: 22, delay: "0.05s" },
    { x: 29, h: 34, delay: "0.12s" },
    { x: 40, h: 18, delay: "0.2s" },
    { x: 51, h: 38, delay: "0.28s" },
    { x: 62, h: 26, delay: "0.36s" },
  ];
  const barBase = 108;
  const pieCx = 86;
  const pieCy = 78;
  const pieR = 16;
  const pie = (start, end) => {
    const polar = (deg) => {
      const rad = ((deg - 90) * Math.PI) / 180;
      return [pieCx + pieR * Math.cos(rad), pieCy + pieR * Math.sin(rad)];
    };
    const [x1, y1] = polar(start);
    const [x2, y2] = polar(end);
    return `M ${pieCx} ${pieCy} L ${x1.toFixed(2)} ${y1.toFixed(2)} A ${pieR} ${pieR} 0 0 1 ${x2.toFixed(2)} ${y2.toFixed(2)} Z`;
  };

  return (
    <svg className="feature-report-doc" width="108" height="116" viewBox="0 0 140 152" overflow="visible" aria-hidden="true">
      <defs>
        <linearGradient id={`${gid}-doc`} x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="rgba(20, 90, 70, 0.92)" />
          <stop offset="100%" stopColor="rgba(0, 70, 52, 0.78)" />
        </linearGradient>
        <linearGradient id={`${gid}-head`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="rgba(180, 255, 220, 0.78)" />
          <stop offset="100%" stopColor="rgba(0, 204, 102, 0.42)" />
        </linearGradient>
        <linearGradient id={`${gid}-line`} x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%" stopColor="rgba(230, 255, 245, 0.92)" />
          <stop offset="100%" stopColor="rgba(0, 255, 136, 0.45)" />
        </linearGradient>
        <linearGradient id={`${gid}-bar`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#ffffff" />
          <stop offset="100%" stopColor="#00ff88" />
        </linearGradient>
        <linearGradient id={`${gid}-pen`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#3dff9a" />
          <stop offset="100%" stopColor="#00994d" />
        </linearGradient>
        <linearGradient id={`${gid}-cap`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#e7fff3" />
          <stop offset="100%" stopColor="#00ff88" />
        </linearGradient>
        <radialGradient id={`${gid}-shine`} cx="24%" cy="16%" r="68%">
          <stop offset="0%" stopColor="rgba(255,255,255,0.38)" />
          <stop offset="100%" stopColor="rgba(255,255,255,0)" />
        </radialGradient>
        <filter id={`${gid}-glow`} x="-45%" y="-45%" width="190%" height="190%">
          <feGaussianBlur stdDeviation="1.5" result="b" />
          <feMerge>
            <feMergeNode in="b" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>

      <g transform="rotate(-4 58 66)">
        <rect
          x="10"
          y="8"
          width="96"
          height="116"
          rx="14"
          fill={`url(#${gid}-doc)`}
          stroke="rgba(180, 255, 220, 0.85)"
          strokeWidth="2.2"
        />
        <rect x="10" y="8" width="96" height="116" rx="14" fill={`url(#${gid}-shine)`} />
        <rect x="10" y="8" width="96" height="22" rx="14" fill={`url(#${gid}-head)`} />
        <rect x="10" y="20" width="96" height="10" fill={`url(#${gid}-head)`} />
        <path d="M10 30 H106" stroke="rgba(230, 255, 245, 0.45)" strokeWidth="1.2" />
        <path
          d="M82 8 V18 C82 21.3 84.7 24 88 24 H106"
          fill="none"
          stroke="rgba(230, 255, 245, 0.7)"
          strokeWidth="1.8"
          strokeLinejoin="round"
        />

        <rect x="22" y="40" width="58" height="5.5" rx="2.6" fill={`url(#${gid}-line)`} />
        <rect x="22" y="51" width="48" height="5.5" rx="2.6" fill={`url(#${gid}-line)`} opacity="0.9" />
        <rect x="22" y="62" width="36" height="5.5" rx="2.6" fill={`url(#${gid}-line)`} opacity="0.8" />

        {bars.map((bar) => (
          <rect
            key={bar.x}
            className="chart-bar"
            x={bar.x}
            y={barBase - bar.h}
            width="9"
            height={bar.h}
            rx="2.4"
            fill={`url(#${gid}-bar)`}
            stroke="rgba(230, 255, 245, 0.55)"
            strokeWidth="0.7"
            style={{ animationDelay: bar.delay }}
          />
        ))}

        <path d={pie(0, 120)} fill="#b8ffd9" />
        <path d={pie(120, 240)} fill="#00e57a" />
        <path d={pie(240, 360)} fill="#007a52" />
        <circle
          cx={pieCx}
          cy={pieCy}
          r={pieR}
          fill="none"
          stroke="rgba(230, 255, 245, 0.9)"
          strokeWidth="1.8"
        />
        <circle cx={pieCx} cy={pieCy} r="6" fill="rgba(0, 32, 26, 0.95)" />
      </g>

      <g transform="translate(108 82) rotate(32)">
        <rect x="-1" y="-10" width="11" height="10" rx="2.8" fill={`url(#${gid}-cap)`} />
        <rect x="7.4" y="-7" width="2.4" height="15" rx="1.1" fill="rgba(255,255,255,0.85)" />
        <rect x="0" y="0" width="9" height="38" rx="4.5" fill={`url(#${gid}-pen)`} />
        <rect x="1.6" y="4" width="2" height="28" rx="1" fill="rgba(255,255,255,0.35)" />
        <polygon points="-0.6,38 9.6,38 4.5,50" fill="#e7fff3" />
        <polygon points="1.4,38 7.6,38 4.5,46" fill="#00ff88" />
      </g>
    </svg>
  );
}

export function UsersFigure({ gid }) {
  const gear =
    "M 0 -13.5 L 2.32 -13.3 L 2.35 -7.65 L 3.74 -7.07 L 7.76 -11.05 L 9.55 -9.55 L 11.05 -7.76 L 7.07 -3.74 L 7.65 -2.35 L 13.3 -2.32 L 13.5 0 L 13.3 2.32 L 7.65 2.35 L 7.07 3.74 L 11.05 7.76 L 9.55 9.55 L 7.76 11.05 L 3.74 7.07 L 2.35 7.65 L 2.32 13.3 L 0 13.5 L -2.32 13.3 L -2.35 7.65 L -3.74 7.07 L -7.76 11.05 L -9.55 9.55 L -11.05 7.76 L -7.07 3.74 L -7.65 2.35 L -13.3 2.32 L -13.5 0 L -13.3 -2.32 L -7.65 -2.35 L -7.07 -3.74 L -11.05 -7.76 L -9.55 -9.55 L -7.76 -11.05 L -3.74 -7.07 L -2.35 -7.65 L -2.32 -13.3 Z";

  return (
    <svg width="92" height="92" viewBox="0 0 92 92" overflow="visible" aria-hidden="true">
      <defs>
        <radialGradient id={`${gid}-head-front`} cx="38%" cy="32%" r="68%">
          <stop offset="0%" stopColor="rgba(255, 160, 255, 0.95)" />
          <stop offset="55%" stopColor="rgba(255, 0, 255, 0.82)" />
          <stop offset="100%" stopColor="rgba(191, 0, 255, 0.62)" />
        </radialGradient>
        <radialGradient id={`${gid}-head-back`} cx="40%" cy="30%" r="70%">
          <stop offset="0%" stopColor="rgba(255, 120, 255, 0.72)" />
          <stop offset="100%" stopColor="rgba(153, 0, 255, 0.48)" />
        </radialGradient>
        <linearGradient id={`${gid}-body-front`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="rgba(191, 0, 255, 0.78)" />
          <stop offset="100%" stopColor="rgba(153, 0, 255, 0.42)" />
        </linearGradient>
        <linearGradient id={`${gid}-body-back`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="rgba(191, 0, 255, 0.58)" />
          <stop offset="100%" stopColor="rgba(153, 0, 255, 0.32)" />
        </linearGradient>
        <radialGradient id={`${gid}-gear`} cx="40%" cy="35%" r="70%">
          <stop offset="0%" stopColor="rgba(255, 80, 180, 0.92)" />
          <stop offset="100%" stopColor="rgba(191, 0, 255, 0.55)" />
        </radialGradient>
        <radialGradient id={`${gid}-orb`} cx="40%" cy="35%" r="65%">
          <stop offset="0%" stopColor="rgba(255, 180, 255, 0.95)" />
          <stop offset="100%" stopColor="rgba(191, 0, 255, 0.4)" />
        </radialGradient>
        <filter id={`${gid}-glow`} x="-55%" y="-55%" width="210%" height="210%">
          <feGaussianBlur stdDeviation="1.6" result="b" />
          <feMerge>
            <feMergeNode in="b" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>

      <circle className="members-spark" cx="20" cy="12" r="4.5" fill={`url(#${gid}-orb)`} />
      <circle className="members-spark" cx="48" cy="7" r="6" fill={`url(#${gid}-orb)`} />
      <circle className="members-spark" cx="74" cy="14" r="4" fill={`url(#${gid}-orb)`} />

      <g opacity="0.72" transform="translate(6 26) scale(0.88)">
        <circle
          cx="16"
          cy="14"
          r="13"
          fill={`url(#${gid}-head-back)`}
          stroke="rgba(255, 150, 255, 0.55)"
          strokeWidth="1.5"
        />
        <rect x="3" y="28" width="26" height="22" rx="13" fill={`url(#${gid}-body-back)`} />
      </g>

      <g opacity="0.72" transform="translate(48 26) scale(0.88)">
        <circle
          cx="16"
          cy="14"
          r="13"
          fill={`url(#${gid}-head-back)`}
          stroke="rgba(255, 150, 255, 0.55)"
          strokeWidth="1.5"
        />
        <rect x="3" y="28" width="26" height="22" rx="13" fill={`url(#${gid}-body-back)`} />
      </g>

      <g transform="translate(22 18)">
        <circle
          cx="24"
          cy="16"
          r="15"
          fill={`url(#${gid}-head-front)`}
          stroke="rgba(255, 170, 255, 0.85)"
          strokeWidth="2"
        />
        <ellipse cx="18" cy="11" rx="6.5" ry="4.5" fill="rgba(255,255,255,0.28)" />
        <rect
          x="6"
          y="34"
          width="36"
          height="28"
          rx="16"
          fill={`url(#${gid}-body-front)`}
          stroke="rgba(255, 150, 255, 0.58)"
          strokeWidth="1.7"
        />
      </g>

      <g transform="translate(18 72)">
        <g className="members-gear">
          <path
            d={gear}
            fill={`url(#${gid}-gear)`}
            stroke="rgba(255, 150, 255, 0.75)"
            strokeWidth="1.15"
          />
          <circle r="5" fill="rgba(20, 10, 40, 0.88)" />
        </g>
      </g>

      <g transform="translate(70 64)">
        <circle r="16" fill="rgba(28, 8, 58, 0.72)" stroke="rgba(255, 190, 255, 0.95)" strokeWidth="2.4" />
        <circle r="8.5" fill="none" stroke="rgba(255, 150, 255, 0.8)" strokeWidth="1.6" />
        <circle r="3.2" fill="#ff66ff" />
        <rect x="-1.15" y="-21" width="2.3" height="6.2" rx="1.1" fill="rgba(255, 210, 255, 0.95)" />
        <rect x="-1.15" y="14.8" width="2.3" height="6.2" rx="1.1" fill="rgba(255, 210, 255, 0.95)" />
        <rect x="-21" y="-1.15" width="6.2" height="2.3" rx="1.1" fill="rgba(255, 210, 255, 0.95)" />
        <rect x="14.8" y="-1.15" width="6.2" height="2.3" rx="1.1" fill="rgba(255, 210, 255, 0.95)" />
      </g>
    </svg>
  );
}

export function TargetDart({ gid }) {
  return (
    <svg className="feature-dart" viewBox="0 0 120 120" overflow="visible" aria-hidden="true">
      <defs>
        <radialGradient id={`${gid}-tgt`} cx="50%" cy="42%" r="58%">
          <stop offset="0%" stopColor="rgba(0, 180, 255, 0.38)" />
          <stop offset="100%" stopColor="rgba(0, 100, 200, 0.12)" />
        </radialGradient>
        <radialGradient id={`${gid}-bull`} cx="42%" cy="38%" r="62%">
          <stop offset="0%" stopColor="rgba(0, 255, 255, 0.95)" />
          <stop offset="100%" stopColor="rgba(0, 200, 255, 0.55)" />
        </radialGradient>
        <filter id={`${gid}-dart-glow`} x="-55%" y="-55%" width="210%" height="210%">
          <feGaussianBlur stdDeviation="1.8" result="b" />
          <feMerge>
            <feMergeNode in="b" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>
      <g>
        <circle
          cx="60"
          cy="60"
          r="50"
          fill={`url(#${gid}-tgt)`}
          stroke="rgba(0, 220, 255, 0.85)"
          strokeWidth="3"
        />
        <circle cx="60" cy="60" r="35" fill="none" stroke="rgba(0, 220, 255, 0.72)" strokeWidth="2.5" />
        <circle cx="60" cy="60" r="20" fill="none" stroke="rgba(0, 220, 255, 0.62)" strokeWidth="2" />
        <circle cx="60" cy="60" r="8" fill={`url(#${gid}-bull)`} />
        <line
          x1="90"
          y1="30"
          x2="63"
          y2="57"
          stroke="rgba(200, 230, 255, 0.95)"
          strokeWidth="3"
          strokeLinecap="round"
        />
        <polygon points="60,60 69,51 55.5,56" fill="rgba(200, 230, 255, 0.92)" />
        <polygon points="90,30 101,21 94.5,35" fill="rgba(150, 200, 255, 0.78)" />
        <polygon points="90,30 99,42 85,35.5" fill="rgba(150, 200, 255, 0.7)" />
      </g>
    </svg>
  );
}

export function TargetFigure({ gid }) {
  const pinPath =
    "M 80 10 C 40 10, 10 40, 10 80 C 10 120, 80 170, 80 170 C 80 170, 150 120, 150 80 C 150 40, 120 10, 80 10 Z";

  return (
    <svg width="118" height="132" viewBox="0 0 160 180" overflow="visible" aria-hidden="true">
      <defs>
        <radialGradient id={`${gid}-pin`} cx="40%" cy="36%" r="72%">
          <stop offset="0%" stopColor="rgba(0, 200, 255, 0.92)" />
          <stop offset="48%" stopColor="rgba(0, 100, 200, 0.55)" />
          <stop offset="100%" stopColor="rgba(0, 50, 150, 0.28)" />
        </radialGradient>
        <linearGradient id={`${gid}-pin-glass`} x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="rgba(0, 200, 255, 0.42)" />
          <stop offset="100%" stopColor="rgba(0, 100, 200, 0.12)" />
        </linearGradient>
        <radialGradient id={`${gid}-dot`} cx="42%" cy="38%" r="62%">
          <stop offset="0%" stopColor="rgba(0, 255, 255, 0.95)" />
          <stop offset="100%" stopColor="rgba(0, 200, 255, 0.45)" />
        </radialGradient>
        <filter id={`${gid}-pin-glow`} x="-40%" y="-40%" width="180%" height="190%">
          <feGaussianBlur stdDeviation="2.4" result="b" />
          <feMerge>
            <feMergeNode in="b" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
        <filter id={`${gid}-shine`} x="-60%" y="-60%" width="220%" height="220%">
          <feGaussianBlur stdDeviation="4.2" />
        </filter>
      </defs>
      <path
        d={pinPath}
        fill={`url(#${gid}-pin)`}
        stroke="rgba(0, 220, 255, 0.85)"
        strokeWidth="3"
      />
      <path d={pinPath} fill={`url(#${gid}-pin-glass)`} />
      <circle cx="80" cy="75" r="35" fill="none" stroke="rgba(0, 220, 255, 0.55)" strokeWidth="6" />
      <circle cx="80" cy="75" r="35" fill="none" stroke="rgba(0, 220, 255, 0.78)" strokeWidth="3" />
      <circle cx="80" cy="75" r="22" fill="none" stroke="rgba(0, 220, 255, 0.45)" strokeWidth="5" />
      <circle cx="80" cy="75" r="22" fill="none" stroke="rgba(0, 220, 255, 0.68)" strokeWidth="2.5" />
      <circle cx="80" cy="75" r="10" fill={`url(#${gid}-dot)`} />
      <ellipse
        cx="55"
        cy="50"
        rx="20"
        ry="30"
        fill="rgba(255, 255, 255, 0.16)"
        filter={`url(#${gid}-shine)`}
        transform="rotate(-20 55 50)"
      />
    </svg>
  );
}

export function BellFigure({ gid }) {
  const body =
    "M 80 18 C 61 18, 46 34, 46 56 C 46 74, 46 92, 46 100 C 46 112, 30 122, 16 128 C 10 131, 8 136, 16 137 L 144 137 C 152 136, 150 131, 144 128 C 130 122, 114 112, 114 100 C 114 92, 114 74, 114 56 C 114 34, 99 18, 80 18 Z";

  return (
    <svg className="feature-bell" width="118" height="140" viewBox="0 0 160 172" overflow="visible" aria-hidden="true">
      <defs>
        <radialGradient id={`${gid}-bell`} cx="36%" cy="24%" r="78%">
          <stop offset="0%" stopColor="#ffe7a8" />
          <stop offset="22%" stopColor="#ffc45c" />
          <stop offset="58%" stopColor="#ff9632" />
          <stop offset="100%" stopColor="#c45a10" />
        </radialGradient>
        <linearGradient id={`${gid}-shade`} x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%" stopColor="rgba(80, 28, 0, 0.28)" />
          <stop offset="38%" stopColor="rgba(80, 28, 0, 0)" />
          <stop offset="72%" stopColor="rgba(80, 28, 0, 0)" />
          <stop offset="100%" stopColor="rgba(80, 28, 0, 0.34)" />
        </linearGradient>
        <linearGradient id={`${gid}-glass`} x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="rgba(255, 236, 190, 0.42)" />
          <stop offset="100%" stopColor="rgba(255, 150, 50, 0.06)" />
        </linearGradient>
        <radialGradient id={`${gid}-rim`} cx="50%" cy="18%" r="78%">
          <stop offset="0%" stopColor="#ffe7b0" />
          <stop offset="55%" stopColor="#ffb347" />
          <stop offset="100%" stopColor="#d06a12" />
        </radialGradient>
        <radialGradient id={`${gid}-cavity`} cx="50%" cy="30%" r="70%">
          <stop offset="0%" stopColor="rgba(90, 32, 4, 0.55)" />
          <stop offset="100%" stopColor="rgba(40, 12, 0, 0.82)" />
        </radialGradient>
        <radialGradient id={`${gid}-clapper`} cx="38%" cy="32%" r="68%">
          <stop offset="0%" stopColor="#fff1c8" />
          <stop offset="100%" stopColor="#ffb347" />
        </radialGradient>
        <radialGradient id={`${gid}-core`} cx="50%" cy="42%" r="58%">
          <stop offset="0%" stopColor="rgba(255, 200, 100, 0.4)" />
          <stop offset="100%" stopColor="rgba(255, 150, 50, 0)" />
        </radialGradient>
        <filter id={`${gid}-glow`} x="-45%" y="-45%" width="190%" height="210%">
          <feGaussianBlur stdDeviation="2.2" result="b" />
          <feMerge>
            <feMergeNode in="b" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
        <filter id={`${gid}-shine`} x="-60%" y="-60%" width="220%" height="220%">
          <feGaussianBlur stdDeviation="3.4" />
        </filter>
      </defs>

      <path
        d={body}
        fill={`url(#${gid}-bell)`}
        stroke="rgba(255, 210, 130, 0.95)"
        strokeWidth="2.6"
        strokeLinejoin="round"
      />
      <path d={body} fill={`url(#${gid}-shade)`} />
      <path d={body} fill={`url(#${gid}-glass)`} />
      <ellipse
        cx="64"
        cy="50"
        rx="11"
        ry="20"
        fill="rgba(255, 255, 255, 0.28)"
        filter={`url(#${gid}-shine)`}
        transform="rotate(-18 64 50)"
      />
      <path
        d="M 80 28 C 73 52, 73 84, 78 112"
        fill="none"
        stroke="rgba(255, 255, 255, 0.16)"
        strokeWidth="5"
        strokeLinecap="round"
      />
      <ellipse cx="80" cy="134" rx="62" ry="10" fill={`url(#${gid}-cavity)`} />
      <ellipse cx="80" cy="132" rx="64" ry="9" fill={`url(#${gid}-rim)`} />
      <ellipse cx="80" cy="130" rx="50" ry="6" fill="rgba(255, 236, 190, 0.22)" />
      <ellipse
        cx="80"
        cy="132"
        rx="64"
        ry="9"
        fill="none"
        stroke="rgba(255, 220, 160, 0.9)"
        strokeWidth="2.2"
      />
      <path
        d="M 68 142 C 68 158, 92 158, 92 142"
        fill={`url(#${gid}-clapper)`}
        stroke="rgba(255, 214, 150, 0.95)"
        strokeWidth="2"
        strokeLinecap="round"
      />
      <circle
        cx="80"
        cy="156"
        r="7.5"
        fill={`url(#${gid}-clapper)`}
        stroke="rgba(255, 200, 100, 0.9)"
        strokeWidth="1.6"
      />
    </svg>
  );
}

export const FIGURE_ICONS = {
  documents: DocumentsFigure,
  calendar: CalendarFigure,
  chartDoc: ChartDocFigure,
  users: UsersFigure,
  target: TargetFigure,
  bell: BellFigure,
};

export function BrainNavIcon() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" aria-hidden="true">
      <path d="M12 4 C8.2 4 6 7 6 10 C4.4 10.4 3.5 12 4 14 C4.4 16 6.2 16.8 8 16.4 C8.4 18.6 10 20 12 20 C14 20 15.6 18.6 16 16.4 C17.8 16.8 19.6 16 20 14 C20.5 12 19.6 10.4 18 10 C18 7 15.8 4 12 4 Z" {...strokeProps("currentColor")} />
      <path d="M12 6.5 V18 M8.5 10.5 C9.6 11.6 10.2 13 10.4 14.8 M15.5 10.5 C14.4 11.6 13.8 13 13.6 14.8" {...strokeProps("currentColor")} />
    </svg>
  );
}

export function UsersNavIcon() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" aria-hidden="true">
      <circle cx="9" cy="8" r="3" {...strokeProps("currentColor")} />
      <path d="M3.5 19 C4 15.8 6 14 9 14 C12 14 14 15.8 14.5 19" {...strokeProps("currentColor")} />
      <circle cx="16.5" cy="8.5" r="2.4" {...strokeProps("currentColor")} />
      <path d="M15.2 14.2 C17.4 14.4 19.4 15.8 20.2 19" {...strokeProps("currentColor")} />
    </svg>
  );
}

export function TargetNavIcon() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" aria-hidden="true">
      <circle cx="12" cy="12" r="8" {...strokeProps("currentColor")} />
      <circle cx="12" cy="12" r="4.2" {...strokeProps("currentColor")} />
      <circle cx="12" cy="12" r="1.4" fill="currentColor" />
    </svg>
  );
}

export function ShieldNavIcon() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" aria-hidden="true">
      <path d="M12 3.2 L19.5 6.4 V12.4 C19.5 17 16 20.2 12 21.4 C8 20.2 4.5 17 4.5 12.4 V6.4 Z" {...strokeProps("currentColor")} />
      <path d="M12 8 V15 M9 11.5 H15" {...strokeProps("currentColor")} />
    </svg>
  );
}

export const NAV_ICONS = {
  brain: BrainNavIcon,
  users: UsersNavIcon,
  target: TargetNavIcon,
  shield: ShieldNavIcon,
};
