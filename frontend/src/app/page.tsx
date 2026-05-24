'use client';

import { useState } from 'react';
import PortfolioHeader from '../components/portfolio/PortfolioHeader';
import ActionQueue from '../components/queue/ActionQueue';
import SkuDetailPanel from '../components/sku/SkuDetailPanel';

export default function HomePage() {
  const [selectedSkuId, setSelectedSkuId] = useState<string | null>(null);
  const [isSkuPanelOpen, setIsSkuPanelOpen] = useState(false);

  const handleSkuClick = (skuId: string) => {
    setSelectedSkuId(skuId);
    setIsSkuPanelOpen(true);
  };

  const handleClosePanel = () => {
    setIsSkuPanelOpen(false);
    setSelectedSkuId(null);
  };

  return (
    <main className="min-h-screen bg-bg-base text-text-primary">
      <PortfolioHeader />
      <ActionQueue onSkuClick={handleSkuClick} />
      <SkuDetailPanel 
        skuId={selectedSkuId} 
        open={isSkuPanelOpen} 
        onClose={handleClosePanel} 
      />
    </main>
  );
}
