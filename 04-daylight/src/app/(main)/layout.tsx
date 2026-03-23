import { NavBar } from "@/components/NavBar";

export default function MainLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <NavBar />
      <main className="mx-auto w-full max-w-5xl flex-1 px-4 py-6 sm:px-6">
        {children}
      </main>
      <footer className="border-t border-gray-100 py-6 text-center text-xs text-gray-400">
        Daylight — AI-generated summaries. Always read the full bill text for complete details.
      </footer>
    </>
  );
}
