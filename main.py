import uvicorn
from fastapi import FastAPI
from routes import router

app = FastAPI(title="Educore analytics tool")
app.include_router(router)

if __name__ == "__main__":
    uvicorn.run(app)

