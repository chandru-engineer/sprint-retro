export default function AuthBackground({ children }: { children: React.ReactNode }) {
  return (
    <div className="auth-bg min-h-dvh flex items-center justify-center px-4 py-10 relative overflow-hidden">
      <div className="auth-blob auth-blob-1" aria-hidden="true" />
      <div className="auth-blob auth-blob-2" aria-hidden="true" />
      <div className="auth-blob auth-blob-3" aria-hidden="true" />
      <div className="auth-grid" aria-hidden="true" />
      <div className="relative z-10 w-full flex justify-center">{children}</div>
    </div>
  );
}
