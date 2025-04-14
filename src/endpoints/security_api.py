from datetime import datetime, timedelta, timezone

from fastapi import Depends, Security, HTTPException, status  # noqa: F401
from fastapi.openapi.models import OAuthFlowImplicit, OAuthFlows  # noqa: F401
from fastapi.security import (  # noqa: F401
    HTTPAuthorizationCredentials,
    HTTPBasic,
    HTTPBasicCredentials,
    HTTPBearer,
    OAuth2,
    OAuth2AuthorizationCodeBearer,
    OAuth2PasswordBearer,
    SecurityScopes,
)
from fastapi.security.api_key import APIKeyCookie, APIKeyHeader, APIKeyQuery  # noqa: F401
import jwt
from jwt import ExpiredSignatureError, InvalidTokenError
from passlib.context import CryptContext

from src.logic.extra_models import TokenModel

bearer_auth = HTTPBearer()


def get_token_bearerAuth(credentials: HTTPAuthorizationCredentials = Depends(bearer_auth)) -> TokenModel:
    """
    Check and retrieve authentication information from custom bearer token.

    :param credentials: Credentials provided by Authorization header
    :type credentials: HTTPAuthorizationCredentials
    :return: Decoded token information or None if token is invalid
    :rtype: TokenModel
    :raises HTTPException: If the token is invalid or missing
    """
    token = credentials.credentials
    return decode_token(token)


SECRET_KEY = "5956740c456fe634d0cc2ca44e5780698da88e5091c471ef756dc61a8559bb55"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 90

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password):
    return pwd_context.hash(password)


def verify_password(password, hashed_password):
    return pwd_context.verify(password, hashed_password)


def decode_token(token: str) -> TokenModel:
    """
    Декодирует и проверяет JWT токен.

    :param token: JWT токен для декодирования
    :return: Данные из токена (например, user_id, username, role)
    :raises: HTTPException, если токен невалидный
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        user_id = payload.get("user_id")
        email = payload.get("email")
        role = payload.get("role")

        if user_id is not None and email is not None and role is not None:
            return TokenModel(user_id=user_id, email=email, role=role)

        if role is not None and user_id is None and email is None:
            return TokenModel(role=role)

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    except jwt.PyJWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def create_access_token(data: dict):
    to_encode = data.copy()
    if ACCESS_TOKEN_EXPIRE_MINUTES:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire, "user_id": data["user_id"], "email": data["email"], "role": data["role"], })
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_test_access_token(data: dict):
    to_encode = data.copy()
    if ACCESS_TOKEN_EXPIRE_MINUTES:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire, "user_id": '', "email": '', "role": data["role"]})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt