from fastapi import APIRouter, Form, Request, HTTPException
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from .gemini_flash import generate_outline
from .gemini_pro import generate_story
from .image_generator import generate_image
from .layout_builder import build_comic_layout
from .exporters import save_pdf

router=APIRouter(); templates=Jinja2Templates(directory="templates")

class PromptRequest(BaseModel):
    story_prompt:str
    character_name:str="Alex"
    setting:str="forest"
    tone:str="funny"
    art_style:str="comic book"

def _run(story_prompt,character_name,setting,tone,art_style):
    prompt=f"Story idea: {story_prompt}\nMain character: {character_name}\nSetting: {setting}\nTone: {tone}\nArt style: {art_style}"
    outline=generate_outline(prompt)
    story=generate_story(outline,character_name,setting,tone,art_style)
    images=[]
    for p in outline:
        visual=f"{p['image_prompt']}. Character: {character_name}. Setting: {setting}. Tone: {tone}. Art style: {art_style}. Keep character appearance consistent."
        images.append(generate_image(visual,f"panel_{p['panel']}.png"))
    layout=build_comic_layout(images,story,outline)
    return layout,save_pdf(layout)

@router.get("/")
async def home(request:Request):
    return templates.TemplateResponse("index.html",{"request":request})

@router.post("/generate")
async def generate(request:Request,story_prompt:str=Form(...),character_name:str=Form(...),
                   setting:str=Form(...),tone:str=Form(...),art_style:str=Form(...)):
    try:
        layout,pdf=_run(story_prompt,character_name,setting,tone,art_style)
        return templates.TemplateResponse("comic_preview.html",{"request":request,"layout":layout,
            "pdf_url":"/"+pdf.replace("\\","/").split("static/",1)[-1]})
    except Exception as e:
        raise HTTPException(500,str(e))

@router.post("/generate-comic/json")
async def generate_json(p:PromptRequest):
    layout,pdf=_run(p.story_prompt,p.character_name,p.setting,p.tone,p.art_style)
    return {"layout":layout,"pdf_path":"/"+pdf.replace("\\","/").split("static/",1)[-1]}

@router.get("/export-success")
async def export_success(request:Request,pdf_path:str):
    return templates.TemplateResponse("export_success.html",{"request":request,"pdf_path":pdf_path})

@router.get("/test-image")
async def test_image(request:Request,prompt:str="a brave fox in an enchanted forest"):
    path=generate_image(prompt,"test_panel.png")
    return templates.TemplateResponse("test_image.html",{"request":request,
        "image_url":"/static/panels/test_panel.png","prompt":prompt})
