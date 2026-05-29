from pydantic import BaseModel

class LoginSchema(BaseModel):
    email: str
    password: str

    class Config:
        from_attributes = True