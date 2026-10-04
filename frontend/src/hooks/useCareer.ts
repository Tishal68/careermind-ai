'use client';

import { useCareerContext } from '@/context/CareerContext';

export function useCareer() {
  return useCareerContext();
}
