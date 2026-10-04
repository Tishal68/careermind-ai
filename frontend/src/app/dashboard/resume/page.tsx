'use client';

import React, { useState } from 'react';
import { Card } from '@/components/UIComponents';
import { Uploader, ParsedPreview } from '@/components/FeatureComponents';
import { FileCheck, Sparkles } from 'lucide-react';

export default function ResumePage() {
  const [parsedResume, setParsedResume] = useState<any>(null);

  return (
    <div className="max-w-6xl mx-auto px-6 py-10 space-y-8">
      <div>
        <h1 className="text-3xl font-extrabold text-white flex items-center gap-3"><FileCheck className="w-8 h-8 text-indigo-400" />Resume Management & Parsing</h1>
        <p className="text-slate-400 text-sm mt-1">Upload your resume in PDF or DOCX format to automatically extract skills, education, and experience.</p>
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-1">
          <Card glass className="sticky top-24"><h2 className="text-lg font-bold text-white mb-4 flex items-center gap-2"><Sparkles className="w-5 h-5 text-indigo-400" />Upload Resume</h2><Uploader onSuccess={(data) => setParsedResume(data)} /></Card>
        </div>
        <div className="lg:col-span-2">
          {parsedResume ? <ParsedPreview data={parsedResume} /> : <Card glass className="text-center py-16 border-dashed"><FileCheck className="w-12 h-12 text-slate-600 mx-auto mb-3" /><p className="text-slate-300 font-medium">No Resume Parsed Yet</p><p className="text-xs text-slate-500 max-w-sm mx-auto mt-1">Upload your PDF or DOCX file to preview extracted intelligence.</p></Card>}
        </div>
      </div>
    </div>
  );
}
