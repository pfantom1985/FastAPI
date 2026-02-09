# Proxy & Contract API
Mini-API “Proxy & Contract” — FastAPI сервис-обёртка над JSONPlaceholder.
Ваш API возвращает нормализованные посты/комментарии и всегда отдаёт ошибки в едином формате.

## Требования
- Python 3.12+
- pip

## Установка
```bash
python3.12 -m venv .venv
source .venv/bin/activate

python -m pip install -U pip
python -m pip install -r requirements.txt
```

## Запуск
```bash
uvicorn app.main:app --reload
```

Swagger UI:
- http://127.0.0.1:8000/docs

## Переменные окружения
Настройки читаются из env (и/или из `.env`) и имеют значения по умолчанию.
- JSONPLACEHOLDER_BASE_URL (default: https://jsonplaceholder.typicode.com) — базовый URL внешнего API.
- HTTP_TIMEOUT (default: 5.0) — таймаут HTTP-запроса в секундах.
- HTTP_RETRIES (default: 3) — количество попыток (ретраи только на сетевые ошибки и 5xx).
- HTTP_BACKOFF (default: 0.3) — задержка между попытками (backoff).

## Эндпоинты (curl примеры)

### Healthcheck
```bash
curl "http://127.0.0.1:8000/api/v1/health"
```

```bash
curl "http://127.0.0.1:8000/api/v1/upstream/ping"
```

```bash
curl "http://127.0.0.1:8000/api/v1/posts?limit=2&start=0"
```

```bash
curl "http://127.0.0.1:8000/api/v1/posts/1"
```

```bash
curl "http://127.0.0.1:8000/api/v1/posts/search?q=qui&limit=10&start=0"
```

```bash
curl -i "http://127.0.0.1:8000/api/v1/posts?limit=999"
```

## Формат ошибок
Любая ошибка возвращается в едином формате:
```json
{
  "error": {
    "code": "SOME_CODE",
    "message": "Human readable message",
    "details": {}
  }
}
```

```bash
curl -i "http://127.0.0.1:8000/api/v1/posts?limit=999"
```