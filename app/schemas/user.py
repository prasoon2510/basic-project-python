from pydantic import BaseModel, ConfigDict, EmailStr


class UserCreate(BaseModel):

    zitadel_user_id: str

    email: EmailStr

    full_name: str

    role: str = "CUSTOMER"


class UserResponse(BaseModel):

    id: int

    zitadel_user_id: str

    email: EmailStr

    full_name: str

    role: str

    model_config = ConfigDict(from_attributes=True)