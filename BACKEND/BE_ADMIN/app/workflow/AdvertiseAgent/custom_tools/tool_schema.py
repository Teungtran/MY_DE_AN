from pydantic import BaseModel
from typing import Literal, Optional


class InferredDeviceType(BaseModel):
    type: Optional[Literal["phone", "laptop/pc", "earphone", "mouse", "keyboard"]]