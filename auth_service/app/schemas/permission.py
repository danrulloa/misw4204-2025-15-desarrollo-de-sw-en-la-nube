from pydantic import BaseModel

class PermissionCreate(BaseModel):
    name: str
    description: str

class PermissionOut(BaseModel):
    id: int
    name: str
    description: str

    class Config:
        orm_mode = True
