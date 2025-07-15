from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager
import uvicorn
import asyncio
import logging

from app.core.config import settings
from app.db.session import engine
from app.db.models import Base
from app.api.routes import router as api_router

# Konfiguracja logowania
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def init_db():
    """Inicjalizacja bazy danych z retry logic"""
    max_retries = 5
    retry_delay = 5
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Próba połączenia z bazą danych (próba {attempt + 1}/{max_retries})")
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Pomyślnie połączono z bazą danych i utworzono tabele")
            return
        except Exception as e:
            logger.error(f"Błąd połączenia z bazą danych: {e}")
            if attempt < max_retries - 1:
                logger.info(f"Ponowna próba za {retry_delay} sekund...")
                await asyncio.sleep(retry_delay)
            else:
                logger.error("Nie udało się połączyć z bazą danych po wszystkich próbach")
                raise


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        await init_db()
    except Exception as e:
        logger.error(f"Błąd inicjalizacji bazy danych: {e}")
        logger.warning("Aplikacja będzie działać bez połączenia z bazą danych")
        # Nie przerywamy startu aplikacji - pozwalamy działać bez bazy
    
    yield
    
    # Shutdown
    try:
        await engine.dispose()
        logger.info("Zamknięto połączenia z bazą danych")
    except Exception as e:
        logger.error(f"Błąd podczas zamykania połączeń z bazą: {e}")


app = FastAPI(
    title="Sailing Route Optimizer",
    description="API do wyznaczania optymalnej trasy regatowej",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Compression middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Include routers
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Sailing Route Optimizer API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """Sprawdzenie stanu aplikacji"""
    status = {"status": "healthy", "components": {}}
    
    # Sprawdź połączenie z bazą danych
    try:
        async with engine.begin() as conn:
            await conn.execute("SELECT 1")
        status["components"]["database"] = "healthy"
    except Exception as e:
        status["components"]["database"] = f"unhealthy: {str(e)}"
        status["status"] = "degraded"
    
    return status

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )