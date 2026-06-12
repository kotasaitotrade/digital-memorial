from pydantic import BaseModel
from typing import List, Any, Optional, Dict


class HakajimaiPlanUpdate(BaseModel):
    kuyou_method: Optional[str] = None
    kuyou_detail: Optional[str] = None
    message_to_family: Optional[str] = None
    checklist_items: Optional[List[Any]] = None
    cost_items: Optional[List[Any]] = None
    sect: Optional[str] = None
    grave_info: Optional[Dict[str, Any]] = None


class HakajimaiPlanResponse(BaseModel):
    id: int
    user_id: int
    kuyou_method: str
    kuyou_detail: str
    message_to_family: str
    checklist_items: List[Any]
    cost_items: List[Any]
    sect: str
    grave_info: Dict[str, Any]

    class Config:
        from_attributes = True
