"use client";

import Link from "next/link";
import { useSession, signOut } from "next-auth/react";
import { useState } from "react";

export function NavBar() {
  const { data: session } = useSession();
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <nav className="border-b border-gray-200 bg-white">
      <div className="mx-auto max-w-5xl px-4 sm:px-6">
        <div className="flex h-14 items-center justify-between">
          <Link href="/dashboard" className="text-xl font-bold text-amber-600">
            Daylight
          </Link>

          {/* Desktop nav */}
          <div className="hidden items-center gap-6 sm:flex">
            <Link href="/dashboard" className="text-sm text-gray-700 hover:text-gray-900">
              Feed
            </Link>
            <Link href="/alerts" className="text-sm text-gray-700 hover:text-gray-900">
              Alerts
            </Link>
            <Link href="/settings" className="text-sm text-gray-700 hover:text-gray-900">
              Settings
            </Link>
            {session?.user && (
              <button
                onClick={() => signOut({ callbackUrl: "/" })}
                className="text-sm text-gray-500 hover:text-gray-700"
              >
                Sign out
              </button>
            )}
          </div>

          {/* Mobile hamburger */}
          <button
            className="sm:hidden p-2"
            onClick={() => setMenuOpen(!menuOpen)}
            aria-label="Toggle menu"
          >
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              {menuOpen ? (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              ) : (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              )}
            </svg>
          </button>
        </div>

        {/* Mobile menu */}
        {menuOpen && (
          <div className="border-t py-3 sm:hidden space-y-2">
            <Link href="/dashboard" className="block text-sm text-gray-700 py-1" onClick={() => setMenuOpen(false)}>
              Feed
            </Link>
            <Link href="/alerts" className="block text-sm text-gray-700 py-1" onClick={() => setMenuOpen(false)}>
              Alerts
            </Link>
            <Link href="/settings" className="block text-sm text-gray-700 py-1" onClick={() => setMenuOpen(false)}>
              Settings
            </Link>
            {session?.user && (
              <button
                onClick={() => signOut({ callbackUrl: "/" })}
                className="block text-sm text-gray-500 py-1"
              >
                Sign out
              </button>
            )}
          </div>
        )}
      </div>
    </nav>
  );
}
