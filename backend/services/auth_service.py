import os
from jose import jwt

from datetime import (
    datetime,
    timedelta,
    UTC
)


SECRET_KEY = os.getenv(
    "SECRET_KEY"
)

ALGORITHM = os.getenv(
    "ALGORITHM"
)

ACCESS_TOKEN_EXPIRE_MINUTES = 30


ADMIN_USERNAME = os.getenv(
    "ADMIN_USERNAME"
)

ADMIN_PASSWORD = os.getenv(
    "ADMIN_PASSWORD"
)


def authenticate_user(
    username: str,
    password: str
):

    return (
        username == ADMIN_USERNAME
        and
        password == ADMIN_PASSWORD
    )


def create_access_token(
    data: dict
):

    to_encode = data.copy()

    expire = datetime.now(
        UTC
    ) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    to_encode.update(
        {
            "exp": expire
        }
    )

    encoded_jwt = jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return encoded_jwt