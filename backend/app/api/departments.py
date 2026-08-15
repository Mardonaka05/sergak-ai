"""Department CRUD"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from pydantic import BaseModel

from app.core.database import get_db
from app.models.department import Department

router = APIRouter()


class DeptIn(BaseModel):
    key: str
    name: str
    color: str = "#3b82f6"
    icon: str = "building-2"
    rules: dict = {}


class DeptOut(DeptIn):
    id: int
    class Config:
        from_attributes = True


@router.get("", response_model=List[DeptOut])
async def list_depts(db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Department))
    return res.scalars().all()


@router.post("", response_model=DeptOut, status_code=201)
async def create_dept(data: DeptIn, db: AsyncSession = Depends(get_db)):
    d = Department(**data.model_dump())
    db.add(d)
    await db.commit()
    await db.refresh(d)
    return d


@router.put("/{dept_id}", response_model=DeptOut)
async def update_dept(dept_id: int, data: DeptIn, db: AsyncSession = Depends(get_db)):
    d = await db.get(Department, dept_id)
    if not d: raise HTTPException(404, "Department not found")
    for k, v in data.model_dump().items(): setattr(d, k, v)
    await db.commit()
    await db.refresh(d)
    return d


@router.delete("/{dept_id}", status_code=204)
async def delete_dept(dept_id: int, db: AsyncSession = Depends(get_db)):
    d = await db.get(Department, dept_id)
    if not d: raise HTTPException(404, "Department not found")
    await db.delete(d)
    await db.commit()
