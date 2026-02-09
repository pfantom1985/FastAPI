from functools import lru_cache
import requests
from fastapi import Depends, Request
from app.clients.http import HttpClient, HttpClientConfig
from app.core.config import Settings
from app.services.jsonplaceholder import JsonPlaceholderService

@lru_cache
def get_settings() -> Settings:
    return Settings()

def get_http_session(request: Request) -> requests.Session:
    return request.app.state.http_session

def get_http_client(
    settings: Settings = Depends(get_settings),
    session: requests.Session = Depends(get_http_session),
) -> HttpClient:
    config = HttpClientConfig(
        timeout=settings.HTTP_TIMEOUT,
        retries=settings.HTTP_RETRIES,
        backoff=settings.HTTP_BACKOFF,
    )
    return HttpClient(session=session, config=config)

def get_jsonplaceholder_service(
    settings: Settings = Depends(get_settings),
    client: HttpClient = Depends(get_http_client),
) -> JsonPlaceholderService:
    return JsonPlaceholderService(client=client, settings=settings)
