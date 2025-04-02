from fastapi import APIRouter
from service.linkedin_service import get_company_info, get_posts, info_companies,post_companies
from typing import Dict
router = APIRouter()


#endpoint de una sola organizacion para obtener el nombre
@router.get("/linkedin/nombre/{vanity_name}")
async def fetch_company_info(vanity_name: str):
    return await get_company_info(vanity_name)
#endpoint de una sola organizacion para obtener los 30 ultimos posts
@router.get("/linkedin/posts/{vanity_name}")
async def fetch_company_post(vanity_name: str):
    return await get_posts(vanity_name)
#endpoint de una sola organizacion para obtener tanto post como basic
@router.get("/linkedin/fullinfo/{vanity_name}")
async def fetch_company_fullInfo(vanity_name: str):
    company_info = await get_company_info(vanity_name)
    company_post = await get_posts(vanity_name)

    full_info = (company_info, company_post)
    return full_info
#endpoint par aobtener el basic de una lista de compañias
@router.get("/linkedin/api/v1/getBasic")
async def fetch_multiple_companies(data: Dict):
    return await info_companies(data)
#endpoint par aobtener los posts de una lista de compañias
@router.get("/linkedin/api/v1/getPost")
async def fetch_multiple_post(data: Dict):
    return await post_companies(data)