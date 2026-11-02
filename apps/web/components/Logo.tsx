export default function Logo({ size = 22 }: { size?: number }) {
  return (
    <span className="logo" style={{ fontSize: size }}>
      <svg width={size} height={size} viewBox="0 0 24 24" aria-hidden="true">
        <circle cx="12" cy="12" r="10" fill="none" stroke="#647CFF" strokeWidth="2.2" />
        <path d="M7 9.5l5 7 5-7" fill="none" stroke="#25C99A" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
      VEYRA
    </span>
  );
}
