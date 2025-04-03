from fastapi import FastAPI, Request, Query, HTTPException, File, UploadFile
from fastapi.responses import StreamingResponse, HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import logging
import os
from datetime import datetime, timezone
from dotenv import load_dotenv
import httpx
import json
from query_gemini import QueryGemini
import shutil

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

    # Pass sessionID to QueryGemini
    query_rag = QueryGemini(session_id=sessionID)

    def event_generator():
        response_chunks = []
        for content in query_rag.query_gemini(search_query):
            json_content = json.dumps({'type': 'response', 'data': content})
            # Make the response SSE compliant
            sse_content = f"data: {json_content}\n\n"
            print(sse_content)  # Debugging: Print the content to the console
            yield sse_content

    return StreamingResponse(event_generator(), media_type="text/event-stream")

# File upload endpoint
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Endpoint to upload files to a local folder.
    Supports PDF, JSON, CSV, Excel, and Word files up to 500MB.
    """
    # Allowed file extensions
    allowed_extensions = {".pdf", ".json", ".csv", ".xlsx", ".xls", ".docx", ".doc"}
    file_extension = os.path.splitext(file.filename)[1].lower()

    # Check file type
    if file_extension not in allowed_extensions:
        raise HTTPException(status_code=400, detail="Unsupported file type.")

    # Check file size (500MB limit)
    file_size = await file.read()
    if len(file_size) > 500 * 1024 * 1024:  # 500MB in bytes
        raise HTTPException(status_code=400, detail="File size exceeds 500MB limit.")
    await file.seek(0)  # Reset file pointer after reading

    # Save file to the "uploads" directory
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {"filename": file.filename, "message": "File uploaded successfully."}

if __name__ == "__main__":
    session_id = input("Enter session ID: ")  # Prompt user for session ID
    query = QueryGemini(session_id)  # Pass session ID to QueryGemini
    try:
        while True:
            prompt = input("Enter your question (or press CTRL+C to exit): ")
            print("Answer:", end=' ')
            for chunk in query.query_gemini(prompt):  # Query Gemini with the prompt
                print(chunk, end='')
    except KeyboardInterrupt:
        print("\nExiting. Goodbye!")