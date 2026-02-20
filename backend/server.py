"""
FastAPI wrapper for TypeScript Fractal Backend
Proxies all /api/* requests to Node.js TypeScript backend running on port 8002
"""
import os
import subprocess
import threading
import time
import httpx
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

TS_BACKEND_URL = "http://127.0.0.1:8002"
ts_process = None


def start_ts_backend():
    """Start TypeScript backend in background"""
    global ts_process
    env = os.environ.copy()
    env["PORT"] = "8002"
    env["FRACTAL_ONLY"] = "1"
    env["MINIMAL_BOOT"] = "1"
    env["FRACTAL_ENABLED"] = "true"
    env["WS_ENABLED"] = "false"
    
    # Use MONGODB_URI from env (Emergent provides complete URI)
    mongo_url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
    db_name = os.environ.get("DB_NAME", "fractal_dev")
    env["MONGODB_URI"] = f"{mongo_url}/{db_name}"
    
    print(f"[Proxy] Starting TypeScript backend on port 8002...")
    print(f"[Proxy] MONGODB_URI={env.get('MONGODB_URI')}")
    
    ts_process = subprocess.Popen(
        ["npx", "tsx", "src/app.fractal.ts"],
        cwd="/app/backend",
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    
    # Stream logs in background thread
    def stream_logs():
        if ts_process and ts_process.stdout:
            for line in ts_process.stdout:
                print(f"[TS] {line.decode().strip()}")
    
    log_thread = threading.Thread(target=stream_logs, daemon=True)
    log_thread.start()
    
    # Wait for backend to be ready
    for i in range(30):
        try:
            resp = httpx.get(f"{TS_BACKEND_URL}/api/health", timeout=2.0)
            if resp.status_code == 200:
                print(f"[Proxy] TypeScript backend ready!")
                return True
        except:
            pass
        time.sleep(1)
    
    print("[Proxy] Warning: TypeScript backend may not be ready")
    return False


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    threading.Thread(target=start_ts_backend, daemon=True).start()
    yield
    # Shutdown
    global ts_process
    if ts_process:
        ts_process.terminate()


app = FastAPI(title="Fractal Backend Proxy", lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"ok": True, "message": "Fractal Backend Proxy", "ts_backend": TS_BACKEND_URL}


@app.api_route("/api/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_api(request: Request, path: str):
    """Proxy all /api/* requests to TypeScript backend"""
    # Longer timeout for simulation/optimization endpoints
    long_timeout_keywords = ["optimize", "sweep", "certify", "sim"]
    timeout = 900.0 if any(kw in path for kw in long_timeout_keywords) else 60.0
    
    async with httpx.AsyncClient(timeout=timeout) as client:
        url = f"{TS_BACKEND_URL}/api/{path}"
        
        # Forward query params
        if request.query_params:
            url += f"?{request.query_params}"
        
        # Forward body for POST/PUT/PATCH
        body = None
        if request.method in ["POST", "PUT", "PATCH"]:
            body = await request.body()
        
        try:
            resp = await client.request(
                method=request.method,
                url=url,
                content=body,
                headers={
                    k: v for k, v in request.headers.items()
                    if k.lower() not in ["host", "content-length"]
                },
            )
            
            return Response(
                content=resp.content,
                status_code=resp.status_code,
                headers=dict(resp.headers),
                media_type=resp.headers.get("content-type"),
            )
        except httpx.ConnectError:
            return Response(
                content='{"ok": false, "error": "TypeScript backend not ready"}',
                status_code=503,
                media_type="application/json",
            )
        except Exception as e:
            return Response(
                content=f'{{"ok": false, "error": "{str(e)}"}}',
                status_code=500,
                media_type="application/json",
            )
