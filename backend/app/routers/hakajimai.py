from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.hakajimai import HakajimaiPlan, DEFAULT_CHECKLIST, DEFAULT_COST_ITEMS, DEFAULT_GRAVE_INFO
from ..schemas.hakajimai import HakajimaiPlanUpdate, HakajimaiPlanResponse
from ..models.user import User
from .auth import get_current_user

router = APIRouter(tags=["hakajimai"])


def _get_or_create(db: Session, user_id: int) -> HakajimaiPlan:
    plan = db.query(HakajimaiPlan).filter(HakajimaiPlan.user_id == user_id).first()
    if not plan:
        plan = HakajimaiPlan(
            user_id=user_id,
            kuyou_method="",
            kuyou_detail="",
            message_to_family="",
            checklist_items=list(DEFAULT_CHECKLIST),
            cost_items=list(DEFAULT_COST_ITEMS),
            sect="",
            grave_info=dict(DEFAULT_GRAVE_INFO),
        )
        db.add(plan)
        db.commit()
        db.refresh(plan)
    return plan


@router.get("/hakajimai", response_model=HakajimaiPlanResponse)
def get_plan(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return _get_or_create(db, current_user.id)


@router.put("/hakajimai", response_model=HakajimaiPlanResponse)
def update_plan(
    body: HakajimaiPlanUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    plan = _get_or_create(db, current_user.id)
    if body.kuyou_method is not None:
        plan.kuyou_method = body.kuyou_method
    if body.kuyou_detail is not None:
        plan.kuyou_detail = body.kuyou_detail
    if body.message_to_family is not None:
        plan.message_to_family = body.message_to_family
    if body.checklist_items is not None:
        plan.checklist_items = body.checklist_items
    if body.cost_items is not None:
        plan.cost_items = body.cost_items
    if body.sect is not None:
        plan.sect = body.sect
    if body.grave_info is not None:
        plan.grave_info = body.grave_info
    db.commit()
    db.refresh(plan)
    return plan
