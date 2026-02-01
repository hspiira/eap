export function WaterDropSvg({ className = '' }: { className?: string }) {
  const cx = 200
  const surfaceY = 156
  const dropStartY = 36
  const rippleRadii = [20, 45, 70, 95, 120, 145, 170, 195]
  const cycleDuration = 5

  return (
    <svg
      className={className}
      viewBox="0 0 400 300"
      preserveAspectRatio="xMidYMid slice"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden
    >
      <defs>
        <linearGradient id="water-bg" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stopColor="#bae6fd" />
          <stop offset="40%" stopColor="#7dd3fc" />
          <stop offset="100%" stopColor="#0ea5e9" />
        </linearGradient>
        <linearGradient id="splash-col" x1="0%" y1="100%" x2="0%" y2="0%">
          <stop offset="0%" stopColor="#0ea5e9" stopOpacity="0.95" />
          <stop offset="50%" stopColor="#7dd3fc" stopOpacity="0.9" />
          <stop offset="100%" stopColor="#e0f2fe" stopOpacity="0.85" />
        </linearGradient>
        <linearGradient id="drop-fill" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#e0f2fe" />
          <stop offset="70%" stopColor="#0ea5e9" />
        </linearGradient>
        <filter id="drop-soft" x="-50%" y="-50%" width="200%" height="200%">
          <feGaussianBlur in="SourceGraphic" stdDeviation="0.5" result="blur" />
          <feMerge>
            <feMergeNode in="blur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>

      <style>{`
        @keyframes water-drop-fall {
          0% { transform: translateY(${dropStartY - surfaceY}px); opacity: 1; }
          26% { transform: translateY(0); opacity: 1; }
          28% { opacity: 0; }
          100% { opacity: 0; }
        }
        @keyframes water-splash-rise {
          0%, 26% { transform: scaleY(0); opacity: 0; }
          30% { opacity: 1; }
          38% { transform: scaleY(1); opacity: 1; }
          44% { transform: scaleY(0.95); opacity: 0.9; }
          50% { transform: scaleY(0); opacity: 0; }
          100% { opacity: 0; }
        }
        @keyframes water-ripple {
          0%, 26% { transform: scale(0); opacity: 0; }
          28% { opacity: 0.55; }
          76% { transform: scale(1); opacity: 0; }
          100% { transform: scale(1); opacity: 0; }
        }
        .water-drop {
          transform-origin: 0 0;
          animation: water-drop-fall ${cycleDuration}s ease-in-out infinite;
        }
        .water-splash {
          transform-origin: 0 0;
          animation: water-splash-rise ${cycleDuration}s ease-out infinite;
        }
        .water-ripple {
          transform-origin: center;
          animation: water-ripple ${cycleDuration}s ease-out infinite;
        }
      `}</style>

      <rect width="400" height="300" fill="url(#water-bg)" />

      {rippleRadii.map((r, i) => (
        <circle
          key={r}
          className="water-ripple"
          cx={cx}
          cy={surfaceY}
          r={r}
          stroke="rgba(255,255,255,0.7)"
          strokeWidth="1.8"
          fill="none"
          style={{
            animationDelay: `${i * 0.12}s`,
          }}
        />
      ))}

      <g transform={`translate(${cx}, ${surfaceY})`}>
        <g className="water-splash">
          <path
            d="M -8 0 L 8 0 L 5 -55 L -5 -55 Z"
            fill="url(#splash-col)"
          />
        </g>
      </g>

      <g transform={`translate(${cx}, ${surfaceY})`}>
        <g className="water-drop">
          <circle
            r="7"
            fill="url(#drop-fill)"
            filter="url(#drop-soft)"
          />
          <circle
            r="2.5"
            fill="rgba(255,255,255,0.8)"
            cx="-2"
            cy="-2"
          />
        </g>
      </g>
    </svg>
  )
}
