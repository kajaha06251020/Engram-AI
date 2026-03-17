import type { Metadata } from "next";
import "./globals.css";
import ClientLayout from "@/components/ClientLayout";

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
        <ClientLayout>{children}</ClientLayout>
      </body>
    </html>
  );
}
