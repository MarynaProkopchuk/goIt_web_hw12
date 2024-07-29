from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db
from src.entity.models import User
from src.schemas.user import UserSchema



async def get_user_by_email(email: str, db: AsyncSession = Depends(get_db)):
    try:
        stmt = select(User).filter_by(email=email)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        return user
    except Exception as e:
        print(f"Error in get_user_by_email: {e}")
        raise


async def create_user(body: UserSchema, db: AsyncSession):
    try:
        new_user = User(**body.dict())
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        return new_user
    except Exception as e:
        print(f"Error in create_user: {e}")
        raise

async def update_token(user: User, token: str, db: AsyncSession):
    user.refresh_token = token
    await db.commit()