from fastapi import FastAPI, Request, Query, HTTPException, File, UploadFile
from fastapi.responses import StreamingResponse, HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import logging
import os
from datetime import datetime, timezone
from dotenv import load_dotenv
import json
from query_gemini import QueryGemini
from drag_and_drop_ui import upload_and_index  # Import the function

# Initialize FastAPI app
app = FastAPI()

# Mount static directory for CSS, JS, and images
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize Jinja2 templates
templates = Jinja2Templates(directory="templates")

# Load environment variables
load_dotenv()

UPLOAD_DIRECTORY = "./uploads"

# Ensure the upload directory exists
os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)

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

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    '''
        Endpoint to handle file uploads and trigger indexing.
    '''
    try:
        file_path = os.path.join(UPLOAD_DIRECTORY, file.filename)
        with open(file_path, "wb") as f:
            f.write(await file.read())
        
        # Trigger the upload_and_index function
        upload_and_index(file_path)  # Pass the file path to the function

        return JSONResponse(content={"filename": file.filename}, status_code=200)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Streaming endpoint
@app.get("/stream")
async def stream(
    request: Request,
    search_query: str = Query(...),
    topNDocuments: int = Query(5),
    sessionID: str = Query(...),  # sessionID is received as a query parameter
):
    print(
        f"search_query is {search_query}, topNDocuments is {topNDocuments}, sessionID is {sessionID}"
    )
    # Write sessionID to a file (optional, for debugging or logging purposes)
    with open("sessionID.txt", "w") as f:
        f.write(sessionID)

    # Pass sessionID to QueryGemini
    query_rag = QueryGemini(session_id=sessionID)  # sessionID is passed here

    def event_generator():
        response_chunks = []
        for content in query_rag.query_gemini(search_query):  # QueryGemini uses sessionID internally
            json_content = json.dumps({'type': 'response', 'data': content})
            # Make the response SSE compliant
            sse_content = f"data: {json_content}\n\n"
            print(sse_content)  # Debugging: Print the content to the console
            yield sse_content

    return StreamingResponse(event_generator(), media_type="text/event-stream")

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