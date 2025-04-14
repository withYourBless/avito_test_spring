import os
from dotenv import load_dotenv

os.environ["ENVIRONMENT"] = "test"
load_dotenv(".env.test", override=True)

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from src.endpoints.main import app as application


@pytest.fixture
def app() -> FastAPI:
    application.dependency_overrides = {}
    return application


@pytest.fixture
def client(app) -> TestClient:
    return TestClient(app)
