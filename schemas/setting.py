from pydantic import BaseModel

class ConfigurationBase(BaseModel):
    name: str
    description: str
    key: str
    value: str

class ConfigurationResponse(ConfigurationBase):
    id: int


class ConfigurationUpdate(BaseModel):
    value: str