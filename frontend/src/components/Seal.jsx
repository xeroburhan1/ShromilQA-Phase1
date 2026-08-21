export default function Seal({ size = 36, className = "" }) {
  return (
    <img
      src="/logo.png"
      alt="Shromik QA Logo"
      width={size}
      height={size}
      className={`app-seal-logo ${className}`}
      style={{
        width: `${size}px`,
        height: `${size}px`,
        objectFit: "cover",
        borderRadius: "8px",
        display: "inline-block",
        flexShrink: 0,
      }}
    />
  );
}
