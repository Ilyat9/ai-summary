from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from worker import process_url
import redis
import json
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="AI-Summary API")

# Настраиваем CORS, чтобы React на 5173 порту не ругался
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "https://ai-summary-frontend-19vp.onrender.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем Redis
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
if REDIS_URL.startswith("rediss://"):
    redis_client = redis.from_url(REDIS_URL, ssl_cert_reqs=None)
else:
    redis_client = redis.from_url(REDIS_URL)

class URLRequest(BaseModel):
    url: HttpUrl


class TaskResponse(BaseModel):
    task_id: str
    status: str


class StatusResponse(BaseModel):
    status: str
    result: str | None = None
    error: str | None = None


@app.post("/submit", response_model=TaskResponse)
async def submit_url(request: URLRequest):
    """
    Принимает URL и запускает фоновую задачу
    """
    try:
        # Отправляем задачу в Celery воркер
        task = process_url.delay(str(request.url))
        
        return TaskResponse(
            task_id=task.id,
            status="processing"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка запуска задачи: {str(e)}")


@app.get("/status/{task_id}", response_model=StatusResponse)
async def get_status(task_id: str):
    """
    Проверяем, готова ли выжимка
    """
    try:
        from celery.result import AsyncResult
        from worker import celery_app
        
        task_result = AsyncResult(task_id, app=celery_app)
        
        if task_result.ready():
            if task_result.successful():
                return StatusResponse(
                    status="completed",
                    result=task_result.result
                )
            else:
                return StatusResponse(
                    status="failed",
                    error=str(task_result.info)
                )
        else:
            return StatusResponse(status="processing")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения статуса: {str(e)}")


@app.get("/health")
async def health_check():
    """
    Проверка здоровья сервиса
    """
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)