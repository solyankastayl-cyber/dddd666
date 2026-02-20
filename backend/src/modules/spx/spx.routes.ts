/**
 * SPX TERMINAL — API Routes (Skeleton)
 * 
 * BLOCK B1 — SPX API Namespace /api/spx/v2.1/*
 * 
 * Currently returns "coming soon" for most endpoints.
 * Will be fully implemented when SPX data adapter is ready.
 */

import type { FastifyInstance } from 'fastify';
import SPX_CONFIG from './spx.config.js';

export async function registerSpxRoutes(fastify: FastifyInstance): Promise<void> {
  const prefix = SPX_CONFIG.apiPrefix;
  
  /**
   * GET /api/spx/v2.1/info
   * SPX Product info
   */
  fastify.get(`${prefix}/info`, async () => {
    return {
      product: 'SPX Terminal',
      version: SPX_CONFIG.contractVersion,
      symbol: SPX_CONFIG.symbol,
      frozen: SPX_CONFIG.frozen,
      status: SPX_CONFIG.status,
      horizons: SPX_CONFIG.horizons,
      governance: SPX_CONFIG.governance,
      dataSource: SPX_CONFIG.dataSource,
      description: 'Pure SPX Fractal Terminal - S&P 500 Index Analysis',
      message: 'SPX Terminal is under construction. Full functionality coming soon.',
    };
  });
  
  /**
   * GET /api/spx/v2.1/terminal
   * SPX Terminal (placeholder)
   */
  fastify.get(`${prefix}/terminal`, async () => {
    return {
      ok: false,
      status: 'BUILDING',
      message: 'SPX Terminal is under construction',
      symbol: SPX_CONFIG.symbol,
      eta: 'Data adapter + backfill required first',
    };
  });
  
  /**
   * GET /api/spx/v2.1/status
   * SPX Build status
   */
  fastify.get(`${prefix}/status`, async () => {
    return {
      ok: true,
      product: 'SPX Terminal',
      status: SPX_CONFIG.status,
      progress: {
        config: true,
        routes: true,
        dataAdapter: false,
        backfill: false,
        horizons: false,
        consensus: false,
        governance: false,
        ui: false,
      },
      nextStep: 'Implement SPX data adapter (spx.data.adapter.ts)',
    };
  });
  
  fastify.log.info(`[SPX] Terminal routes registered at ${prefix}/* (BUILDING)`);
}

export default registerSpxRoutes;
