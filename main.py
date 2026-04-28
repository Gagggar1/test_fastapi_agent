import os
import time
from typing import Any, Dict, List, Optional, Tuple

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

load_dotenv()

# Настройки Langflow
LANGFLOW_URL = (os.getenv("LANGFLOW_URL") or "http://127.0.0.1:7860").strip().rstrip("/")
LANGFLOW_FLOW_ID = (os.getenv("LANGFLOW_FLOW_ID") or "").strip()
LANGFLOW_API_KEY = (os.getenv("LANGFLOW_API_KEY") or "").strip()

LANGFLOW_INPUT_TYPE = os.getenv("LANGFLOW_INPUT_TYPE") or "chat"
LANGFLOW_OUTPUT_TYPE = os.getenv("LANGFLOW_OUTPUT_TYPE") or "chat"

# CORS config
LOVEABLE_ORIGIN = (os.getenv("LOVEABLE_ORIGIN") or "").strip().rstrip("/")

missing: List[str] = []
for k, v in [
    ("LANGFLOW_URL", LANGFLOW_URL),
    ("LANGFLOW_FLOW_ID", LANGFLOW_FLOW_ID),
    ("LANGFLOW_API_KEY", LANGFLOW_API_KEY),
]:
    if not v:
        missing.append(k)

if missing:
    print(f"Warning: Missing required env vars: {', '.join(missing)}")

app = FastAPI(title="Langflow FastAPI Proxy (Homework Edition)")

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[LOVEABLE_ORIGIN] if LOVEABLE_ORIGIN else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = httpx.AsyncClient(timeout=httpx.Timeout(900.0), trust_env=False)

# --- 1. СТРУКТУРА ЗАПРОСА (С УЛУЧШЕНИЯМИ) ---
class ChatRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Текст запроса к агенту")
    session_id: Optional[str] = Field(None, description="ID сессии для контекста")
    user_id: Optional[str] = Field("web-user", description="ID пользователя для аналитики (наше улучшение)")
    mode: Optional[str] = Field("short", description="Режим ответа: short или detailed")

def _extract_text_from_langflow(resp_json: Dict[str, Any]) -> Optional[str]:
    try:
        return resp_json["outputs"][0]["outputs"][0]["results"]["message"]["text"]
    except (KeyError, IndexError, TypeError):
        return None

def _make_auth_headers() -> List[Dict[str, str]]:
    return [
        {"Authorization": f"Bearer {LANGFLOW_API_KEY}"},
        {"x-api-key": LANGFLOW_API_KEY},
    ]

async def _run_langflow(input_value: str, session_id: str) -> Tuple[Dict[str, Any], str]:
    url = f"{LANGFLOW_URL}/api/v1/run/{LANGFLOW_FLOW_ID}"

    payload: Dict[str, Any] = {
        "input_value": input_value,
        "input_type": LANGFLOW_INPUT_TYPE,
        "output_type": LANGFLOW_OUTPUT_TYPE,
        "session_id": session_id,
        "tweaks": None,
    }

    last_status: Optional[int] = None
    last_text: Optional[str] = None

    for auth in _make_auth_headers():
        headers = {"Content-Type": "application/json", **auth}
        try:
            r = await client.post(url, json=payload, headers=headers)
            last_status = r.status_code
            last_text = r.text

            if r.status_code in (401, 403):
                continue

            r.raise_for_status()
            return r.json(), ("bearer" if "Authorization" in auth else "x-api-key")

        except httpx.HTTPError as e:
            raise HTTPException(status_code=502, detail=f"Langflow error: {repr(e)}")

    raise HTTPException(status_code=502, detail=f"Auth failed. Last status={last_status}")


@app.get("/")
@app.get("/health")
async def health() -> Dict[str, str]:
    return {"status": "ok", "message": "FastAPI is running!"}


# --- 2. ЭНДПОИНТ С УЛУЧШЕНИЯМИ ---
@app.post("/chat")
async def chat_endpoint(req: ChatRequest) -> Dict[str, Any]:
    # Фиксируем время начала обработки (наше улучшение)
    start_time = time.time()
    
    # Можно добавить логику изменения промпта в зависимости от режима
    final_input = req.text
    if req.mode == "detailed":
        final_input += " (Ответь максимально подробно)"

    resp_json, auth_used = await _run_langflow(
        input_value=final_input,
        session_id=req.session_id or f"session-{req.user_id}",
    )
    
    # Вычисляем затраченное время в миллисекундах
    processing_time_ms = int((time.time() - start_time) * 1000)

    # --- 3. СТРУКТУРА ОТВЕТА (С УЛУЧШЕНИЯМИ) ---
    return {
        "input": req.text,
        "result_text": _extract_text_from_langflow(resp_json),
        "user_id": req.user_id,
        "processing_time_ms": processing_time_ms,
        # Мы специально убрали поле "raw", чтобы клиенты не видели лишних данных (безопасность)
    }
