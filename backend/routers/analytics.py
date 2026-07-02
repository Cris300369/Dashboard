from fastapi import APIRouter, Depends, Query
from typing import Optional
import sqlite3
from core.database import get_db
from services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/laptops")
def get_laptops(
    os_desc: Optional[str] = None, fab_desc: Optional[str] = None, cat_desc: Optional[str] = None,
    pan_desc: Optional[str] = None, gpu_fab: Optional[str] = None, cpu_fab: Optional[str] = None,
    ram_desc: Optional[str] = None, alm_desc: Optional[str] = None,
    db: sqlite3.Connection = Depends(get_db)
):
    service = AnalyticsService(db)
    return service.get_laptops(
        os_desc=os_desc, fab_desc=fab_desc, cat_desc=cat_desc, pan_desc=pan_desc,
        gpu_fab=gpu_fab, cpu_fab=cpu_fab, ram_desc=ram_desc, alm_desc=alm_desc
    )

@router.get("/queries/{query_id}")
def get_canned_queries(query_id: str, db: sqlite3.Connection = Depends(get_db)):
    service = AnalyticsService(db)
    return service.get_canned_query(query_id)
