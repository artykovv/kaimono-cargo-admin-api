from pydantic import BaseModel

class BranchBase(BaseModel):
    name: str
    code: str
    address: str

class BranchCreate(BranchBase):
    pass

class BranchUpdate(BranchBase):
    name: str | None = None
    code: str | None = None
    address: str | None = None

class BranchResponse(BranchBase):
    id: int
    
    class Config:
        from_attributes = True  # Заменяет orm_mode в новых версиях Pydantic