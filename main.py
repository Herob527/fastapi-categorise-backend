from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database_handle.database import engine
from database_handle.models import audios, bindings, categories, texts
from routes import (
    audios as r_audios,
)
from routes import (
    bindings as r_bindings,
)
from routes import (
    categories as r_categories,
)
from routes import (
    finalize as r_finalise,
)
from routes import (
    texts as r_texts,
)

from routes import (
    dashboard as r_dashboard,
)

texts.Base.metadata.create_all(engine)
audios.Base.metadata.create_all(engine)
categories.Base.metadata.create_all(engine)
bindings.Base.metadata.create_all(engine)

origins = "https?://localhost:.+"

app = FastAPI()

app.include_router(r_categories.router)
app.include_router(r_texts.router)
app.include_router(r_audios.router)
app.include_router(r_bindings.router)
app.include_router(r_finalise.router)
app.include_router(r_dashboard.router)


@app.get("/")
async def root():
    return "Hello"


print("Listening")
