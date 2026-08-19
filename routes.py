from fastapi import APIRouter, HTTPException, Body

router = APIRouter()

@router.get("/")
def read_root():
    return {"Hello": "World"}