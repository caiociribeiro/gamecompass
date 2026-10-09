from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from neo4j import GraphDatabase
from neo4j.exceptions import Neo4jError

from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # O driver é criado uma vez e reutilizado durante a vida da aplicação.
    app.state.neo4j_driver = GraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password),
    )
    try:
        yield
    finally:
        app.state.neo4j_driver.close()


app = FastAPI(
    title=settings.app_name,
    description="API inicial do sistema de recomendação de jogos GameCompass.",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/", tags=["Geral"])
def root():
    return {"name": settings.app_name, "version": app.version}


@app.get("/health", tags=["Saúde"])
def health():
    return {"status": "ok"}


@app.get("/health/neo4j", tags=["Saúde"])
def neo4j_health():
    try:
        with app.state.neo4j_driver.session() as session:
            result = session.run("RETURN 1 AS status")
            record = result.single()
            if record is None or record["status"] != 1:
                raise HTTPException(
                    status_code=503,
                    detail="Neo4j respondeu com resultado inesperado.",
                )
        return {"status": "ok", "database": "neo4j"}
    except HTTPException:
        raise
    except (Neo4jError, OSError) as exc:
        raise HTTPException(
            status_code=503,
            detail="Não foi possível conectar ao Neo4j.",
        ) from exc
