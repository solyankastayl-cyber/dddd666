/**
 * COMBINED TERMINAL — API Routes
 * 
 * BLOCK C1 — Combined API Namespace /api/combined/v2.1/*
 * 
 * Provides aggregated view of BTC + SPX with integration layers.
 */

import type { FastifyInstance, FastifyRequest } from 'fastify';
import COMBINED_CONFIG from './combined.config.js';

export async function registerCombinedRoutes(fastify: FastifyInstance): Promise<void> {
  const prefix = COMBINED_CONFIG.apiPrefix;
  
  /**
   * GET /api/combined/v2.1/info
   * Combined Product info
   */
  fastify.get(`${prefix}/info`, async () => {
    return {
      product: COMBINED_CONFIG.productName,
      version: COMBINED_CONFIG.version,
      status: COMBINED_CONFIG.status,
      primaryAsset: COMBINED_CONFIG.primaryAsset,
      macroAsset: COMBINED_CONFIG.macroAsset,
      layers: COMBINED_CONFIG.layers,
      defaultProfile: COMBINED_CONFIG.defaultProfile,
      spxInfluence: COMBINED_CONFIG.spxInfluence,
      safety: COMBINED_CONFIG.safety,
      description: 'BTC×SPX Macro-Integrated Terminal with full cross-asset intelligence',
    };
  });
  
  /**
   * GET /api/combined/v2.1/terminal
   * Combined Terminal (aggregates BTC + SPX)
   */
  fastify.get(`${prefix}/terminal`, async (req: FastifyRequest<{
    Querystring: {
      spxInfluence?: string;
      profile?: string;
    };
  }>) => {
    const spxInfluenceEnabled = req.query.spxInfluence !== 'OFF';
    const profile = req.query.profile || COMBINED_CONFIG.defaultProfile;
    
    return {
      ok: true,
      status: COMBINED_CONFIG.status,
      message: 'Combined Terminal is under construction. BTC core available, SPX pending.',
      
      config: {
        spxInfluence: spxInfluenceEnabled,
        profile,
        layers: COMBINED_CONFIG.layers,
      },
      
      // Placeholder for actual data
      btcCore: {
        available: true,
        message: 'Use /api/btc/v2.1/terminal for BTC-only data',
      },
      
      spxCore: {
        available: false,
        message: 'SPX Terminal is under construction',
      },
      
      combinedKernel: {
        available: false,
        message: 'Combined decision kernel requires both BTC and SPX to be active',
      },
      
      nextSteps: [
        '1. Complete SPX Terminal (data adapter + backfill)',
        '2. Implement Combined Decision Kernel',
        '3. Add integration layers L1-L4',
        '4. Build Combined UI',
      ],
    };
  });
  
  /**
   * GET /api/combined/v2.1/status
   * Combined Build status
   */
  fastify.get(`${prefix}/status`, async () => {
    return {
      ok: true,
      product: COMBINED_CONFIG.productName,
      status: COMBINED_CONFIG.status,
      progress: {
        config: true,
        routes: true,
        btcIntegration: true,
        spxIntegration: false,
        decisionKernel: false,
        layer1_macroGate: false,
        layer2_sizing: false,
        layer3_arbitration: false,
        layer4_learning: false,
        ui: false,
      },
      dependencies: {
        btcTerminal: 'READY',
        spxTerminal: 'BUILDING',
      },
      nextStep: 'Complete SPX Terminal first, then implement Combined Decision Kernel',
    };
  });
  
  /**
   * GET /api/combined/v2.1/layers
   * Integration layers info
   */
  fastify.get(`${prefix}/layers`, async () => {
    return {
      ok: true,
      layers: COMBINED_CONFIG.layers,
      profiles: {
        CONSERVATIVE: {
          L1: true, L2: true, L3: false, L4: false,
          description: 'Only macro gates and sizing - no direction override',
        },
        BALANCED: {
          L1: true, L2: true, L3: true, L4: false,
          description: 'Full risk management including direction arbitration',
        },
        AGGRESSIVE: {
          L1: true, L2: true, L3: true, L4: true,
          description: 'Maximum integration with learning coupling',
        },
      },
    };
  });
  
  fastify.log.info(`[Combined] Terminal routes registered at ${prefix}/* (BUILDING)`);
}

export default registerCombinedRoutes;
