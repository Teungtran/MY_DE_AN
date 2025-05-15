from collections.abc import Generator
from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session

from config.base_config import APP_CONFIG
from services.postgres import engine

SECRET_KEY = "Xin chao"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


reusable_oauth2 = OAuth2PasswordBearer(tokenUrl=f"{APP_CONFIG.oauth_config.token_url}/login/access-token")


def get_db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_db)]
TokenDep = Annotated[str, Depends(reusable_oauth2)]


# def get_current_user(session: SessionDep, token: TokenDep) -> User:
#     try:
#         payload = jwt.decode(
#             token, SECRET_KEY, algorithms=[ALGORITHM]
#         )
#         token_data = TokenPayload(**payload)
#     except (InvalidTokenError, ValidationError):
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="Could not validate credentials",
#         )
#     user = session.get(User, token_data.sub)
#     if not user:
#         raise HTTPException(status_code=404, detail="User not found")
#     if not user.is_active:
#         raise HTTPException(status_code=400, detail="Inactive user")
#     return user


# CurrentUser = Annotated[User, Depends(get_current_user)]


# def get_current_active_superuser(current_user: CurrentUser) -> User:
#     if not current_user.is_superuser:
#         raise HTTPException(
#             status_code=403, detail="The user doesn't have enough privileges"
#         )
#     return current_user
