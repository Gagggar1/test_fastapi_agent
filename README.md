# Langflow FastAPI Proxy

Этот проект представляет собой бэкенд на базе **FastAPI**, который выступает в качестве прокси (моста) между веб-интерфейсом (например, Lovable) и AI-агентом, развёрнутым в **Langflow**.

## 🚀 Возможности (Улучшения)
* **Асинхронные запросы:** Используется `httpx` для быстрой и неблокирующей обработки.
* **CORS настроен:** Интерфейс из браузера может отправлять запросы без ошибки CORS.
* **Аналитика:** Передается `user_id` для отслеживания запросов и считается `processing_time_ms` (время, которое AI думал над ответом).
* **Безопасность:** Скрыты "сырые" (raw) ответы агента, наружу передаётся только текст. `API-ключ` хранится на сервере и не утекает в браузер.
* **Режимы ответа:** Поддерживается передача поля `mode` (например, `detailed` заставляет агента отвечать подробно).

---

## 🛠️ Локальный запуск (Разработка)

1. Клонируйте репозиторий:
   ```bash
   git clone <URL_вашего_репозитория>
   cd b-Pel07-zerocoder-test-main
   ```

2. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```

3. Создайте файл `.env` в корне проекта со своими данными:
   ```env
   LANGFLOW_URL=https://langflow.dev.gagggarr.ru
   LANGFLOW_FLOW_ID=ваш-flow-id
   LANGFLOW_API_KEY=ваш-секретный-ключ
   LOVEABLE_ORIGIN=https://ваш-интерфейс.lovable.app
   ```
   *(ВНИМАНИЕ: `.env` добавлен в `.gitignore` и не попадёт в GitHub!)*

4. Запустите сервер:
   ```bash
   uvicorn main:app --reload
   ```

5. Перейдите в браузере по адресу: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## ☁️ Деплой на Railway

Проект полностью подготовлен для быстрого развёртывания на Railway. Все нужные файлы (`Procfile` и `requirements.txt`) уже в корне репозитория.

### Инструкция:
1. Запушьте код на свой GitHub:
   ```bash
   git add .
   git commit -m "feat: init Langflow proxy"
   git branch -M main
   git push -u origin main
   ```
2. Перейдите на [Railway.app](https://railway.app/).
3. Нажмите **New Project** -> **Deploy from GitHub repo**.
4. Выберите свой репозиторий. Railway сам всё соберет и запустит!
5. Зайдите в проект Railway на вкладку **Variables** и пропишите 3 секретных ключа:
   - `LANGFLOW_URL`
   - `LANGFLOW_FLOW_ID`
   - `LANGFLOW_API_KEY`
   - `LOVEABLE_ORIGIN` (добавьте сюда ссылку на свой Lovable)
6. В разделе **Settings** -> **Networking** нажмите **Generate Domain**, чтобы получить публичную ссылку на ваш API.

---

## 📚 API Эндпоинты

### `GET /health`
Проверка работоспособности сервиса.
**Ответ:** `{"status": "ok", "message": "FastAPI is running!"}`

### `POST /chat`
Отправка сообщения агенту.

**Request Body (JSON):**
```json
{
  "text": "Привет! Идея для рилса?",
  "session_id": "session_123",
  "user_id": "user_456",
  "mode": "short"
}
```

**Response (JSON):**
```json
{
  "input": "Привет! Идея для рилса?",
  "result_text": "Вот классная идея для твоего рилса...",
  "user_id": "user_456",
  "processing_time_ms": 1540
}
```