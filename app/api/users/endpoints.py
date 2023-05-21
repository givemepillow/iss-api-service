from datetime import datetime

from fastapi import APIRouter, UploadFile, Depends
from fastapi.params import Form, File, Query
from app.api.posts import schemas
from app.adapters.gallery import GalleryProtocol
from app.api.schemas import ResponseSchema
from app.service_layer import dto, services
from app.service_layer.unit_of_work import UnitOfWork

router = APIRouter(prefix="/users", tags=["Users"])
