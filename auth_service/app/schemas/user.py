from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    tenant: int
    
class UserBasic(BaseModel):
    id: int
    username: str

    class Config:
        orm_mode = True