from sqlalchemy.ext.asyncio import AsyncSession
from schemas.branch import BranchCreate, BranchUpdate
from models import Branch
from sqlalchemy.future import select

class BranchService:
    @staticmethod
    async def create_branch(db: AsyncSession, branch_data: BranchCreate):
        db_branch = Branch(**branch_data.dict())
        db.add(db_branch)
        await db.commit()
        await db.refresh(db_branch)
        return db_branch

    @staticmethod
    async def get_branch(db: AsyncSession, branch_id: int):
        result = await db.execute(select(Branch).filter(Branch.id == branch_id))
        return result.scalars().first()

    @staticmethod
    async def get_all_branches(db: AsyncSession, skip: int = 0, limit: int = 100):
        result = await db.execute(select(Branch).offset(skip).limit(limit))
        return result.scalars().all()

    @staticmethod
    async def update_branch(db: AsyncSession, branch_id: int, branch_data: BranchUpdate):
        db_branch = await BranchService.get_branch(db, branch_id)
        if not db_branch:
            return None
        
        update_data = branch_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_branch, key, value)
            
        await db.commit()
        await db.refresh(db_branch)
        return db_branch

    @staticmethod
    async def delete_branch(db: AsyncSession, branch_id: int):
        db_branch = await BranchService.get_branch(db, branch_id)
        if not db_branch:
            return None
        
        await db.delete(db_branch)
        await db.commit()
        return db_branch