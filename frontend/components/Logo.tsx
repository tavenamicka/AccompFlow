export function Logo({ size = 36 }: { size?: number }) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width={size} height={size} aria-hidden="true">
      <rect width="64" height="64" rx="32" fill="#C1502E" />
      <path d="M32 50V30" stroke="#FBF6EF" strokeWidth="5" strokeLinecap="round" />
      <path d="M32 34C32 22 24 16 14 16c0 12 6 18 18 18z" fill="#FBF6EF" />
      <path d="M32 30c0-9 6-14 16-14 0 10-5 14-16 14z" fill="#6B8F5E" stroke="#FBF6EF" strokeWidth="2.5" strokeLinejoin="round" />
    </svg>
  );
}
