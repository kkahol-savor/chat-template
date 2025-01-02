
# Basic Chat Application with OpenAI Integration

This is a simple chat application that integrates a frontend and backend to provide chat functionality using OpenAI's API. The application allows users to interact with an AI agent and receive responses in real time.

## Project Structure

- **`main.py`**: The entry point for the backend application, implemented using FastAPI.
- **`query_openai.py`**: Contains helper functions to interact with OpenAI's API.
- **`requirements.txt`**: Lists all the dependencies required for the project.
- **`static/`**: Contains static files (CSS, JavaScript, images).
  - **`styles.css`**: Defines the styling for the application.
  - **`chat.js`**: Handles the frontend logic and manages communication with the backend.
  - **`Logo.png`**: The logo displayed in the header.
- **`templates/`**: Contains HTML templates.
  - **`index.html`**: The main HTML page for the chat interface.

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/your-repo/chat-app.git
   cd chat-app
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   - Create a `.env` file in the root directory.
   - Add your OpenAI API key:
     ```env
     OPENAI_API_KEY=your_api_key_here
     ```

4. Run the application:
   ```bash
   uvicorn main:app --reload
   ```

5. Open your browser and navigate to `http://127.0.0.1:8000`.

## Features

- **Real-Time Chat**: Users can send messages and receive responses in real time.
- **Markdown Rendering**: The application supports rendering responses with Markdown for better readability.
- **Session Management**: Unique session IDs are generated for each user to maintain context.
- **Custom Styling**: The interface is styled using CSS for a clean and modern look.

## File Descriptions

### `main.py`
- Starts the FastAPI server.
- Defines API endpoints to handle user requests and communicate with OpenAI.

### `query_openai.py`
- Contains utility functions for querying OpenAI's API and processing responses.

### `requirements.txt`
- Dependencies:
  - `uvicorn`: ASGI server.
  - `fastapi`: Framework for building APIs.
  - `jinja2`: Template engine for rendering HTML.
  - `httpx`: HTTP client for making API requests.
  - `python-dotenv`: For managing environment variables.
  - `openai`: Official OpenAI library.

### Static Files
- **`styles.css`**: Manages the layout and design, including gradients, header styling, and chat box appearance.
- **`chat.js`**: Implements the client-side logic for handling form submissions and streaming server responses.
- **`Logo.png`**: Adds a visual identity to the application.

### Template
- **`index.html`**: Defines the basic structure of the chat interface. It includes placeholders for dynamic content like username and chat messages.

## Usage

1. Start the server by running `uvicorn`.
2. Open the application in your browser.
3. Interact with the chat by typing a query and pressing the "Send" button.

## Future Improvements

- Add user authentication.
- Implement more robust error handling.
- Enhance the UI for mobile responsiveness.
- Support additional languages and features.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

---
