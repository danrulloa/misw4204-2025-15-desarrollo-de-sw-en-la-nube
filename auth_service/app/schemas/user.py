from pydantic import BaseModel, EmailStr, model_validator
from typing import Optional


class UserCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    city: Optional[str] = None
    country: Optional[str] = None
    password1: str
    password2: str

    @model_validator(mode="after")
    def _validate_passwords(self):
        if self.password1 != self.password2:
            raise ValueError("Las contraseñas no coinciden.")
        if len(self.password1) < 8:
            raise ValueError("La contraseña debe tener al menos 8 caracteres.")
        return self

    def to_create_dict(self) -> dict:
        """Normaliza el payload a lo que normalmente guardas en DB."""
        return {
            "username": self.username or self.email.split("@", 1)[0],
            "email": self.email,
            "password": self.password1,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "city": self.city,
            "country": self.country,
        }

class UserBasic(BaseModel):
    id: int
    username: str

    class Config:
        orm_mode = True