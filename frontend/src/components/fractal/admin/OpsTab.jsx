/**
 * BLOCK 80.1 + 80.3 — Ops Tab
 * 
 * Daily Run Control + History + Consensus Timeline
 */

import React from 'react';
import { DailyRunCard } from './DailyRunCard';
import { DailyRunHistory } from './DailyRunHistory';
import { ConsensusTimelineCard } from './ConsensusTimelineCard';

export function OpsTab() {
  return (
    <div className="space-y-6" data-testid="ops-tab">
      {/* Daily Run Control */}
      <DailyRunCard />
      
      {/* Consensus Timeline */}
      <ConsensusTimelineCard />
      
      {/* Run History */}
      <DailyRunHistory />
    </div>
  );
}

export default OpsTab;
