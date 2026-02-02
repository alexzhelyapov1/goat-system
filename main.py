from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import habits, movies, tasks, auth, admin, telegram

app = FastAPI()

origins = [
    "http://localhost:5173",  # React development server
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(habits.router)
app.include_router(movies.router)
app.include_router(tasks.router)
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(telegram.router)

@app.get("/health")
def health_check():
    return {"status": "ok"}

