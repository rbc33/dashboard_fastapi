from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from fastapi.staticfiles import StaticFiles
import os
from pathlib import Path
from dotenv import load_dotenv
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.io as pio

_ = load_dotenv()
data = []
df : pd.DataFrame
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
    global df
    df = pd.DataFrame(data, columns=["Path", "Filesize", "Extension"])
    
def get_size()->str:
    size = df.Filesize.sum()
    if size < 1024:
        size = f"{size} bytes"
    elif size < 1024**2:
        size = f"{size//1024} kb"
    elif size < 1024**3:
        size = f"{size//(1024**2)} mb"
    else:
        size = f"{size//(1024**3)} gb"
    return size



@app.get("/")
async def root():
    return {"message": "Hello World"}
@app.get("/pie_chart")
async def get_pie(request: Request, amount: int = 10):
    top_ten = set(
        df
        .groupby('Extension')
        .Filesize.sum()
        .sort_values(ascending=False)
        .head(amount)
        .index
    )
    df.loc[:,'Top_Ten'] = df.eval('Extension in @top_ten')
    plot_df = ( 
            df.assign(Extension = lambda x:np.where(x.Top_Ten, x.Extension, "Other"))
            .groupby("Extension")
            .Filesize.sum()
            .reset_index()
        )
    fig = px.pie(plot_df, names="Extension", values="Filesize")
    context = { "pie_chart": pio.to_html(fig, full_html=False) }
    return template.TemplateResponse(request, 'pie_chart.html', context)

@app.get("/bad_actors")
def get_bad_actors(request: Request, amount: int = 10):
    print("badc_func")
    plot_df = df.sort_values("Filesize", ascending=False).head(amount)
    fig = px.bar(
        plot_df,
        "Path",
        "Filesize"
    )
    fig.update_xaxes(tickangle=45)
    context = { "bad_actors_chart": pio.to_html(fig, full_html=False) }
    return template.TemplateResponse(request, 'bad_actors.html', context)
    
@app.get("/read_stats")
async def read_stats(request: Request, directory: str = DEFAULT_DIR):
    get_stats(directory)
    dirs = [str(dir) for dir in Path(directory).iterdir() if dir.is_dir()]
    context = {
        "subdirectories": dirs,
        "current_dir": directory,
        "parent_dir": str(Path(directory).parent),
        "dir_size":  get_size()
    }
    return template.TemplateResponse(request, 'base.html', context)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
