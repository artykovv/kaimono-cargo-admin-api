from pydantic import BaseModel, ConfigDict

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
    
    model_config = ConfigDict(from_attributes=True)