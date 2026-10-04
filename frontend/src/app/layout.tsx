import type { Metadata } from 'next';
import './globals.css';
import { AuthProvider } from '@/context/AuthContext';
import { SessionProvider } from '@/context/SessionContext';
import { CareerProvider } from '@/context/CareerContext';
import { WorkspaceProvider } from '@/context/WorkspaceContext';

export const metadata: Metadata = {
  title: 'NexPath - Your AI Career Operating System',
  description: 'Proactive AI Career Operating System for automated resume parsing, ATS checking, NexScore™ computation, skill gap analysis, and AI career coaching.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-[#070c14] text-slate-100 min-h-screen flex flex-col antialiased font-sans selection:bg-[#0F5E4E] selection:text-white">
        <AuthProvider>
          <SessionProvider>
            <CareerProvider>
              <WorkspaceProvider>
                <div className="flex-1 flex flex-col">{children}</div>
              </WorkspaceProvider>
            </CareerProvider>
          </SessionProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
