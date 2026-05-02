import Link from "next/link";

export function Nav() {
  return (
    <nav className="border-b bg-white">
      <div className="mx-auto max-w-6xl px-4 py-3 flex items-center gap-6">
        <Link href="/" className="font-semibold">
          IRS Transcript Analyzer
        </Link>
        <Link href="/clients" className="text-slate-600 hover:text-slate-900">
          Clients
        </Link>
        <Link href="/library" className="text-slate-600 hover:text-slate-900">
          Observation library
        </Link>
      </div>
    </nav>
  );
}
