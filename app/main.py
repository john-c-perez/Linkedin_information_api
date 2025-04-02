from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from rest.linkedin_routes import router
app = FastAPI()
@app.exception_handler(Exception)
async def global_excption_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"message": "error inesperado ocurrido", "detail": str(exc)},
    )

app.include_router(router)
