from fastapi import FastAPI

app = FastAPI(title="BetterAnk API")

@app.get("/")
async def root():
    return {"message": "Hello from BetterAnk API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)