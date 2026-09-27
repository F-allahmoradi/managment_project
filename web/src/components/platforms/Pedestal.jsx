export default function Pedestal({ color, uid }) {
  const g = (name) => `${uid}-${name}`;
  const rings = [
    { rx: 128, ry: 30, o: 0.35, w: 1.2 },
    { rx: 110, ry: 25, o: 0.55, w: 1.4 },
    { rx: 92, ry: 20.5, o: 0.7, w: 1.6 },
    { rx: 74, ry: 16, o: 0.55, w: 1.3 },
    { rx: 56, ry: 11.5, o: 0.45, w: 1.2 },
    { rx: 38, ry: 7.5, o: 0.55, w: 1.1 },
    { rx: 22, ry: 4.2, o: 0.7, w: 1.1 },
  ];

  return (
    <div className="pedestal" aria-hidden="true">
      <span className="pedestal-neon-ring" />
      <svg className="pedestal-svg" viewBox="0 0 320 238" preserveAspectRatio="xMidYMax meet">
        <defs>
          <linearGradient id={g("cylH")} x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor="#000814" />
            <stop offset="12%" stopColor="#00111f" />
            <stop offset="28%" stopColor="#003566" />
            <stop offset="50%" stopColor="#0a2a4d" />
            <stop offset="72%" stopColor="#003566" />
            <stop offset="88%" stopColor="#00111f" />
            <stop offset="100%" stopColor="#000814" />
          </linearGradient>
          <linearGradient id={g("cylV")} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="rgba(0,180,216,0.18)" />
            <stop offset="18%" stopColor="rgba(0,53,102,0.12)" />
            <stop offset="55%" stopColor="rgba(0,8,20,0.15)" />
            <stop offset="100%" stopColor="rgba(0,0,0,0.72)" />
          </linearGradient>
          <linearGradient id={g("side")} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#0d1b33" />
            <stop offset="50%" stopColor="#07101f" />
            <stop offset="100%" stopColor="#000814" />
          </linearGradient>
          <linearGradient id={g("shoulder")} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#123050" />
            <stop offset="100%" stopColor="#071422" />
          </linearGradient>
          <radialGradient id={g("disc")} cx="50%" cy="38%" r="72%">
            <stop offset="0%" stopColor={color} stopOpacity="0.55" />
            <stop offset="28%" stopColor={color} stopOpacity="0.28" />
            <stop offset="62%" stopColor="#003566" stopOpacity="0.55" />
            <stop offset="100%" stopColor="#000814" stopOpacity="0.96" />
          </radialGradient>
          <radialGradient id={g("glass")} cx="50%" cy="20%" r="70%">
            <stop offset="0%" stopColor="rgba(255,255,255,0.35)" />
            <stop offset="40%" stopColor="rgba(0,180,216,0.12)" />
            <stop offset="100%" stopColor="rgba(0,180,216,0)" />
          </radialGradient>
          <radialGradient id={g("spark")} cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#fff" />
            <stop offset="28%" stopColor={color} stopOpacity="0.85" />
            <stop offset="100%" stopColor={color} stopOpacity="0" />
          </radialGradient>
          <linearGradient id={g("base")} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="rgba(0,180,216,0.28)" />
            <stop offset="100%" stopColor="rgba(0,29,61,0.45)" />
          </linearGradient>
          <filter id={g("glow")} x="-50%" y="-120%" width="200%" height="340%">
            <feGaussianBlur stdDeviation="2.6" result="b" />
            <feMerge>
              <feMergeNode in="b" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
          <filter id={g("soft")} x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="1.2" />
          </filter>
        </defs>

        <ellipse cx="160" cy="236" rx="142" ry="15" fill="#000" opacity="0.55" />

        <path d="M30 58 L30 208 A130 28 0 0 0 290 208 L290 58 Z" fill={`url(#${g("cylH")})`} />
        <path d="M30 58 L30 208 A130 28 0 0 0 290 208 L290 58 Z" fill={`url(#${g("cylV")})`} />

        <rect x="30" y="58" width="18" height="150" fill={color} opacity="0.12" filter={`url(#${g("soft")})`} />
        <rect x="272" y="58" width="14" height="150" fill={color} opacity="0.1" filter={`url(#${g("soft")})`} />
        <rect x="31" y="58" width="2" height="150" fill="rgba(0,180,216,0.28)" />
        <rect x="287" y="58" width="2" height="150" fill={color} opacity="0.28" />

        <ellipse cx="160" cy="212" rx="130" ry="20" fill="#000814" opacity="0.85" />
        <ellipse cx="160" cy="212" rx="130" ry="20" fill={`url(#${g("base")})`} />
        <ellipse cx="160" cy="212" rx="130" ry="20" fill="none" stroke={color} strokeWidth="1.6" opacity="0.45" />
        <ellipse cx="160" cy="222" rx="142" ry="22" fill="none" stroke={color} strokeWidth="1.2" opacity="0.28" />
        <path d="M48 202 A112 20 0 0 0 272 202" fill="none" stroke="rgba(0,0,0,0.7)" strokeWidth="2" />
        <path d="M52 206 A108 16 0 0 0 268 206" fill="none" stroke={color} strokeWidth="1.1" opacity="0.22" />

        <ellipse cx="160" cy="58" rx="130" ry="24" fill={`url(#${g("shoulder")})`} />
        <ellipse cx="160" cy="58" rx="130" ry="24" fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth="1" />
        <ellipse cx="160" cy="58" rx="130" ry="24" fill="none" stroke={color} strokeWidth="5" opacity="0.28" />

        <path d="M48 34 L48 54 A112 10 0 0 0 272 54 L272 34 Z" fill={`url(#${g("side")})`} />
        <ellipse cx="160" cy="54" rx="112" ry="10" fill="none" stroke="rgba(0,0,0,0.55)" strokeWidth="2" />

        <ellipse cx="160" cy="30" rx="112" ry="22" fill={`url(#${g("disc")})`} />
        <ellipse cx="160" cy="30" rx="112" ry="22" fill={`url(#${g("glass")})`} />
        <ellipse cx="160" cy="30" rx="112" ry="22" fill="none" stroke="rgba(255,255,255,0.28)" strokeWidth="1" />
        <ellipse cx="160" cy="30" rx="112" ry="22" fill="none" stroke={color} strokeWidth="6" opacity="0.32" />
        <ellipse
          className="pedestal-ring"
          cx="160"
          cy="30"
          rx="112"
          ry="22"
          fill="none"
          stroke={color}
          strokeWidth="2.4"
          opacity="0.95"
          filter={`url(#${g("glow")})`}
        />
        <ellipse cx="160" cy="32" rx="108" ry="19" fill="none" stroke="#05070d" strokeWidth="3.5" />

        {rings.map((ring) => (
          <g key={ring.rx} className="pedestal-ring">
            <ellipse
              cx="160"
              cy="30"
              rx={ring.rx}
              ry={ring.ry}
              fill="none"
              stroke={color}
              strokeWidth={ring.w + 1.1}
              opacity={ring.o * 0.32}
            />
            <ellipse
              cx="160"
              cy="30"
              rx={ring.rx}
              ry={ring.ry}
              fill="none"
              stroke={color}
              strokeWidth={ring.w}
              opacity={ring.o}
            />
          </g>
        ))}

        <ellipse cx="160" cy="22" rx="52" ry="7" fill="#000" opacity="0.4" />
        <circle cx="160" cy="28" r="20" fill={`url(#${g("spark")})`} />
        <circle cx="160" cy="28" r="3" fill="#fff" />
        <circle cx="160" cy="28" r="7" fill="none" stroke="#fff" strokeWidth="0.8" opacity="0.55" />
      </svg>
    </div>
  );
}
