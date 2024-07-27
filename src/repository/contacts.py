from typing import Optional
from datetime import datetime, timedelta
from sqlalchemy import select, update, extract, and_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.entity.models import Contact
from src.schemas.contact import ContactSchema, ContactUpdateSchema


async def get_contacts(limit: int, offset: int, db: AsyncSession):
    stmt = select(Contact).offset(offset).limit(limit)
    contacts = await db.execute(stmt)
    return contacts.scalars().all()


async def get_contact(name: str, surname: str, email: str, db: AsyncSession):
    query = select(Contact)

    if name:
        query = query.filter(Contact.name.ilike(f"%{name}%"))
    if surname:
        query = query.filter(Contact.surname.ilike(f"%{surname}%"))
    if email:
        query = query.filter(Contact.email.ilike(f"%{email}%"))

    contact = await db.execute(query)
    return contact.scalar_one_or_none()


async def create_contact(body: ContactSchema, db: AsyncSession):
    contact = Contact(**body.model_dump(exclude_unset=True))
    db.add(contact)
    await db.commit()
    await db.refresh(contact)
    return contact


async def update_contact(contact_id: int, body: ContactUpdateSchema, db: AsyncSession):
    update_data = body.dict(exclude_unset=True)
    stmt = (
        update(Contact)
        .where(Contact.id == contact_id)
        .values(**update_data)
        .execution_options(synchronize_session="fetch")
    )
    try:
        result = await db.execute(stmt)
        await db.commit()
    except SQLAlchemyError as e:
        await db.rollback()
        raise e

    if result.rowcount == 0:
        return None
    stmt = select(Contact).filter_by(id=contact_id)
    updated_contact = await db.execute(stmt)
    return updated_contact.scalar_one_or_none()


async def delete_contact(contact_id: int, db: AsyncSession):
    stmt = stmt = select(Contact).filter_by(id=contact_id)
    contact = await db.execute(stmt)
    contact = contact.scalar_one_or_none()
    if contact:
        await db.delete(contact)
        await db.commit()
    return contact


async def get_upcoming_birthdays(db: AsyncSession):
    today = datetime.today()
    today_month = today.month
    today_day = today.day

    next_week = today + timedelta(days=7)
    next_week_month = next_week.month
    next_week_day = next_week.day

    stmt = select(Contact).where(
        and_(
            (extract("month", Contact.birthday) == today_month)
            & (extract("day", Contact.birthday) >= today_day)
            | (extract("month", Contact.birthday) == next_week_month)
            & (extract("day", Contact.birthday) <= next_week_day)
            | (extract("month", Contact.birthday) > today_month)
            & (extract("month", Contact.birthday) < next_week_month)
        )
    )
    result = await db.execute(stmt)
    return result.scalars().all()
