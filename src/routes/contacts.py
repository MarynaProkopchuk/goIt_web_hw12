from fastapi import APIRouter, HTTPException, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.db import get_db
from src.entity.models import User

from src.repository import contacts as repositories_contacts
from src.schemas.contact import ContactSchema, ContactResponse, ContactUpdateSchema
from src.services.auth import auth_service

router = APIRouter(prefix="/contacts", tags=["contacts"])


@router.get("/", response_model=list[ContactResponse])
async def get_contacts(
    limit: int = Query(10, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db), user: User = Depends(auth_service.get_current_user)
):
    contacts = await repositories_contacts.get_contacts(limit, offset, db, user)
    return contacts


@router.get("/search", response_model=ContactResponse)
async def search_contact(
    name: str = Query(None, min_length=1, max_length=50),
    surname: str = Query(None, min_length=1, max_length=50),
    email: str = Query(None),
    db: AsyncSession = Depends(get_db),user: User = Depends(auth_service.get_current_user),
):
    if not any([name, surname, email]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one search parameter must be provided",
        )

    contact = await repositories_contacts.get_contact(name, surname, email, db, user)
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No contact found"
        )
    return contact


@router.post("/", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
async def create_contact(body: ContactSchema, db: AsyncSession = Depends(get_db), user: User = Depends(auth_service.get_current_user),):
    contact = await repositories_contacts.create_contact(body, db, user)
    return contact


@router.patch("/update", response_model=ContactResponse)
async def update_contact(
    body: ContactUpdateSchema,
    name: str = Query(None, min_length=1, max_length=50),
    surname: str = Query(None, min_length=1, max_length=50),
    email: str = Query(None),
    db: AsyncSession = Depends(get_db), user: User = Depends(auth_service.get_current_user),
):
    if not any([name, surname, email]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one search parameter must be provided",
        )

    contact = await repositories_contacts.get_contact(name, surname, email, db, user)
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No contact found"
        )

    updated_contact = await repositories_contacts.update_contact(contact.id, body, db, user)
    if not updated_contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found"
        )
    return updated_contact


@router.delete("/delete", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact(
    name: str = Query(None, min_length=1, max_length=50),
    surname: str = Query(None, min_length=1, max_length=50),
    email: str = Query(None),
    db: AsyncSession = Depends(get_db), user: User = Depends(auth_service.get_current_user),
):
    if not any([name, surname, email]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one search parameter must be provided",
        )
    contact = await repositories_contacts.get_contact(name, surname, email, db, user)
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No contact found"
        )
    await repositories_contacts.delete_contact(contact.id, db, user)
    return None


@router.get("/birthdays", response_model=list[ContactResponse])
async def get_upcoming_birthdays(db: AsyncSession = Depends(get_db), user: User = Depends(auth_service.get_current_user),):
    contacts = await repositories_contacts.get_upcoming_birthdays(db, user)
    if not contacts:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No contacts with upcoming birthdays found",
        )
    return contacts
