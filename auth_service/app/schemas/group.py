from typing import List
from pydantic import BaseModel
from app.schemas.permission import PermissionOut
from app.schemas.user import UserBasic

class GroupCreate(BaseModel):
    name: str
    permission_ids: list[int]


class GroupOut(BaseModel):
    id: int
    name: str
    permissions: list[PermissionOut]

    class Config:
        orm_mode = True

class GroupWithUsers(BaseModel):
    id: int
    name: str
    users: List[UserBasic]

    class Config:
        orm_mode = True


