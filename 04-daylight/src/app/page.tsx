import Link from "next/link";
import { auth } from "@/lib/auth";

export default async function LandingPage() {
  const session = await auth();

  return (
    <div className="flex min-h-screen flex-col">
      {/* Header */}
      <header className="border-b border-gray-100 bg-white">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-4 sm:px-6">
          <span className="text-xl font-bold text-amber-600">Daylight</span>
          {session?.user ? (
            <Link
              href="/dashboard"
              className="rounded-md bg-amber-500 px-4 py-2 text-sm font-medium text-white hover:bg-amber-600"
            >
              Go to Dashboard
            </Link>
          ) : (
            <div className="flex gap-3">
              <Link
                href="/login"
                className="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
              >
                Sign in
              </Link>
              <Link
                href="/register"
                className="rounded-md bg-amber-500 px-4 py-2 text-sm font-medium text-white hover:bg-amber-600"
              >
                Get started
              </Link>
            </div>
          )}
        </div>
      </header>

      {/* Hero */}
      <main className="flex flex-1 flex-col items-center justify-center px-4 py-20 text-center">
        <h1 className="max-w-2xl text-4xl font-bold tracking-tight text-gray-900 sm:text-5xl">
          Understand the bills that affect your life
        </h1>
        <p className="mt-6 max-w-xl text-lg text-gray-600">
          Bills are unreadable by design. Daylight translates legislation into
          plain English and alerts you before votes happen — so you can act while
          it still matters.
        </p>
        <Link
          href="/register"
          className="mt-8 rounded-md bg-amber-500 px-6 py-3 text-base font-medium text-white hover:bg-amber-600"
        >
          Start tracking bills
        </Link>

        {/* Features */}
        <div className="mt-20 grid max-w-4xl gap-8 sm:grid-cols-3">
          <div className="text-left">
            <h3 className="font-semibold text-gray-900">Translate</h3>
            <p className="mt-2 text-sm text-gray-600">
              AI translates bills from legalese into plain English anyone can
              understand. No law degree required.
            </p>
          </div>
          <div className="text-left">
            <h3 className="font-semibold text-gray-900">Alert</h3>
            <p className="mt-2 text-sm text-gray-600">
              Get a weekly email when bills you care about are moving — before
              votes happen, when your voice matters most.
            </p>
          </div>
          <div className="text-left">
            <h3 className="font-semibold text-gray-900">Act</h3>
            <p className="mt-2 text-sm text-gray-600">
              One-tap call scripts, letter templates, and sharing tools. From
              informed to involved in 30 seconds.
            </p>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-gray-100 py-8 text-center text-xs text-gray-400">
        Daylight — Making legislation readable, one bill at a time.
      </footer>
    </div>
  );
}
