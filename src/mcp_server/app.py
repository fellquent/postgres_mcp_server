from contextlib import asynccontextmanager

from fastapi import FastAPI

from mcp_server.server import mcp

mcp_app = mcp.http_app(path="/", stateless_http=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with mcp_app.lifespan(app):
        yield


app = FastAPI(lifespan=lifespan, title="Postgres MCP Server")
app.mount("/mcp", mcp_app)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
