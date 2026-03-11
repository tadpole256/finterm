from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.alerts import router as alerts_router
from app.api.routes.filings import router as filings_router
from app.api.routes.health import router as health_router
from app.api.routes.layout import router as layout_router
from app.api.routes.macro import router as macro_router
from app.api.routes.market import router as market_router
from app.api.routes.portfolio import router as portfolio_router
from app.api.routes.research import ai_router as ai_router
from app.api.routes.research import router as research_router
from app.api.routes.screening import router as screening_router
from app.api.routes.watchlists import router as watchlists_router
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix=settings.api_prefix)
app.include_router(market_router, prefix=settings.api_prefix)
app.include_router(watchlists_router, prefix=settings.api_prefix)
app.include_router(layout_router, prefix=settings.api_prefix)
app.include_router(screening_router, prefix=settings.api_prefix)
app.include_router(research_router, prefix=settings.api_prefix)
app.include_router(ai_router, prefix=settings.api_prefix)
app.include_router(portfolio_router, prefix=settings.api_prefix)
app.include_router(alerts_router, prefix=settings.api_prefix)
app.include_router(filings_router, prefix=settings.api_prefix)
app.include_router(macro_router, prefix=settings.api_prefix)
