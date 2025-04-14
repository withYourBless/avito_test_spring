from datetime import datetime
from unittest.mock import patch

import pytest
from pydantic import StrictStr  # noqa: F401
from typing import Any  # noqa: F401

from src.Exceptions import UserLoginException, UserPasswordException, UserRegisterException, ReceptionException, \
    PVZException
from src.endpoints.models.dummy_login_post_request import DummyLoginPostRequest
from src.endpoints.models.login_post_request import LoginPostRequest
from src.endpoints.models.product import Product
from src.endpoints.models.products_post_request import ProductsPostRequest
from src.endpoints.models.pvz import PVZ
from src.endpoints.models.pvz_get200_response_inner import PvzGet200ResponseInner
from src.endpoints.models.pvz_get200_response_inner_receptions_inner import PvzGet200ResponseInnerReceptionsInner
from src.endpoints.models.reception import Reception
from src.endpoints.models.receptions_post_request import ReceptionsPostRequest
from src.endpoints.models.register_post_request import RegisterPostRequest
from src.endpoints.security_api import decode_token, get_password_hash

from src.logic.default_api_base import MyBaseApi
from unittest import IsolatedAsyncioTestCase

from src.logic.extra_models import TokenModel
from src.repository import dto


class TestLogic(IsolatedAsyncioTestCase):
    async def test_login_post(self):
        with (patch('src.logic.default_api_base.get_user_by_email') as get_user_by_email):
            hash_password = get_password_hash('password')
            get_user_by_email.return_value = dto.UserOut(id='1', email='email', password=hash_password,
                                                         role='moderator')
            service = MyBaseApi()
            auth = await service.login_post(LoginPostRequest(email='email', password='password'))

            dec_token = decode_token(auth)

            assert dec_token.email == 'email'
            assert get_user_by_email.call_count == 1

    async def test_login_post_user_login_exception(self):
        with (patch('src.logic.default_api_base.get_user_by_email') as get_user_by_email):
            hash_password = get_password_hash('falsepassword')
            get_user_by_email.return_value = dto.UserOut(id='1', email='email', password=hash_password,
                                                         role='moderator')

            service = MyBaseApi()
            with pytest.raises(UserPasswordException):
                await service.login_post(LoginPostRequest(email='email', password='password'))

    async def test_login_post_user_password_exception(self):
        with (patch('src.logic.default_api_base.get_user_by_email') as get_user_by_email):
            get_user_by_email.return_value = None

            service = MyBaseApi()
            with pytest.raises(UserLoginException):
                await service.login_post(LoginPostRequest(email='email', password='password'))

    async def test_dummy_login_post_moderator(self):
        service = MyBaseApi()
        dummy_login = await service.dummy_login_post(DummyLoginPostRequest(role='moderator'))

        dec_token = decode_token(dummy_login)

        assert dec_token.role == 'moderator'

    async def test_dummy_login_post_employee(self):
        service = MyBaseApi()
        dummy_login = await service.dummy_login_post(DummyLoginPostRequest(role='employee'))

        dec_token = decode_token(dummy_login)

        assert dec_token.role == 'employee'

    async def test_register_post(self):
        with (patch('src.logic.default_api_base.get_user_by_email') as get_user_by_email,
              patch('src.logic.default_api_base.create_user') as create_user):
            get_user_by_email.return_value = None
            create_user.return_value = '2'
            service = MyBaseApi()
            user = RegisterPostRequest(email='email2', password='password', role='employee')

            new_user = await service.register_post(user)

            assert new_user.email == user.email
            assert new_user.role == 'employee'
            assert get_user_by_email.call_count == 1
            assert create_user.call_count == 1

    async def test_register_post_user_register_exception(self):
        with (patch('src.logic.default_api_base.get_user_by_email') as get_user_by_email,
              patch('src.logic.default_api_base.create_user') as create_user):
            hash_password = get_password_hash('password')
            get_user_by_email.return_value = dto.UserOut(id='1', email='email', password=hash_password,
                                                         role='moderator')
            create_user.return_value = '2'
            service = MyBaseApi()
            user = RegisterPostRequest(email='email2', password='password', role='employee')

            with pytest.raises(UserRegisterException):
                await service.register_post(user)

    async def test_product_post(self):
        with (patch('src.logic.default_api_base.open_receptions') as open_receptions,
              patch('src.logic.default_api_base.add_product') as add_product):
            open_receptions.return_value = [
                ('1', '1', 'in_progress', '2025-04-14 12:00:00')
            ]
            add_product.return_value = {
                'new_product_id': '1',
                'reception_id': '1',
                'received_datetime': '2025-04-14'}

            service = MyBaseApi()

            product = ProductsPostRequest(
                type="одежда",
                pvz_id='1'
            )
            token_model = TokenModel(
                user_id='1',
                email='email',
                role='employee',
            )

            new_product = await service.products_post(product, token_model)

            assert new_product.type == product.type
            assert open_receptions.call_count == 1
            assert add_product.call_count == 1

    async def test_product_post_user_login_exception(self):
        with (patch('src.logic.default_api_base.open_receptions') as open_receptions,
              patch('src.logic.default_api_base.add_product') as add_product):
            open_receptions.return_value = [
                ('1', '1', 'in_progress', '2025-04-14 12:00:00')
            ]
            add_product.return_value = {
                'new_product_id': '1',
                'reception_id': '1',
                'received_datetime': '2025-04-14'}

            service = MyBaseApi()

            product = ProductsPostRequest(
                type="одежда",
                pvz_id='1'
            )
            token_model = TokenModel(
                user_id='1',
                email='email',
                role='moderator',
            )

            with pytest.raises(UserLoginException):
                await service.products_post(product, token_model)

    async def test_product_post_reception_exception(self):
        with (patch('src.logic.default_api_base.open_receptions') as open_receptions,
              patch('src.logic.default_api_base.add_product') as add_product):
            open_receptions.return_value = []
            add_product.return_value = {
                'new_product_id': '1',
                'reception_id': '1',
                'received_datetime': '2025-04-14'}

            service = MyBaseApi()

            product = ProductsPostRequest(
                type="одежда",
                pvz_id='1'
            )
            token_model = TokenModel(
                user_id='1',
                email='email',
                role='employee',
            )

            with pytest.raises(ReceptionException):
                await service.products_post(product, token_model)

    async def test_pvz_get(self):
        with (patch('src.logic.default_api_base.get_pvz') as get_pvz):
            get_pvz.return_value = [
                PvzGet200ResponseInner(
                    pvz=PVZ(id='1', registration_date='2025-01-01', city='Москва'),
                    receptions=[
                        PvzGet200ResponseInnerReceptionsInner(
                            reception=Reception(id='1', date_time='2025-04-14 12:00:00', pvz_id='1',
                                                status='in_progress'),
                            products=[
                                Product(id='1', date_time=datetime(2025, 4, 14, 12, 0, 0), type='одежда',
                                        reception_id='1')
                            ]
                        ),
                        PvzGet200ResponseInnerReceptionsInner(
                            reception=Reception(id='2', date_time='2025-04-14 13:00:00', pvz_id='1', status='close'),
                            products=[
                                Product(id='2', date_time=datetime(2025, 4, 14, 13, 0, 0), type='обувь',
                                        reception_id='2')
                            ]
                        )
                    ]
                ),
                PvzGet200ResponseInner(
                    pvz=PVZ(id='2', registration_date='2025-02-01', city='Санкт-Петербург'),
                    receptions=[
                        PvzGet200ResponseInnerReceptionsInner(
                            reception=Reception(id='3', date_time='2025-04-13 12:00:00', pvz_id='2',
                                                status='in_progress'),
                            products=[
                                Product(id='3', date_time=datetime(2025, 4, 13, 12, 0, 0), type='электроника',
                                        reception_id='3')
                            ]
                        )
                    ]
                )
            ]

            service = MyBaseApi()

            token_model = TokenModel(
                user_id='1',
                email='email',
                role='employee',
            )

            pvz = await service.pvz_get(token_model, datetime.strptime('2025-04-13', '%Y-%m-%d'),
                                        datetime.strptime('2025-04-14', '%Y-%m-%d'), 1, 2)
            assert get_pvz.call_count == 1
            assert pvz != []

    async def test_pvz_get_user_login_exception(self):
        with (patch('src.logic.default_api_base.get_pvz') as get_pvz):
            get_pvz.return_value = [
                PvzGet200ResponseInner(
                    pvz=PVZ(id='1', registration_date='2025-01-01', city='Москва'),
                    receptions=[
                        PvzGet200ResponseInnerReceptionsInner(
                            reception=Reception(id='1', date_time='2025-04-14 12:00:00', pvz_id='1',
                                                status='in_progress'),
                            products=[
                                Product(id='1', date_time=datetime(2025, 4, 14, 12, 0, 0), type='одежда',
                                        reception_id='1')
                            ]
                        ),
                        PvzGet200ResponseInnerReceptionsInner(
                            reception=Reception(id='2', date_time='2025-04-14 13:00:00', pvz_id='1', status='close'),
                            products=[
                                Product(id='2', date_time=datetime(2025, 4, 14, 13, 0, 0), type='обувь',
                                        reception_id='2')
                            ]
                        )
                    ]
                )
            ]

            service = MyBaseApi()

            token_model = TokenModel(
                user_id='1',
                email='email',
                role='',
            )

            with pytest.raises(UserLoginException):
                await service.pvz_get(token_model, datetime.strptime('2025-04-13', '%Y-%m-%d'),
                                      datetime.strptime('2025-04-14', '%Y-%m-%d'), 1, 2)

    async def test_pvz_post(self):
        with (patch('src.logic.default_api_base.add_pvz') as add_pvz):
            add_pvz.return_value = '2'

            service = MyBaseApi()

            token_model = TokenModel(
                user_id='1',
                email='email',
                role='moderator',
            )

            pvz = PVZ(id='2', registration_date='2025-04-14', city='Москва')

            new_pvz = await service.pvz_post(pvz, token_model)

            assert add_pvz.call_count == 1
            assert new_pvz.id == pvz.id

    async def test_pvz_post_user_login_exception(self):
        with (patch('src.logic.default_api_base.add_pvz') as add_pvz):
            add_pvz.return_value = '2'

            service = MyBaseApi()

            token_model = TokenModel(
                user_id='1',
                email='email',
                role='employee',
            )

            pvz = PVZ(id='2', registration_date='2025-04-14', city='Москва')

            with pytest.raises(UserLoginException):
                await service.pvz_post(pvz, token_model)

    async def test_pvz_post_pvz_exception(self):
        with (patch('src.logic.default_api_base.add_pvz') as add_pvz):
            add_pvz.return_value = None

            service = MyBaseApi()

            token_model = TokenModel(
                user_id='1',
                email='email',
                role='moderator',
            )

            pvz = PVZ(id='2', registration_date='2025-04-14', city='Москва')

            with pytest.raises(PVZException):
                await service.pvz_post(pvz, token_model)

    async def test_pvz_id_close_last_reception_post(self):
        with (patch('src.logic.default_api_base.close_last_reception') as close_last_reception,
              patch('src.logic.default_api_base.open_receptions') as open_receptions):
            close_last_reception.return_value = Reception(
                id='1',
                date_time=datetime.strptime('2025-04-13', '%Y-%m-%d'),
                pvz_id='1',
                status="close")
            open_receptions.return_value = [
                ('1', '1', 'in_progress', '2025-04-14 12:00:00')
            ]

            service = MyBaseApi()

            token_model = TokenModel(
                user_id='1',
                email='email',
                role='employee',
            )

            reception = await service.pvz_pvz_id_close_last_reception_post('1', token_model)

            assert close_last_reception.call_count == 1
            assert open_receptions.call_count == 1
            assert reception.id == "1"
            assert reception.pvz_id == "1"

    async def test_pvz_id_close_last_reception_post_user_login_exception(self):
        with (patch('src.logic.default_api_base.close_last_reception') as close_last_reception,
              patch('src.logic.default_api_base.open_receptions') as open_receptions):
            close_last_reception.return_value = Reception(
                id='1',
                date_time=datetime.strptime('2025-04-13', '%Y-%m-%d'),
                pvz_id='1',
                status="close")
            open_receptions.return_value = [
                ('1', '1', 'in_progress', '2025-04-14 12:00:00')
            ]

            service = MyBaseApi()

            token_model = TokenModel(
                user_id='1',
                email='email',
                role='moderator',
            )

            with pytest.raises(UserLoginException):
                await service.pvz_pvz_id_close_last_reception_post('1', token_model)

    async def test_pvz_id_close_last_reception_post_reception_exception(self):
        with (patch('src.logic.default_api_base.close_last_reception') as close_last_reception,
              patch('src.logic.default_api_base.open_receptions') as open_receptions):
            close_last_reception.return_value = []
            open_receptions.return_value = []

            service = MyBaseApi()

            token_model = TokenModel(
                user_id='1',
                email='email',
                role='employee',
            )

            with pytest.raises(ReceptionException):
                await service.pvz_pvz_id_close_last_reception_post('1', token_model)

    async def test_pvz_id_delete_last_product_post(self):
        with (patch('src.logic.default_api_base.open_receptions') as open_receptions,
              patch('src.logic.default_api_base.delete_last_product_pos') as delete_last_product_pos):
            open_receptions.return_value = [
                ('1', '1', 'in_progress', '2025-04-14 12:00:00')
            ]
            delete_last_product_pos.return_value = "1"

            token_model = TokenModel(
                user_id='1',
                email='email',
                role='employee',
            )

            service = MyBaseApi()

            await service.pvz_pvz_id_delete_last_product_post('1', token_model)

            assert delete_last_product_pos.call_count == 1
            assert open_receptions.call_count == 1

    async def test_receptions_post(self):
        with (patch('src.logic.default_api_base.open_receptions') as open_receptions,
              patch('src.logic.default_api_base.add_reception') as add_reception):
            open_receptions.return_value = []
            add_reception.return_value = "1"

            token_model = TokenModel(
                user_id='1',
                email='email',
                role='employee',
            )

            reception = ReceptionsPostRequest(pvz_id="2")

            service = MyBaseApi()

            reception = await service.receptions_post(reception, token_model)

            assert open_receptions.call_count == 1
            assert add_reception.call_count == 1
            assert reception.id == "1"
            assert reception.pvz_id == "2"
