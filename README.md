# LINKEDIN EXTRACTION API

## Descripción
Este código sirve para extraer información de organizaciones de LinkedIn que sean públicas.

## Tecnologías
- **Python** (versión 3.13.2)
- **FastAPI**

## Instalación

Para instalar en tu ambiente local, sigue estos pasos:

1. Clona este repositorio:
   ```sh
   git clone <URL_DEL_REPOSITORIO>
   ```
   O también puedes descargarlo en formato ZIP y ejecutarlo en el IDE que prefieras.

2. Crea un ambiente virtual dentro de la carpeta raíz del proyecto:
   ```sh
   python -m venv venv
   ```
   Luego, actívalo:
   - En Windows:
     ```sh
     venv\Scripts\activate
     ```
   - En macOS/Linux:
     ```sh
     source venv/bin/activate
     ```

3. Instala las dependencias del proyecto:
   ```sh
   pip install -r requirements.txt
   ```
   Estas instalaciones no son globales, solo se aplican a este proyecto.

4. Configuración del token:
   - Ve a la carpeta `configuration` dentro del proyecto.
   - Abre el archivo `settings.py` y escribe el token que te proporciona LinkedIn para poder usar sus APIs.
   - Este token tendrá un período válido de dos meses a partir de la fecha de creación.
   - Más información en la documentación oficial de LinkedIn: [LinkedIn API](https://learn.microsoft.com/es-es/linkedin/).

## Ejecución

Para ejecutar el proyecto:
1. Asegúrate de activar el ambiente virtual si aún no lo has hecho.
2. Ejecuta el siguiente comando en la terminal:
   ```sh
   uvicorn main:app --reload
   ```
   Esto ejecutará el servidor en la dirección por defecto: [http://127.0.0.1:8000/](http://127.0.0.1:8000/).

## Endpoints disponibles

| Endpoint | Descripción | Ejemplo |
|----------|------------|---------|
| `/linkedin/nombre/{vanity_name}` | Obtiene información de una organización. | `127.0.0.1:8000/linkedin/nombre/gurpo-kfc-ecuador` |
| `/linkedin/posts/{vanity_name}` | Obtiene los últimos 30 posts. Solo las estadísticas de posts tipo `ugc post` están disponibles; para `shares` se necesita autorización o ser administrador. | `127.0.0.1:8000/linkedin/posts/gurpo-kfc-ecuador` |
| `/linkedin/fullinfo/{vanity_name}` | Obtiene tanto posts como información general en una sola consulta. | `127.0.0.1:8000/linkedin/fullinfo/gurpo-kfc-ecuador` |
| `/linkedin/api/v1/getBasic` | Obtiene información básica de una lista de organizaciones. | - |
| `/linkedin/api/v1/getPost` | Obtiene información de los últimos 30 posts de una lista de organizaciones. | - |

**Nota:** Todos estos son métodos `GET`.

Para los dos últimos endpoints (`/linkedin/api/v1/getBasic` y `/linkedin/api/v1/getPost`), se debe enviar el siguiente cuerpo en la solicitud:

```json
{
    "pages": [
        "https://www.linkedin.com/company/gurpo-kfc-ecuador/",
        "https://www.linkedin.com/company/paginaejemplo/"
        "aqui sigue agregando paginas"
    ],
    "red": "Linkedin"
}
```

**Importante:** Los resultados de cada endpoint se devuelven en **texto plano**, no en JSON, por petición especial.

## Estructura del Proyecto

La estructura del proyecto es la siguiente:
```
Linkedin-api-pj/
│── app/
│   ├── configuration/
│   │   ├── settings.py
│   ├── rest/
│   │   ├── linkedin_routes.py
│   ├── service/
│   │   ├── linkedin_service.py
│   ├── utils/
│   │   ├── linkedin_utils.py
│   ├── main.py
│── venv/ (entorno virtual)
│── requirements.txt
│── README.md
```

