'use client';

import React, { useState, useEffect } from 'react';
import { ProjectCard } from '@/components/FeatureComponents';
import { fetchApi } from '@/lib/api';
import { FolderGit2 } from 'lucide-react';

export default function ProjectsPage() {
  const [projects, setProjects] = useState<any[]>([]);

  useEffect(() => {
    fetchApi<any[]>('/projects/recommendations?job_role=AI%20Engineer&experience_level=Mid-Level')
      .then((data) => setProjects(data))
      .catch(() => {
        setProjects([
          { id: "proj_1", title: "Autonomous AI Resume & Career RAG Platform", description: "Build a multi-agent vector search engine using Gemini API and FAISS.", required_skills: ["Python", "FastAPI", "FAISS", "Gemini API"], learning_outcomes: ["RAG Architecture", "Vector Search"], difficulty: "Intermediate", estimated_time: "20 Hours" },
          { id: "proj_2", title: "Real-time AI Telemetry Dashboard", description: "Develop an interactive monitoring dashboard with Chart.js and Next.js.", required_skills: ["Next.js", "TypeScript", "Tailwind CSS"], learning_outcomes: ["State Management", "Data Visualization"], difficulty: "Intermediate", estimated_time: "15 Hours" }
        ]);
      });
  }, []);

  return (
    <div className="max-w-7xl mx-auto px-6 py-10 space-y-8">
      <div><h1 className="text-3xl font-extrabold text-white flex items-center gap-3"><FolderGit2 className="w-8 h-8 text-indigo-400" />Project Recommendation Engine</h1><p className="text-slate-400 text-sm mt-1">Hands-on portfolio projects matched to fill your skill gaps.</p></div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">{projects.map((p) => <ProjectCard key={p.id} project={p} />)}</div>
    </div>
  );
}
