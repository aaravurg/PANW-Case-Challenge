'use client';

import { useState } from 'react';
import OnboardingScreen from '@/components/OnboardingScreen';
import Dashboard from '@/components/Dashboard';

export default function Home() {
  const [showDashboard, setShowDashboard] = useState(false);

  if (showDashboard) {
    return <Dashboard />;
  }

  return <OnboardingScreen onComplete={() => setShowDashboard(true)} />;
}
