import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Link from "next/link";
import { MessageSquare, Wrench, Boxes } from "lucide-react";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "AgentLite",
  description: "AI Agent with Skills and MCP Tools",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.className} bg-slate-950 text-slate-50`}>
        <div className="flex h-screen">
          {/* Sidebar */}
          <aside className="w-64 bg-slate-900 border-r border-slate-700 flex flex-col">
            <div className="p-6 border-b border-slate-700">
              <h1 className="text-2xl font-bold bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent">
                AgentLite
              </h1>
              <p className="text-sm text-slate-400 mt-1">
                AI Assistant Platform
              </p>
            </div>

            <nav className="flex-1 p-4 space-y-2">
              <NavLink href="/" icon={<MessageSquare size={20} />}>
                Chat
              </NavLink>
              <NavLink href="/skills" icon={<Boxes size={20} />}>
                Skills
              </NavLink>
              <NavLink href="/tools" icon={<Wrench size={20} />}>
                Tools
              </NavLink>
            </nav>

            <div className="p-4 border-t border-slate-700 text-xs text-slate-500">
              <p>Version 0.1.0</p>
            </div>
          </aside>

          {/* Main Content */}
          <main className="flex-1 overflow-auto bg-slate-950">{children}</main>
        </div>
      </body>
    </html>
  );
}

function NavLink({
  href,
  icon,
  children,
}: {
  href: string;
  icon: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <Link
      href={href}
      className="flex items-center gap-3 px-4 py-3 rounded-lg hover:bg-slate-800 transition-colors text-slate-300 hover:text-white"
    >
      {icon}
      <span>{children}</span>
    </Link>
  );
}
