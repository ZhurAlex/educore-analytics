import logging

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.routes import router

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

app = FastAPI(title="Educore analytics tool")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.include_router(router)

if __name__ == "__main__":
    uvicorn.run(app)
