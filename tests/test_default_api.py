# coding: utf-8
import random
from uuid import uuid4

import requests

from datetime import datetime  # noqa: F401
from pydantic import Field, StrictStr  # noqa: F401
from typing import Any, List, Optional, Dict  # noqa: F401

from requests import Response
from typing_extensions import Annotated  # noqa: F401

from src.endpoints.models.products_post_request import ProductsPostRequest
from src.endpoints.models.pvz import PVZ
from src.endpoints.models.receptions_post_request import ReceptionsPostRequest
from src.endpoints.security_api import create_access_token

base_url = "http://localhost:8080"


def get_moderator_token() -> str:
    token_model_moderator = {
        "user_id": "1",
        "email": "test_moderator@email",
        "role": "moderator"}

    moderator_token = create_access_token(token_model_moderator)

    return moderator_token


def get_employee_token() -> str:
    token_model_moderator = {
        "user_id": "2",
        "email": "test_employee@email",
        "role": "employee"}
    employee_token = create_access_token(token_model_moderator)
    return employee_token


def get_header(token: str) -> dict[str, str]:
    headers = {"Content-Type": "application/json",
               "Authorization": f"Bearer {token}"}
    return headers


def create_pvz(moderator_token: dict[str, str]) -> Response:
    """
    Создание нового ПВЗ
    """
    pvz = PVZ(
        id=str(uuid4()),
        registration_date=datetime.now(),
        city='Москва'
    )
    new_pvz_response = requests.post(base_url + "/pvz", data=pvz.to_json(), headers=moderator_token)

    return new_pvz_response


def add_new_reception(pvz_id: str, employee_token: dict[str, str]) -> Response:
    """
    Добавление новой приёмки заказов
    """
    reception = ReceptionsPostRequest(
        pvzId=pvz_id
    )
    new_reception_response = requests.post(base_url + "/receptions", json=reception.model_dump(by_alias=True), headers=employee_token)

    return new_reception_response


def add_product(product: ProductsPostRequest, employee_token: dict[str, str]) -> Response:
    """
    Добавление товара в рамках текущей приёмки заказов
    """
    new_product_response = requests.post(base_url + "/products", json=product.model_dump(by_alias=True), headers=employee_token)

    return new_product_response


def close_last_reception_post(pvz_id: str, employee_token: dict[str, str]) -> Response:
    """
    Закрытие приёмки заказов
    """
    url = f"{base_url}/pvz/{pvz_id}/close_last_reception"

    close_last_reception_response = requests.post(url, json={}, headers=employee_token)
    return close_last_reception_response


def test_full_cycle():
    moderator_header = get_header(get_moderator_token())

    pvz_response = create_pvz(moderator_header)
    assert pvz_response.status_code == 201

    pvz = PVZ.from_dict(pvz_response.json())

    employee_header = get_header(get_employee_token())
    reception_response = add_new_reception(pvz.id, employee_header)
    assert reception_response.status_code == 201

    products = ['электроника', 'одежда', 'обувь']
    for i in range(50):
        product_response = add_product(ProductsPostRequest(
            type=random.choice(products),
            pvzId=pvz.id,
            ),
            employee_header
        )
        assert product_response.status_code == 201

    close_last_reception_response = close_last_reception_post(pvz_id=pvz.id, employee_token=employee_header)
    assert close_last_reception_response.status_code == 200
