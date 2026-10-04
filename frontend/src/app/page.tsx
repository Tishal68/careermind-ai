'use client';

import React from 'react';
import Link from 'next/link';
import { Card, Button } from '@/components/UIComponents';
import { Compass, Sparkles, ArrowRight, ShieldCheck, Target, Map, FolderGit2, Bot } from 'lucide-react';

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-[#070c14] text-slate-100 selection:bg-emerald-500 selection:text-white">
      {/* Inline Navbar */}
      <nav className="w-full border-b border-white/10 bg-[#070c14]/80 backdrop-blur-xl sticky top-0 z-50">
        <div className="max-w-6xl mx-auto flex items-center justify-between px-6 py-3">
          <Link href="/" className="flex items-center gap-2.5">
            <div className="p-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-400">
              <Compass className="w-5 h-5" />
            </div>
            <span className="text-lg font-extrabold text-white tracking-tight">NexPath</span>
          </Link>
          <div className="flex items-center gap-3">
            <Link href="/login">
              <Button variant="ghost" size="sm">Sign In</Button>
            </Link>
            <Link href="/register">
              <Button variant="emerald" size="sm" rightIcon={<ArrowRight className="w-3.5 h-3.5" />}>
                Get Started
              </Button>
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="max-w-6xl mx-auto px-6 py-24 text-center space-y-8 relative">
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-semibold">
          <Sparkles className="w-4 h-4" /> Next-Generation AI Career Operating System
        </div>

        <h1 className="text-4xl md:text-6xl font-extrabold text-white tracking-tight max-w-4xl mx-auto leading-tight">
          Your Personal AI Career Mentor & <span className="text-emerald-400">Career Operating System</span>
        </h1>

        <p className="text-sm md:text-base text-slate-400 max-w-2xl mx-auto leading-relaxed">
          NexPath automatically parses your resume, calculates your <strong className="text-white">NexScore™</strong>, identifies skill gaps, and generates a personalized 4-week roadmap to make you industry-ready.
        </p>

        <div className="flex flex-wrap justify-center gap-4 pt-4">
          <Link href="/register">
            <Button size="lg" variant="emerald" rightIcon={<ArrowRight className="w-4 h-4" />}>
              Get Started for Free
            </Button>
          </Link>
          <Link href="/login">
            <Button size="lg" variant="outline">
              Sign In to Workspace
            </Button>
          </Link>
        </div>
      </section>

      {/* Philosophy & Architecture Pillars */}
      <section className="max-w-6xl mx-auto px-6 py-16 border-t border-white/10">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card className="p-8 bg-[#0b1320] border-white/10 space-y-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-500/10 text-emerald-400 flex items-center justify-center">
              <Compass className="w-5 h-5" />
            </div>
            <h3 className="text-base font-bold text-white">Single-Upload Automation</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Upload your resume once. NexPath automatically executes parsing, ATS compatibility checking, gap analysis, and roadmap generation.
            </p>
          </Card>

          <Card className="p-8 bg-[#0b1320] border-white/10 space-y-3">
            <div className="w-10 h-10 rounded-xl bg-orange-500/10 text-orange-400 flex items-center justify-center">
              <Target className="w-5 h-5" />
            </div>
            <h3 className="text-base font-bold text-white">NexScore™ Rating</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              One central composite score evaluating your ATS compatibility, resume quality, technical depth, and role readiness.
            </p>
          </Card>

          <Card className="p-8 bg-[#0b1320] border-white/10 space-y-3">
            <div className="w-10 h-10 rounded-xl bg-amber-500/10 text-amber-400 flex items-center justify-center">
              <Bot className="w-5 h-5" />
            </div>
            <h3 className="text-base font-bold text-white">Proactive AI Mentor</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              A personal career coach that remembers your resume, target role, roadmap progress, and interview history.
            </p>
          </Card>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-white/5 py-8 text-center text-xs text-slate-500">
        <p>© 2026 NexPath. Built with Next.js, FastAPI & Google Gemini AI.</p>
      </footer>
    </div>
  );
}
