import logging
import uuid
from contextlib import asynccontextmanager
from contextvars import ContextVar
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db.store import init_db

# ── Request-ID context for log tracing ────────────────
request_id_ctx: ContextVar[str] = ContextVar("request_id", default="-")


class _RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_ctx.get("-")  # type: ignore[attr-defined]
        return True


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  [%(request_id)s]  %(name)s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
for handler in logging.root.handlers:
    handler.addFilter(_RequestIdFilter())
# Quiet noisy third-party loggers
logging.getLogger("chromadb").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    init_db()
    yield
    # Cleanup on shutdown (if needed)


app = FastAPI(
    title="Developer Portfolio Optimizer",
    description="AI-powered resume and GitHub profile analysis",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request body size limit middleware ──────────────────
_MAX_BODY_BYTES = settings.max_file_size_bytes + 1024 * 1024  # file limit + 1 MB headroom


@app.middleware("http")
async def limit_request_body(request: Request, call_next):
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > _MAX_BODY_BYTES:
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=413,
            content={"detail": f"Request body too large (max {settings.max_file_size_mb + 1} MB)"},
        )
    return await call_next(request)


# ── Request-ID middleware ──────────────────────────────
@app.middleware("http")
async def attach_request_id(request: Request, call_next):
    rid = request.headers.get("x-request-id", uuid.uuid4().hex[:12])
    request_id_ctx.set(rid)
    response = await call_next(request)
    response.headers["x-request-id"] = rid
    return response

# ── Routes ──────────────────────────────────────────────
from app.api.v1.router import v1_router  # noqa: E402

app.include_router(v1_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    checks: dict[str, str] = {}

    # SQLite
    try:
        from app.db.store import load
        load("_health", "_ping")  # lightweight read
        checks["sqlite"] = "ok"
    except Exception as e:
        checks["sqlite"] = f"error: {e}"

    # ChromaDB
    try:
        from app.db.chroma_client import get_chroma_client
        get_chroma_client().heartbeat()
        checks["chromadb"] = "ok"
    except Exception as e:
        checks["chromadb"] = f"error: {e}"

    healthy = all(v == "ok" for v in checks.values())
    from fastapi.responses import JSONResponse
    return JSONResponse(
        content={"status": "ok" if healthy else "degraded", "checks": checks},
        status_code=200 if healthy else 503,
    )
