from fastapi import APIRouter, HTTPException, Depends, status, Query, Security
from fastapi.security import OAuth2PasswordRequestForm, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db

from src.repository import users as repositories_users
from src.schemas.user import UserSchema, UserResponse, TokenSchema
from src.services.auth import auth_service


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def signup(body: UserSchema, db: AsyncSession = Depends(get_db)):
        exist_user = await repositories_users.get_user_by_email(body.email, db)
        if exist_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Account already exists"
            )
        else:
            body.password = auth_service.get_password_hash(body.password)
            new_user = await repositories_users.create_user(body, db)
            return new_user


@router.post("/login")
async def login(body: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    user = await repositories_users.get_user_by_email(body.username, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email")
    if not auth_service.verify_password(body.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password")
    # Generate JWT
    access_token = await auth_service.create_access_token(data={"sub": user.email})
    refresh_token = await auth_service.create_refresh_token(data={"sub": user.email})
    await repositories_users.update_token(user, refresh_token, db)
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@router.get("/refresh_token")
async def refresh_token(
    credentials: HTTPAuthorizationCredentials = Security(),
    db: AsyncSession = Depends(get_db),
):
    pass
    return {}
