import requests
from configuration.settings import HEADERS
from fastapi import HTTPException
import urllib
base = "https://api.linkedin.com"

#transformar urn a formato aceptado por el api en el caso de Fotos de perfil
def transform_urn_to_url(urn: str) -> str:
    if "digitalmediaAsset" in urn:
        urn = urn.replace("digitalmediaAsset", "image")
        urn1 = f"{base}/rest/images/{urn.replace(':', '%3A')}"
        response = requests.get(urn1, headers=HEADERS)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Error fetching company data")
        data = response.json()
        return data.get("downloadUrl")
    
#transformar una lista de urn y obtener sus url de descarga
def fetch_media_urls(urns_list):
    if not urns_list:
        return {}
    image_urns = [urn for urn in urns_list if urn.startswith("urn:li:image:")]
    video_urns = [urn for urn in urns_list if urn.startswith("urn:li:video:")]
    media_map = {}

    # Obtener imágenes
    if image_urns:
        image_urns_encoded = [urllib.parse.quote(urn, safe='') for urn in image_urns]
        image_urns_param = ",".join(image_urns_encoded)
        image_url = f"{base}/rest/images?ids=List({image_urns_param})"
        image_response = requests.get(image_url, headers=HEADERS)

        if image_response.status_code == 200:
            image_data = image_response.json()
            results = image_data.get("results", {})
    
            # Iteramos sobre las claves y valores del diccionario 'results'
            media_map.update({
            key: {"downloadUrl": item.get("downloadUrl"), "id": item.get("id")}
            for key, item in results.items()  # 'results.items()' devuelve las claves y los valores
        })
    
    # Obtener videos
    if video_urns:
        video_urns_encoded = [urllib.parse.quote(urn, safe='') for urn in video_urns]
        video_urns_param = ",".join(video_urns_encoded)
        video_url = f"{base}/rest/videos?ids=List({video_urns_param})"
        video_response = requests.get(video_url, headers=HEADERS)

        if video_response.status_code == 200:
            video_data = video_response.json()
            resultsv = video_data.get("results", {})
            media_map.update({
            key: {"downloadUrl": item.get("downloadUrl"), "id": item.get("id"),  "thumbnailUrl": item.get("thumbnail")}
            for key, item in resultsv.items()  # 'results.items()' devuelve las claves y los valores
        })
    return media_map

#volver a asignar las urn al json pero en este caso se integran las url
def assign_media_urls(posts, media_map):
    for post in posts:
        if "content" in post:
            # Asignar URLs a imágenes en multiImage
            if "multiImage" in post["content"]:
                for image in post["content"]["multiImage"]["images"]:
                    if "id" in image and image["id"] in media_map:
                        image["url"] = media_map[image["id"]].get("downloadUrl")
                # 🔹 Mover las imágenes a 'content["images"]'
                post["content"]["images"] = post["content"]["multiImage"]["images"]

                # 🔹 Eliminar la clave 'multiImage'
                del post["content"]["multiImage"]

            # Asignar URLs a videos o imágenes en "media"
            elif "media" in post["content"]:
                media_id = post["content"]["media"].get("id")
                if media_id in media_map:
                    media_info = media_map[media_id]
                    post["content"]["media"]["url"] = media_info.get("downloadUrl")
                    post["content"]["media"]["thumbnailUrl"] = media_info.get("thumbnailUrl")  # Para videos


#verificar si es un ugcpost
def is_ugc_post(post_id: str) -> bool:
    return post_id.startswith("urn:li:ugcPost:")
