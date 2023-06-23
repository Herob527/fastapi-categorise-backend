from database_handle.database import engine
from fastapi import FastAPI
from database_handle.models import texts, audios, categories, bindings
from routes import categories as r_categories, texts as r_texts, audios as r_audios

texts.Base.metadata.create_all(engine)
audios.Base.metadata.create_all(engine)
categories.Base.metadata.create_all(engine)
bindings.Base.metadata.create_all(engine)

app = FastAPI()

app.include_router(r_categories.router)
app.include_router(r_texts.router)
app.include_router(r_audios.router)


@app.get("/")
def root():
    return {"Hejo": "hejo"}
