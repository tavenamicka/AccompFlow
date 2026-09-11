export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen flex-1 items-center justify-center bg-cream px-4">
      <div className="w-full max-w-sm">
        <p className="mb-6 text-center font-heading text-lg font-bold text-brand">AccompFlow</p>
        {children}
      </div>
    </div>
  );
}
