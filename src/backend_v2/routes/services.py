# -*- coding: utf-8 -*-

from fastapi import APIRouter


router = APIRouter()


@router.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}
