from fastapi import FastAPI
from app.api import habits, movies, tasks, auth, admin, telegram

app = FastAPI()

app.include_router(habits.router)
app.include_router(movies.router)
app.include_router(tasks.router)
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(telegram.router)

@app.get("/health")
def health_check():
    return {"status": "ok"}

