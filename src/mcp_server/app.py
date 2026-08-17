from contextlib import asynccontextmanager

from fastapi import FastAPI

from mcp_server.server import mcp

# path="/" avoids doubling: the mcp app's own default path is /mcp, so mounting
# it at /mcp would expose it at /mcp/mcp/. stateless_http keeps sessions out of
# process memory, so more than one uvicorn worker still works.
mcp_app = mcp.http_app(path="/", stateless_http=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # fastapi does not run the lifespan of mounted apps, so delegate explicitly
    async with mcp_app.lifespan(app):
        yield


app = FastAPI(lifespan=lifespan, title="Postgres MCP Server")
# served at /mcp/ with the trailing slash; /mcp 307-redirects and not every
# client follows redirects on POST.
# note: route dependencies do not cover a mounted app -- auth has to be
# middleware, or it will not apply here.
app.mount("/mcp", mcp_app)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
