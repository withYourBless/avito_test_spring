# coding: utf-8
from typing import ClassVar, Dict, List, Tuple, Optional  # noqa: F401

from datetime import datetime

from fastapi import (  # noqa: F401
    HTTPException,
    status
)
from pydantic import Field, StrictStr
from typing_extensions import Annotated

from src.Exceptions import UserLoginException, ReceptionException, PVZException, UserRegisterException, \
    UserPasswordException
from src.endpoints.models.dummy_login_post_request import DummyLoginPostRequest
from src.endpoints.models.login_post_request import LoginPostRequest
from src.endpoints.models.register_post_request import RegisterPostRequest
from src.endpoints.models.user import User
from src.endpoints.security_api import get_password_hash, create_test_access_token, create_access_token, verify_password
from src.logic.extra_models import TokenModel
from src.endpoints.models.product import Product
from src.endpoints.models.products_post_request import ProductsPostRequest
from src.endpoints.models.pvz import PVZ
from src.endpoints.models.pvz_get200_response_inner import PvzGet200ResponseInner
from src.endpoints.models.reception import Reception
from src.endpoints.models.receptions_post_request import ReceptionsPostRequest
from src.repository.repositories import get_user_by_email, add_reception, add_pvz, \
    add_product, close_last_reception, delete_last_product_pos, open_receptions, get_pvz, create_user


class BaseDefaultApi:
    subclasses: ClassVar[Tuple] = ()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        BaseDefaultApi.subclasses = BaseDefaultApi.subclasses + (cls,)


class MyBaseApi(BaseDefaultApi):
    async def dummy_login_post(
            self,
            dummy_login_post_request: DummyLoginPostRequest,
    ) -> str:
        token = create_test_access_token(
            data={"role": dummy_login_post_request.role}
        )
        return token

    async def login_post(
            self,
            login_post_request: LoginPostRequest,
    ) -> str:
        email = login_post_request.email
        password = login_post_request.password

        user = get_user_by_email(email)
        if user:
            hashed_password = user.password
        else:
            raise UserLoginException

        if not verify_password(password, hashed_password):
            raise UserPasswordException

        token = create_access_token(
            data={"email": email, "user_id": user.id, "role": user.role}
        )

        return token

    async def register_post(
            self,
            register_post_request: RegisterPostRequest,
    ) -> User:
        email = register_post_request.email
        password = register_post_request.password
        role = register_post_request.role
        hashed_password = get_password_hash(password)
        if get_user_by_email(email):
            raise UserRegisterException
        user_id = create_user(email, hashed_password, role)

        return User(id=user_id, email=email, role=role)

    async def products_post(
            self,
            products_post_request: ProductsPostRequest,
            token_model: TokenModel,
    ) -> Product:
        if token_model.role != "employee":
            raise UserLoginException
        if not open_receptions(products_post_request.pvz_id):
            raise ReceptionException
        product_type = products_post_request.type
        pvz_id = products_post_request.pvz_id
        db_info = add_product(product_type, pvz_id)
        return Product(id=db_info['new_product_id'], date_time=db_info['received_datetime'], type=product_type,
                       reception_id=db_info['reception_id'])

    async def pvz_get(
            self,
            token_model: TokenModel,
            start_date: Annotated[Optional[datetime], Field(description="Начальная дата диапазона")],
            end_date: Annotated[Optional[datetime], Field(description="Конечная дата диапазона")],
            page: Annotated[Optional[Annotated[int, Field(strict=True, ge=1)]], Field(description="Номер страницы")],
            limit: Annotated[Optional[Annotated[int, Field(le=30, strict=True, ge=1)]], Field(
                description="Количество элементов на странице")],
    ) -> List[PvzGet200ResponseInner]:
        if token_model.role not in ["employee", "moderator"]:
            raise UserLoginException
        offset = (page - 1) * limit
        pvzs = get_pvz(start_date, end_date, limit, offset)
        return pvzs

    async def pvz_post(
            self,
            pvz: PVZ,
            token_model: TokenModel,
    ) -> PVZ:
        if token_model.role != "moderator":
            raise UserLoginException

        result = add_pvz(pvz.id, pvz.registration_date, pvz.city)
        if not result:
            raise PVZException
        return pvz

    async def pvz_pvz_id_close_last_reception_post(
            self,
            pvzId: StrictStr,
            token_model: TokenModel,
    ) -> Reception:
        if token_model.role != "employee":
            raise UserLoginException

        if not open_receptions(pvzId):
            raise ReceptionException
        info = close_last_reception(pvzId)
        return Reception(id=info.id,
                         date_time=info.date_time,
                         pvzId=info.pvz_id,
                         status=info.status)

    async def pvz_pvz_id_delete_last_product_post(
            self,
            pvzId: StrictStr,
            token_model: TokenModel,
    ) -> None:
        if token_model.role != "employee":
            raise UserLoginException
        if not open_receptions(pvzId):
            raise ReceptionException

        if not delete_last_product_pos(pvzId):
            raise ReceptionException

    async def receptions_post(
            self,
            receptions_post_request: ReceptionsPostRequest,
            token_model: TokenModel,
    ) -> Reception:
        if token_model.role != "employee":
            raise UserLoginException

        if open_receptions(receptions_post_request.pvz_id):
            raise ReceptionException
        pvz_id = receptions_post_request.pvz_id
        datetime_now = datetime.now()
        reception_status = "in_progress"
        reception_id = add_reception(pvz_id, datetime_now, reception_status)
        return Reception(id=reception_id, date_time=datetime_now, pvz_id=pvz_id, status=reception_status)
