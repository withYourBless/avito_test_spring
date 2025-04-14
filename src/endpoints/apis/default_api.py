# coding: utf-8
from datetime import datetime
from typing import Dict, List, Annotated, Optional  # noqa: F401

from fastapi import (  # noqa: F401
    APIRouter,
    Body,
    Cookie,
    Depends,
    Form,
    Header,
    HTTPException,
    Path,
    Query,
    Response,
    Security,
    status,
)
from pydantic import StrictStr

from src.Exceptions import UserLoginException, ReceptionException, PVZException, UserPasswordException, \
    PVZCityException, UserRegisterException
from src.logic.default_api_base import BaseDefaultApi
from src.endpoints.models.dummy_login_post_request import DummyLoginPostRequest
from src.endpoints.models.error import Error
from src.logic.extra_models import TokenModel
from src.endpoints.models.login_post_request import LoginPostRequest
from src.endpoints.models.product import Product
from src.endpoints.models.products_post_request import ProductsPostRequest
from src.endpoints.models.pvz import PVZ
from src.endpoints.models.pvz_get200_response_inner import PvzGet200ResponseInner
from src.endpoints.models.reception import Reception
from src.endpoints.models.receptions_post_request import ReceptionsPostRequest
from src.endpoints.models.register_post_request import RegisterPostRequest
from src.endpoints.models.user import User
from src.endpoints.security_api import get_token_bearerAuth

router = APIRouter()


@router.post(
    "/dummyLogin",
    responses={
        200: {"model": str, "description": "Успешная авторизация"},
        400: {"model": Error, "description": "Неверный запрос"},
    },
    tags=["default"],
    summary="Получение тестового токена",
    response_model_by_alias=True,
)
async def dummy_login_post(
        dummy_login_post_request: DummyLoginPostRequest = Body(None, description=""),
) -> str:
    if not BaseDefaultApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    for subclass in BaseDefaultApi.subclasses:
        instance = subclass()
        if hasattr(instance, "dummy_login_post"):
            return await instance.dummy_login_post(dummy_login_post_request)


@router.post(
    "/login",
    responses={
        200: {"model": str, "description": "Успешная авторизация"},
        401: {"model": Error, "description": "Неверные учетные данные"},
    },
    tags=["default"],
    summary="Авторизация пользователя",
    response_model_by_alias=True,
)
async def login_post(
        login_post_request: LoginPostRequest = Body(None, description=""),
) -> str:
    if not BaseDefaultApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    try:
        for subclass in BaseDefaultApi.subclasses:
            instance = subclass()
            if hasattr(instance, "login_post"):
                return await instance.login_post(login_post_request)
    except UserLoginException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=Error(message="Неверные учетные данные").model_dump(),
        )
    except UserPasswordException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=Error(message="Неверный пароль").model_dump(),
        )


@router.post(
    "/products",
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"model": Product, "description": "Товар добавлен"},
        400: {"model": Error, "description": "Неверный запрос или нет активной приемки"},
        403: {"model": Error, "description": "Доступ запрещен"},
    },
    tags=["default"],
    summary="Добавление товара в текущую приемку (только для сотрудников ПВЗ)",
    response_model_by_alias=True,
)
async def products_post(
        products_post_request: ProductsPostRequest = Body(None, description=""),
        token_bearerAuth: TokenModel = Security(
            get_token_bearerAuth
        ),
) -> Product:
    if not BaseDefaultApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    try:
        return await BaseDefaultApi.subclasses[0]().products_post(products_post_request, token_bearerAuth)
    except UserLoginException:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=Error(message="Доступ запрещен").model_dump(),
        )
    except ReceptionException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=Error(message="Неверный запрос или нет активной приемки").model_dump()
        )


@router.get(
    "/pvz",
    responses={
        200: {"model": List[PvzGet200ResponseInner], "description": "Список ПВЗ"},
        403: {"model": Error, "description": "Доступ запрещен"},
    },
    tags=["default"],
    summary="Получение списка ПВЗ с фильтрацией по дате приемки и пагинацией",
    response_model_by_alias=True,
)
async def pvz_get(
        start_date: Optional[datetime] = Query(None, alias="startDate", description="Начальная дата диапазона"),
        end_date: Optional[datetime] = Query(None, alias="endDate", description="Конечная дата диапазона"),
        page: int = Query(1, alias="page", ge=1, description="Номер страницы"),
        limit: int = Query(10, alias="limit", ge=1, le=30, description="Количество элементов на странице"),

        token_bearerAuth: TokenModel = Security(
            get_token_bearerAuth
        ),
) -> List[PvzGet200ResponseInner]:
    if not BaseDefaultApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    try:
        return await BaseDefaultApi.subclasses[0]().pvz_get(token_bearerAuth, start_date, end_date, page, limit)
    except UserLoginException:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=Error(message="Доступ запрещен").model_dump()
        )


@router.post(
    "/pvz",
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"model": PVZ, "description": "ПВЗ создан"},
        400: {"model": Error, "description": "Неверный запрос"},
        403: {"model": Error, "description": "Доступ запрещен"},
    },
    tags=["default"],
    summary="Создание ПВЗ (только для модераторов)",
    response_model_by_alias=True,
)
async def pvz_post(
        pvz: PVZ = Body(None, description=""),
        token_bearerAuth: TokenModel = Security(
            get_token_bearerAuth
        ),
) -> PVZ:
    if not BaseDefaultApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    try:
        return await BaseDefaultApi.subclasses[0]().pvz_post(pvz, token_bearerAuth)
    except UserLoginException:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=Error(message="Доступ запрещен").model_dump()
        )
    except PVZException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=Error(message="ПВЗ с таким id уже существует").model_dump()
        )
    except PVZCityException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=Error(message="В этом городе сейчас нельзя открыть ПВЗ").model_dump()
        )


@router.post(
    "/pvz/{pvzId}/close_last_reception",
    responses={
        200: {"model": Reception, "description": "Приемка закрыта"},
        400: {"model": Error, "description": "Неверный запрос или приемка уже закрыта"},
        403: {"model": Error, "description": "Доступ запрещен"},
    },
    tags=["default"],
    summary="Закрытие последней открытой приемки товаров в рамках ПВЗ",
    response_model_by_alias=True,
)
async def pvz_pvz_id_close_last_reception_post(
        pvzId: StrictStr = Path(..., description=""),
        token_bearerAuth: TokenModel = Security(
            get_token_bearerAuth
        ),
) -> Reception:
    if not BaseDefaultApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    try:
        return await BaseDefaultApi.subclasses[0]().pvz_pvz_id_close_last_reception_post(pvzId, token_bearerAuth)
    except UserLoginException:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=Error(message="Доступ запрещен").model_dump()
        )
    except ReceptionException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=Error(message="Неверный запрос или приемка уже закрыта").model_dump()
        )


@router.post(
    "/pvz/{pvzId}/delete_last_product",
    responses={
        200: {"description": "Товар удален"},
        400: {"model": Error, "description": "Неверный запрос, нет активной приемки или нет товаров для удаления"},
        403: {"model": Error, "description": "Доступ запрещен"},
    },
    tags=["default"],
    summary="Удаление последнего добавленного товара из текущей приемки (LIFO, только для сотрудников ПВЗ)",
    response_model_by_alias=True,
)
async def pvz_pvz_id_delete_last_product_post(
        pvzId: StrictStr = Path(..., description=""),
        token_bearerAuth: TokenModel = Security(
            get_token_bearerAuth
        ),
) -> None:
    if not BaseDefaultApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    try:
        return await BaseDefaultApi.subclasses[0]().pvz_pvz_id_delete_last_product_post(pvzId, token_bearerAuth)
    except UserLoginException:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=Error(message="Доступ запрещен").model_dump()
        )
    except ReceptionException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=Error(message="Неверный запрос, нет активной приемки или нет товаров для удаления").model_dump()
        )


@router.post(
    "/receptions",
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"model": Reception, "description": "Приемка создана"},
        400: {"model": Error, "description": "Неверный запрос или есть незакрытая приемка"},
        403: {"model": Error, "description": "Доступ запрещен"},
    },
    tags=["default"],
    summary="Создание новой приемки товаров (только для сотрудников ПВЗ)",
    response_model_by_alias=True,
)
async def receptions_post(
        receptions_post_request: ReceptionsPostRequest = Body(None, description=""),
        token_bearerAuth: TokenModel = Security(
            get_token_bearerAuth
        ),
) -> Reception:
    if not BaseDefaultApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    try:
        return await BaseDefaultApi.subclasses[0]().receptions_post(receptions_post_request, token_bearerAuth)
    except UserLoginException:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=Error(message="Доступ запрещен").model_dump()
        )
    except ReceptionException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=Error(message="Неверный запрос или есть незакрытая приемка").model_dump()
        )


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"model": User, "description": "Пользователь создан"},
        400: {"model": Error, "description": "Неверный запрос"},
    },
    tags=["default"],
    summary="Регистрация пользователя",
    response_model_by_alias=True,
)
async def register_post(
        register_post_request: RegisterPostRequest = Body(None, description=""),
) -> User:
    if not BaseDefaultApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    try:
        for subclass in BaseDefaultApi.subclasses:
            instance = subclass()
            if hasattr(instance, "login_post"):
                return await instance.register_post(register_post_request)
    except UserRegisterException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=Error(message="Пользователь с таким email уже существует").model_dump()
        )
