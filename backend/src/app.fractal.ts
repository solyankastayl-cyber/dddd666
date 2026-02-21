/**
 * FRACTAL ONLY - Isolated Development Entrypoint
 * 
 * Minimal bootstrap for Fractal + ML + MongoDB only.
 * No Exchange, On-chain, Sentiment, WebSocket, Telegram etc.
 * 
 * Run: npx tsx src/app.fractal.ts
 */

import 'dotenv/config';
import Fastify from 'fastify';
import cors from '@fastify/cors';
import { connectMongo, disconnectMongo } from './db/mongoose.js';
import { registerFractalModule } from './modules/fractal/index.js';
import { registerBtcRoutes } from './modules/btc/index.js';
import { registerSpxRoutes } from './modules/spx/index.js';
import { registerCombinedRoutes } from './modules/combined/index.js';
import { adminAuthRoutes } from './core/admin/admin.auth.routes.js';

async function main() {
  console.log('═══════════════════════════════════════════════════════════════');
  console.log('  FRACTAL ONLY - Isolated Development Mode');
  console.log('═══════════════════════════════════════════════════════════════');
  
  // Get port from env or default
  const PORT = parseInt(process.env.PORT || '8001');
  
  // Connect to MongoDB
  console.log('[Fractal] Connecting to MongoDB...');
  await connectMongo();
  
  // Build minimal Fastify app
  const app = Fastify({
    logger: {
      level: process.env.LOG_LEVEL || 'info',
    },
  });
  
  // CORS
  await app.register(cors, {
    origin: true,
    credentials: true,
  });
  
  // Health endpoint
  app.get('/api/health', async () => ({
    ok: true,
    mode: 'FRACTAL_ONLY',
    timestamp: new Date().toISOString()
  }));
  
  // Register ONLY Fractal module
  console.log('[Fractal] Registering Fractal Module...');
  await registerFractalModule(app);
  console.log('[Fractal] ✅ Fractal Module registered');
  
  // BLOCK A: Register BTC Terminal (Final Product)
  console.log('[Fractal] Registering BTC Terminal (Final)...');
  await registerBtcRoutes(app);
  console.log('[Fractal] ✅ BTC Terminal registered at /api/btc/v2.1/*');
  
  // BLOCK B: Register SPX Terminal (Building)
  console.log('[Fractal] Registering SPX Terminal (Building)...');
  await registerSpxRoutes(app);
  console.log('[Fractal] ✅ SPX Terminal registered at /api/spx/v2.1/*');
  
  // BLOCK C: Register Combined Terminal (Building)
  console.log('[Fractal] Registering Combined Terminal (Building)...');
  await registerCombinedRoutes(app);
  console.log('[Fractal] ✅ Combined Terminal registered at /api/combined/v2.1/*');
  
  // Register Admin Auth routes
  console.log('[Fractal] Registering Admin Auth...');
  await app.register(adminAuthRoutes, { prefix: '/api/admin' });
  console.log('[Fractal] ✅ Admin Auth registered');
  
  // Graceful shutdown
  const shutdown = async (signal: string) => {
    console.log(`[Fractal] Received ${signal}, shutting down...`);
    await app.close();
    await disconnectMongo();
    console.log('[Fractal] Shutdown complete');
    process.exit(0);
  };
  
  process.on('SIGTERM', () => shutdown('SIGTERM'));
  process.on('SIGINT', () => shutdown('SIGINT'));
  
  // Start server
  try {
    await app.listen({ port: PORT, host: '0.0.0.0' });
    console.log('═══════════════════════════════════════════════════════════════');
    console.log(`  ✅ Fractal Backend started on port ${PORT}`);
    console.log('═══════════════════════════════════════════════════════════════');
    console.log('');
    console.log('📦 Available Endpoints:');
    console.log('  GET  /api/health');
    console.log('  GET  /api/fractal/health');
    console.log('  GET  /api/fractal/signal');
    console.log('  GET  /api/fractal/match');
    console.log('  POST /api/fractal/match');
    console.log('  GET  /api/fractal/explain');
    console.log('  GET  /api/fractal/explain/detailed');
    console.log('  GET  /api/fractal/overlay');
    console.log('  POST /api/fractal/admin/backtest');
    console.log('  POST /api/fractal/admin/autolearn/run');
    console.log('  POST /api/fractal/admin/autolearn/monitor');
    console.log('  GET  /api/fractal/admin/dataset');
    console.log('');
  } catch (err) {
    console.error('[Fractal] Fatal error:', err);
    process.exit(1);
  }
}

main().catch((err) => {
  console.error('[Fractal] Fatal error:', err);
  process.exit(1);
});
