from pydantic import BaseModel as PydanticBaseModel, Field
import uuid


class ItemRequestBase(PydanticBaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)


class ItemResponseBase(ItemRequestBase):
    id: uuid.UUID
    owner_id: uuid.UUID


# Properties to receive on item creation
class ItemCreateRequest(ItemRequestBase):
    pass


# Properties to receive on item update
class ItemUpdateRequest(ItemRequestBase):
    pass


# Properties to return via API, id is always required
class ItemResponse(ItemResponseBase):
    pass


class ItemsResponse(PydanticBaseModel):
    data: list[ItemResponse]
    count: int
