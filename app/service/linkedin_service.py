import urllib.parse
from fastapi import HTTPException
from configuration.settings import HEADERS
from utils.linkedin_utils import transform_urn_to_url, is_ugc_post, fetch_media_urls, assign_media_urls
from typing import Dict, Optional
import re
import httpx
import asyncio

base = "https://api.linkedin.com"

#obtener informacion basic de una unica compañia
async def get_company_info(vanity_name: str):
    url = f"{base}/v2/organizations?q=vanityName&vanityName={vanity_name}"
    async with httpx.AsyncClient(timeout=50.0) as client:
        response = await client.get(url, headers=HEADERS)
        
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Error fetching company data")
    
    data = response.json().get("elements", [{}])[0]
    if not data:
        return {"vanityName": vanity_name, "error": "Empresa no encontrada"}

    org_id_n = f"urn:li:organization:{data['id']}"
    org_id = urllib.parse.quote(org_id_n)
    logo_url = transform_urn_to_url(data.get("logoV2", {}).get("original", ""))

    # Obtener seguidores y estadisticas (consulta en paralelo)
    followers_url = f"{base}/rest/networkSizes/{org_id}?edgeType=COMPANY_FOLLOWED_BY_MEMBER"
    stats_url = f"{base}/rest/organizationalEntityShareStatistics?q=organizationalEntity&organizationalEntity={org_id}"

    async with httpx.AsyncClient(timeout=50.0) as client:
        followers_response, stats_response = await asyncio.gather(
            client.get(followers_url, headers=HEADERS),
            client.get(stats_url, headers=HEADERS)
        )

    followers_count = followers_response.json().get("firstDegreeSize", 0)
    stats_data = stats_response.json().get("elements", [{}])[0].get("totalShareStatistics", {})
    #retorna linealmente sin un modelo JSON
    return (
        f"vanityname: {data['vanityName']}, "
        f"localizedname: {data['localizedName']}, "
        f"language: {data["name"]["preferredLocale"]["language"]},"
        f"geographicarea: {data.get("locations", [{}])[0].get("address", {}).get("geographicArea")},"
        f"country: {data.get("locations", [{}])[0].get("address", {}).get("country")},"
        f"city: {data.get("locations", [{}])[0].get("address", {}).get("city")},"
        f"postalcode: {data.get("locations", [{}])[0].get("address", {}).get("postalCode")},"
        f"followers: {followers_count},"
        f"logourl: {logo_url},"
        f"statistics: (uniqueImpressionsCount: {stats_data.get("uniqueImpressionsCount", 0)}, shareCount: {stats_data.get("shareCount", 0)}, engagement: {stats_data.get("engagement", 0)}, clickCount: {stats_data.get("clickCount", 0)}, likeCount: {stats_data.get("likeCount", 0)}, impressionCount: {stats_data.get("impressionCount", 0)}, commentCount: {stats_data.get("commentCount", 0)},)"
    )

#Obtener post de una unica organizacion
async def get_posts(vanity_name: str):
    url = f"{base}/v2/organizations?q=vanityName&vanityName={vanity_name}"

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=HEADERS)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Error fetching company data")
        org_id = response.json().get("elements", [{}])[0].get("id", None)
        org_urn =f"urn:li:organization:{org_id}"
        org_urn = urllib.parse.quote(org_urn)

        #Obtener posts del api
        post_url= f"{base}/rest/posts?author={org_urn}&q=author&count=30&sortBy=LAST_MODIFIED"
        post_response = await client.get(post_url, headers=HEADERS)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Error fetching company data")
        posts_data = post_response.json().get("elements", [])

        ugc_post = [post["id"] for post in posts_data if is_ugc_post(post["id"])]
        #envio a obtener estadisticas de cada post UGC en una lista
        statistics = await get_statistics(ugc_post, org_urn)

        # Extraer todas las URNs de imágenes y videos en una lista
        urns_list = []
        for post in posts_data:
            if "content" in post:
                if "multiImage" in post["content"]:
                    urns_list.extend(image["id"] for image in post["content"]["multiImage"]["images"])
                elif "media" in post["content"]:
                    urns_list.append(post["content"]["media"]["id"])
        
        # Obtener URLs en una sola llamada
        media_map = fetch_media_urls(urns_list)
        # Asignar URLs a los posts
        assign_media_urls(posts_data, media_map)

        #organizar nuevamete para presentar
        filtered_posts = []
        for post in posts_data:
            post_id = post["id"]
            post["statistics"] = statistics.get(post_id, None)
            
            # Extraer los valores necesarios
            post_info = {
                "id": post.get("id", "N/A"),
                "Comentario": post.get("commentary", "N/A"),
                "Impresiones Únicas": post["statistics"].get("uniqueImpressionsCount", 0) if post["statistics"] else 0,
                "Total Compartidos": post["statistics"].get("shareCount", 0) if post["statistics"] else 0,
                "Engagement": post["statistics"].get("engagement", 0) if post["statistics"] else 0,
                "clickcount": post["statistics"].get("clickCount", 0) if post["statistics"] else 0,
                #likecount muestra la suma tanto likes como reacciones a un post
                "likecount": post["statistics"].get("likeCount", 0) if post["statistics"] else 0,
                "impressioncount": post["statistics"].get("impressionCount", 0) if post["statistics"] else 0,
                "Contenido": post.get("content", "N/A"),
            }

            # Convertir a formato lineal
            formatted_post = ", ".join([f"{key}: {value}" for key, value in post_info.items()])
            filtered_posts.append(formatted_post)

    return filtered_posts
    
#obtener estadisticas de una lista de post
async def get_statistics(ugc_post: list, org_urn: str):
    if not ugc_post:
        return {}

    ugc_post_encoded = [urllib.parse.quote(post_id, safe='') for post_id in ugc_post]
    ugc_list = ",".join(ugc_post_encoded)
    
    url = f"{base}/rest/organizationalEntityShareStatistics?q=organizationalEntity&organizationalEntity={org_urn}&ugcPosts=List({ugc_list})"

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=HEADERS)

    if response.status_code != 200:
        return {}

    data = response.json()
    stats = {item["ugcPost"]: item["totalShareStatistics"] for item in data.get("elements", [])}

    return stats

#extraer el vanity name de una url
def extract_vanity_name(url: str) -> Optional[str]:
    match = re.search(r"linkedin\.com/company/([^/]+)/?", url)
    return match.group(1) if match else None

#informacion en batch de varias compañias
async def info_companies(data: Dict):
    pages = data.get("pages", [])
    red = data.get("red", "").lower()

    if red != "linkedin":
        raise HTTPException(status_code=400, detail="Solo se soporta LinkedIn en este endpoint")

    vanity_names = [extract_vanity_name(url) for url in pages if extract_vanity_name(url)]
    
    if not vanity_names:
        return {"error": "No se encontraron vanity names válidos"}

    # Crear tareas para ejecutar en paralelo
    tasks = [get_company_info(vanity_name) for vanity_name in vanity_names]

    # Ejecutar todas las consultas en paralelo
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Manejar errores individuales
    final_results = []
    for vanity_name, result in zip(vanity_names, results):
        if isinstance(result, Exception):
            print(f"Error con {vanity_name}: {result}")
            final_results.append({"vanityName": vanity_name, "error": "Empresa no encontrada o URL incorrecto"})
        else:
            final_results.append(result)

    return final_results


#informacion en batch de post de varias compañias
async def post_companies (data: Dict):
    pages = data.get("pages", [])
    red = data.get("red", "").lower()

    if red != "linkedin":
        raise HTTPException(status_code=400, detail="Solo se soporta LinkedIn en este endpoint.")
    
    results=[]
    async with httpx.AsyncClient() as client:
        tasks = []
        for url in pages:
            vanity_name = extract_vanity_name(url)
            if vanity_name:
                tasks.append(get_posts(vanity_name))
        posts= await asyncio.gather(*tasks, return_exceptions=True)
        for vanity_name, company_posts in zip(pages, posts):
            if isinstance(company_posts, Exception):
                print(f"Error con {vanity_name}: {company_posts}")
                results.append({"vanityName": vanity_name, "error": "Empresa no encontrada o URL incorrecto"})
            else:
                results.append({"vanityName": vanity_name, "posts": company_posts})
    return results