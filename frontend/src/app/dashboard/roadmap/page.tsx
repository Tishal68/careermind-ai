'use client';

import React, { useState } from 'react';
import { Card, Button } from '@/components/UIComponents';
import { RoadmapMilestoneCard } from '@/components/FeatureComponents';
import { Map, Sparkles } from 'lucide-react';
import { fetchApi } from '@/lib/api';

export default function RoadmapPage() {
  const [milestones, setMilestones] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const handleGenerateRoadmap = async () => {
    setIsLoading(true);
    try {
      const data = await fetchApi<any>('/roadmap/generate/1', { method: 'POST' });
      setMilestones(data.milestones || []);
    } catch {
      setMilestones([
        {
          week_number: 1, title: "Fundamentals & Math Prerequisites", focus_topic: "Linear Algebra & NumPy",
          resources: ["Deep Learning Specialization"], tasks: [{ id: "w1_1", task_name: "Implement Neural Net in NumPy", is_completed: false }]
        },
        {
          week_number: 2, title: "PyTorch & Transformers", focus_topic: "Tensors & Attention Mechanisms",
          resources: ["PyTorch Docs"], tasks: [{ id: "w2_1", task_name: "Train Transformer Model", is_completed: false }]
        }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto px-6 py-10 space-y-8">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div><h1 className="text-3xl font-extrabold text-white flex items-center gap-3"><Map className="w-8 h-8 text-pink-400" />Personalized Learning Roadmap</h1><p className="text-slate-400 text-sm mt-1">Weekly milestones customized for your target career role.</p></div>
        <Button onClick={handleGenerateRoadmap} isLoading={isLoading} leftIcon={<Sparkles className="w-4 h-4" />}>Generate Roadmap</Button>
      </div>
      {milestones.length > 0 ? (
        <div className="space-y-6">{milestones.map((m, idx) => <RoadmapMilestoneCard key={idx} milestone={m} />)}</div>
      ) : (
        <Card glass className="text-center py-20 border-dashed"><Map className="w-12 h-12 text-slate-600 mx-auto mb-3" /><p className="text-slate-300 font-medium">No Active Roadmap</p></Card>
      )}
    </div>
  );
}
