import uuid
from datetime import datetime, time

from pydantic import StrictStr

from src.endpoints.models.product import Product
from src.endpoints.models.pvz import PVZ
from src.endpoints.models.pvz_get200_response_inner import PvzGet200ResponseInner
from src.endpoints.models.pvz_get200_response_inner_receptions_inner import PvzGet200ResponseInnerReceptionsInner
from src.endpoints.models.reception import Reception
from src.repository import dto
from src.repository.db_connect import get_cursor

def create_user(email: str, password: str, role):
    user_id = str(uuid.uuid4())
    query = """INSERT INTO users (id, email, password, role)
    VALUES (%s, %s, %s, %s);"""
    with get_cursor() as cursor:
        cursor.execute(query, (user_id, email, password, role))
        cursor.connection.commit()
    return user_id


def get_user_by_email(email: StrictStr) -> dto.UserOut | None:
    query = """ SELECT * FROM users WHERE email=%s"""
    with get_cursor() as cursor:
        cursor.execute(query, (email,))
        user_info = cursor.fetchone()
    if not user_info:
        return None
    user = dto.UserOut(id=user_info[0], email=user_info[1], password=user_info[2], role=user_info[3])
    return user


def add_reception(pvz_id: StrictStr, timestamp: datetime, status: str) -> str:
    query = """INSERT INTO reception (id, reception_datetime, pvz_id, status)
    VALUES (%s, %s, %s, %s); """
    reception_id = str(uuid.uuid4())
    with get_cursor() as cursor:
        cursor.execute(query, (reception_id, timestamp, pvz_id, status))
        cursor.connection.commit()
    return reception_id


def close_last_reception(pvz_id: str) -> Reception:
    last_reception_id = open_receptions(pvz_id)[-1][0]
    products_query = """ SELECT * FROM product WHERE reception_id = %s"""
    with get_cursor() as cursor:
        cursor.execute(products_query, (last_reception_id,))
        products = cursor.fetchall()
        update_query = """UPDATE reception
        SET products = %s, status = 'close'
        WHERE pvz_id = %s;
        """
        cursor.execute(update_query, (products, pvz_id,))
        cursor.connection.commit()

        datetime_reception_query = """SELECT reception_datetime FROM reception
        WHERE pvz_id = %s
        ORDER BY reception_datetime DESC
        LIMIT 1"""
        cursor.execute(datetime_reception_query, (pvz_id,))
        date_time = cursor.fetchone()
    reception = Reception(id=last_reception_id,
                          date_time=date_time[0],
                          pvz_id=pvz_id,
                          status="close")

    return reception


def open_receptions(pvz_id: StrictStr):
    query = """SELECT * FROM reception 
    WHERE pvz_id = %s AND status = %s
    ORDER BY reception_datetime DESC
    LIMIT 1"""
    status = "in_progress"
    with get_cursor() as cursor:
        cursor.execute(query, (pvz_id, status,))

        return cursor.fetchall()

def check_pvz_exists_by_id(pvz_id):
    with get_cursor() as cursor:
        cursor.execute("SELECT 1 FROM pvz WHERE id = %s", (pvz_id,))
        return cursor.fetchone()

def add_pvz(pvz_id: str, reg_date: datetime, city: str) -> str | None:
    if check_pvz_exists_by_id(pvz_id):
        return None
    query = """INSERT INTO pvz (id, register_date, city)
    VALUES (%s, %s, %s)"""
    with get_cursor() as cursor:
        cursor.execute(query, (pvz_id, reg_date, city))
        cursor.connection.commit()
    return pvz_id


def add_product(product_type: str, pvz_id: str):
    new_product_id = str(uuid.uuid4())
    received_datetime = datetime.now()
    reception_id = open_receptions(pvz_id)[-1][0]
    query = """INSERT INTO product (id, received_datetime, product_type, reception_id)
    VALUES (%s, %s, %s, %s); """
    with get_cursor() as cursor:
        cursor.execute(query, (new_product_id, received_datetime, product_type, reception_id))
        cursor.connection.commit()
    return {'new_product_id': new_product_id, 'reception_id': reception_id, 'received_datetime': received_datetime}


def delete_last_product_pos(pvz_id: str):
    last_reception_id = open_receptions(pvz_id)[-1][0]
    query = """
    SELECT id FROM product where reception_id = %s
    ORDER BY received_datetime DESC
    LIMIT 1"""
    product_id = None
    with get_cursor() as cursor:
        cursor.execute(query, (last_reception_id,))
        product_id = cursor.fetchone()
        if product_id:
            query = """DELETE FROM product WHERE product_id = %s"""
            cursor.execute(query, (product_id,))
            cursor.connection.commit()
    return product_id


def get_pvz(start_date, end_date, limit, offset):
    query = """SELECT DISTINCT p.id,
                    p.register_date,
                    p.city,
                    r.id AS reception_id,
                    r.reception_datetime,
                    r.status,
                    r.products
                FROM pvz p
                JOIN reception r ON p.id = r.pvz_id
                WHERE (%(start_date)s IS NULL OR r.reception_datetime >= %(start_date)s)
                AND (%(end_date)s IS NULL OR r.reception_datetime <= %(end_date)s)
                ORDER BY p.id
                LIMIT %(limit)s OFFSET %(offset)s;
                """

    start_datetime = datetime.combine(start_date.date(), time.min) if start_date else None
    end_datetime = datetime.combine(end_date.date(), time.max) if end_date else None

    with get_cursor() as cursor:
        cursor.execute(query, {"start_date": start_datetime,
                               "end_date": end_datetime,
                               "limit": limit,
                               "offset": offset})

        rows = cursor.fetchall()

        column_names = [desc[0] for desc in cursor.description]

    grouped_data = {}

    for row in rows:
        row_dict = dict(zip(column_names, row))
        pvz_id = row_dict['id']

        if pvz_id not in grouped_data:
            grouped_data[pvz_id] = {
                'pvz': PVZ(
                    id=row_dict['id'],
                    registration_date=row_dict['register_date'],
                    city=row_dict['city']
                ),
                'receptions': []
            }

        products = []
        if row_dict['products']:
            for product in row_dict['products']:
                product = product[1:-1].split(',')
                products.append(
                    Product(
                        id=product[0],
                        date_time=datetime.strptime(product[1].strip('"'), "%Y-%m-%d %H:%M:%S.%f"),
                        type=product[2],
                        reception_id=product[3],
                    )
                )

        grouped_data[pvz_id]['receptions'].append(
            PvzGet200ResponseInnerReceptionsInner(
                reception=Reception(
                    id=row_dict['reception_id'],
                    date_time=row_dict['reception_datetime'],
                    pvz_id=pvz_id,
                    status=row_dict['status']
                ),
                products=products
            )
        )

    result = []
    for data in grouped_data.values():
        result.append(PvzGet200ResponseInner(
            pvz=data['pvz'],
            receptions=data['receptions']
        ))

    return result
