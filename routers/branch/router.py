from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert, select

from config.database import get_async_session
from services.branch import BranchService
from schemas.branch import BranchResponse, BranchCreate, BranchUpdate
from models import User
from auth.fastapi_users_instance import fastapi_users


router = APIRouter(prefix="/branches", tags=["branches"])

# Create
@router.post("/", response_model=BranchResponse)
async def create_branch(
    branch: BranchCreate, 
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(fastapi_users.current_user(verified=True))
    ):
    db_branch = await BranchService.create_branch(db, branch)
    return db_branch

# Read (one)
@router.get("/{branch_id}", response_model=BranchResponse)
async def read_branch(branch_id: int, db: AsyncSession = Depends(get_async_session), current_user: User = Depends(fastapi_users.current_user(verified=True))):
    db_branch = await BranchService.get_branch(db, branch_id)
    if db_branch is None:
        raise HTTPException(status_code=404, detail="Branch not found")
    return db_branch

# Read (all)
@router.get("/", response_model=list[BranchResponse])
async def read_branches(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_async_session), current_user: User = Depends(fastapi_users.current_user(verified=True))):
    branches = await BranchService.get_all_branches(db, skip=skip, limit=limit)
    return branches

# Update
@router.patch("/{branch_id}", response_model=BranchResponse)
async def update_branch(branch_id: int, branch: BranchUpdate, db: AsyncSession = Depends(get_async_session), current_user: User = Depends(fastapi_users.current_user(verified=True))):
    db_branch = await BranchService.update_branch(db, branch_id, branch)
    if db_branch is None:
        raise HTTPException(status_code=404, detail="Branch not found")
    return db_branch

# Delete
@router.delete("/{branch_id}")
async def delete_branch(branch_id: int, db: AsyncSession = Depends(get_async_session), current_user: User = Depends(fastapi_users.current_user(verified=True))):
    db_branch = await BranchService.delete_branch(db, branch_id)
    if db_branch is None:
        raise HTTPException(status_code=404, detail="Branch not found")
    return {"message": "Branch deleted successfully"}