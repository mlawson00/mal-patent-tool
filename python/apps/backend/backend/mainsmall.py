from fastapi import FastAPI

app = FastAPI()


@app.get("/api/alive")
async def root():
    return {"message": "Hello World"}