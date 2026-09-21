import type { Metadata } from "next";
import { Manrope, Space_Grotesk } from "next/font/google";
import { DashboardShell } from "../components/DashboardShell";
import { AuthProvider } from "../lib/auth-context";
import "./globals.css";

const manrope = Manrope({ subsets: ["latin"], variable: "--font-manrope" });
const spaceGrotesk = Space_Grotesk({ subsets: ["latin"], variable: "--font-space-grotesk" });

export const metadata: Metadata = {
  title: "Ai-Task Flow",
  description: "A focused workspace for projects, tasks, and team momentum.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body className={`${manrope.variable} ${spaceGrotesk.variable}`}>
        <AuthProvider>
          <DashboardShell>{children}</DashboardShell>
        </AuthProvider>
      </body>
    </html>
  );
}