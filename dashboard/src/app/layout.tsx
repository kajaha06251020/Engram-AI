import type { Metadata } from "next";
import "./globals.css";
import NavTabs from "@/components/NavTabs";

export const metadata: Metadata = {
  title: "Engram-AI Dashboard",
  description: "Real-time visualization of AI agent experiences and skills",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-engram-bg text-gray-200 min-h-screen font-sans">
        <header className="border-b border-engram-border px-6 py-3">
          <div className="max-w-7xl mx-auto flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-6 h-6 rounded-full bg-gradient-to-br from-engram-purple to-purple-400" />
              <span className="font-bold text-sm">Engram-AI</span>
            </div>
            <NavTabs />
          </div>
        </header>
        <main className="max-w-7xl mx-auto px-6 py-6">{children}</main>
      </body>
    </html>
  );
}
