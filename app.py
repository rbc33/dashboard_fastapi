from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from fastapi.staticfiles import StaticFiles
import os
from pathlib import Path
from dotenv import load_dotenv

_ = load_dotenv()
daya = []
DEFAULT_DIR = os.getenv("DEFAULT_DIR") 
template = Jinja2Templates("templates")

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")


def get_stats(directory: str) -> None:
    global data
    data = []
    for directory, dirs, files in os.walk(directory):
        for file in files:
            file = os.path.join(directory, file)
            if not os.path.islink(file):
                data.append([file, os.path.getsize(file), Path(file).suffix[1:]])


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/read_stats")
async def read_stats(request: Request, directory: str = DEFAULT_DIR):
    get_stats(directory)
    dirs = [str(dir) for dir in Path(directory).iterdir() if dir.is_dir()]
    context = {
        "subdirectories": dirs,
        "current_dir": directory,
        "parent_dir": str(Path(directory).parent)   
    }
    return template.TemplateResponse(request, 'base.html', context)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
