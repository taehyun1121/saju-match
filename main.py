from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from compatibility import calc_compatibility, get_pillars

app = FastAPI(title="SajuMatch API")
api = APIRouter(prefix="/api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class PersonInfo(BaseModel):
    year: int
    month: int
    day: int
    hour: Optional[int] = None
    gender: Optional[str] = None


class SajuRequest(BaseModel):
    person: PersonInfo


class CompatibilityRequest(BaseModel):
    person1: PersonInfo
    person2: PersonInfo


@api.post("/saju")
def get_saju(req: SajuRequest):
    p = req.person
    gan, ji, yeonji = get_pillars(p.year, p.month, p.day, p.hour)
    return {
        "ilgan": gan,
        "ilji": ji,
        "yeonji": yeonji,
        "birth": {"year": p.year, "month": p.month, "day": p.day, "hour": p.hour},
    }


@api.post("/compatibility")
def compatibility(req: CompatibilityRequest):
    p1, p2 = req.person1, req.person2
    return calc_compatibility(
        p1.year, p1.month, p1.day, p1.hour,
        p2.year, p2.month, p2.day, p2.hour,
    )


@app.get("/")
def root():
    return {"service": "SajuMatch API", "status": "running", "version": "1.0"}


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(api)
