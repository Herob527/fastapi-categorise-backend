from fastapi.responses import RedirectResponse
from database_handle.database import engine
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database_handle.models import texts, audios, categories, bindings
from routes import (
    categories as r_categories,
    texts as r_texts,
    audios as r_audios,
    bindings as r_bindings,
)

texts.Base.metadata.create_all(engine)
audios.Base.metadata.create_all(engine)
categories.Base.metadata.create_all(engine)
bindings.Base.metadata.create_all(engine)
origins = "https?://localhost:.+"

app = FastAPI()
# Dependency
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(r_categories.router)
app.include_router(r_texts.router)
app.include_router(r_audios.router)
app.include_router(r_bindings.router)


@app.get("/")
def root():
    return RedirectResponse("http://localhost:8000/docs")
