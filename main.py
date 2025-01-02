from fastapi import FastAPI, Request, Query, HTTPException
from fastapi.responses import StreamingResponse, HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import logging
import os
from datetime import datetime, timezone
from dotenv import load_dotenv
import httpx
import json
from query_openai import QueryOpenAi

# Initialize FastAPI app
app = FastAPI()

# Mount static directory for CSS, JS, and images
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize Jinja2 templates
templates = Jinja2Templates(directory="templates")

# Load environment variables
load_dotenv()

@app.get("/", response_class=HTMLResponse)
async def login(request: Request):
    '''
        default application endpoint 
        directly renders the index.html template
    '''
    return templates.TemplateResponse("index.html", {"request": request, "username": "Guest"})

@app.get("/home", response_class=HTMLResponse)
async def auth_redirect(request: Request):
    '''
        home endpoint 
        directly renders the index.html template
    '''
    return templates.TemplateResponse("index.html", {"request": request, "username": "Guest"})

# Streaming endpoint
@app.get("/stream")
async def stream(
    request: Request,
    search_query: str = Query(...),
    topNDocuments: int = Query(5),
    sessionID: str = Query(...),
):
    print(
        f"search_query is {search_query}, topNDocuments is {topNDocuments}, sessionID is {sessionID}"
    )
    # Write sessionID to a file
    with open("sessionID.txt", "w") as f:
        f.write(sessionID)

    query_rag = QueryOpenAi()
    

    def event_generator():
        response_chunks = []
        for content in query_rag.query_openai(search_query):
            json_content = json.dumps({'type': 'response', 'data': content})
            # Make the response SSE compliant
            sse_content = f"data: {json_content}\n\n"
            print(sse_content)  # Debugging: Print the content to the console
            yield sse_content

    return StreamingResponse(event_generator(), media_type="text/event-stream")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)