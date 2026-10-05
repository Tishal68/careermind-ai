import type { Metadata } from 'next';
import './globals.css';
import { AuthProvider } from '@/context/AuthContext';
import { SessionProvider } from '@/context/SessionContext';
import { CareerProvider } from '@/context/CareerContext';
import { WorkspaceProvider } from '@/context/WorkspaceContext';

export const metadata: Metadata = {
  title: 'CareerMind AI - Resume match and career coach',
  description: 'Match your resume to a job role, discover missing skills, and plan your next step with a local Ollama career coach.',
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
