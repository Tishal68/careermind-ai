'use client';

import React from 'react';
import { ChatWindow } from '@/components/FeatureComponents';
import { Bot } from 'lucide-react';

export default function AssistantPage() {
  return (
    <div className="max-w-5xl mx-auto px-6 py-8 space-y-6">
      <div>
        <h1 className="text-3xl font-extrabold text-white flex items-center gap-3">
          <Bot className="w-8 h-8 text-indigo-400" />
          AI Career Assistant & RAG Advisor
        </h1>
        <p className="text-slate-400 text-sm mt-1">
          Chat with an intelligent assistant trained on your resume, missing skills, and software development roadmaps.
        </p>
      </div>

      <ChatWindow />
    </div>
  );
}
