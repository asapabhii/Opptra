import Link from 'next/link';

export default function TopNav() {
  return (
    <nav className="sticky top-0 z-20 border-b border-bg-elevated bg-bg-base/90 backdrop-blur">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 lg:px-6">
        <div className="text-sm font-semibold text-text-primary">Opptra Pricing Intelligence</div>
        <div className="flex items-center gap-4 text-sm text-text-muted">
          <Link href="/" className="hover:text-text-primary">Queue</Link>
          <Link href="/log" className="hover:text-text-primary">Decision Log</Link>
        </div>
      </div>
    </nav>
  );
}
