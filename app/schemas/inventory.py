from pydantic import BaseModel, ConfigDict, Field


class InventoryCreate(BaseModel):

    product_id: int = Field(gt=0)

    quantity: int = Field(ge=0)

    reserved_quantity: int = Field(default=0, ge=0)


class InventoryUpdate(BaseModel):

    quantity: int | None = Field(default=None, ge=0)

    reserved_quantity: int | None = Field(default=None, ge=0)


class InventoryResponse(BaseModel):

    id: int

    product_id: int

    quantity: int

    reserved_quantity: int

    model_config = ConfigDict(from_attributes=True)