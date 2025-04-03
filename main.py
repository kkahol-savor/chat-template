from fastapi import FastAPI, Request, Query, HTTPException, File, UploadFile
from fastapi.responses import StreamingResponse, HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import logging
import os
from datetime import datetime, timezone
from dotenv import load_dotenv
import json
import faiss  # Import FAISS for index loading
from data_indexer import DataIndexer  # Import DataIndexer for FAISS integration
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
    '''
        Streaming endpoint that integrates FAISS for document retrieval and uses QueryGemini for response generation.
    '''
    try:
        # Check if FAISS is trained and ready
        if hasattr(app, "faiss_index") and app.faiss_index is not None:
            logging.info("FAISS index is available. Retrieving documents...")
            data_indexer = app.faiss_index
            retrieved_docs = data_indexer.search_faiss(search_query, top_k=topNDocuments)
            context = " ".join([json.dumps(doc) for doc in retrieved_docs])  # Combine documents as context
            logging.info(f"Retrieved {len(retrieved_docs)} documents from FAISS.")
        else:
            logging.warning("FAISS index is not available. Proceeding without context.")
            context = ""  # No context if FAISS is not available

        # Pass the query and context to QueryGemini
        query_rag = QueryGemini(session_id=sessionID)  # sessionID is passed here

        def event_generator():
            response_chunks = []
            for content in query_rag.query_gemini(search_query, context=context):  # Pass context to QueryGemini
                json_content = json.dumps({'type': 'response', 'data': content})
                # Make the response SSE compliant
                sse_content = f"data: {json_content}\n\n"
                logging.debug(f"Streaming content: {sse_content}")
                yield sse_content

            # Add citations to the response if FAISS was used
            if context:
                citations = [{"type": "citation", "data": doc} for doc in retrieved_docs]
                for citation in citations:
                    json_content = json.dumps(citation)
                    sse_content = f"data: {json_content}\n\n"
                    yield sse_content

        return StreamingResponse(event_generator(), media_type="text/event-stream")

    except Exception as e:
        logging.error(f"Error in /stream endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.on_event("startup")
async def initialize_faiss_index():
    '''
        Initialize FAISS index on application startup.
    '''
    try:
        faiss_index_file = "faiss_index.bin"
        data_file = "data.json"
        if os.path.exists(faiss_index_file):
            logging.info(f"Loading FAISS index from {faiss_index_file}...")
            data_indexer = DataIndexer(data_file=data_file)  # Initialize with the data file
            data_indexer.index = faiss.read_index(faiss_index_file)  # Load the FAISS index from a file
            app.faiss_index = data_indexer
            logging.info("FAISS index loaded successfully.")
        else:
            logging.warning(f"FAISS index file {faiss_index_file} not found. FAISS will not be available.")
            app.faiss_index = None
    except Exception as e:
        logging.error(f"Error initializing FAISS index: {e}")
        app.faiss_index = None

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