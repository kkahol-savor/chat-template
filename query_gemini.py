from dotenv import load_dotenv
import google.generativeai as genai
import os
from collections import deque

class QueryGemini:
    '''class to handle Gemini queries'''
    session_histories = {}  # Dictionary to store histories by sessionID

    def __init__(self, session_id: str):
        load_dotenv()
        gemini_key = os.getenv("GEMINI_KEY")
        genai.configure(api_key=gemini_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        self.session_id = session_id
        if session_id not in QueryGemini.session_histories:
            QueryGemini.session_histories[session_id] = deque(maxlen=10)  # Initialize history for sessionID

    def query_gemini(self, query: str, context: str = ""):
        """
        Query Gemini with the given query and optional context.
        If context is provided, it is included in the prompt for better responses.
        The history of the session is also included in the prompt.
        """
        try:
            # Retrieve the session history
            history = QueryGemini.session_histories[self.session_id]

            # Combine context, history, and query into a structured prompt
            history_text = "\n".join(history) if history else "No history available."
            context_text = context if context else "No context available."
            print(f"History: {history_text}")
            print(f"Context: {context_text}")
            prompt = (
                f"This is the history:\n{history_text}\n\n"
                f"This is the context:\n{context_text}\n\n"
                f"This is the query:\n{query}\n\n"
                "Answer appropriately with citations to the context. Insert citations in the format [1], [2], etc.\n"
                "If no context is available, answer based on the history.\n"
                "If no history is available, answer based on your knowledge.\n"
                "if history is available, answer based on the history and interpret the query based on history.\n"
                "If the question is not clear, ask for clarification.\n"
                "If the question is not relevant, say 'I cannot help with that'."
            )

            # Call the Gemini API and stream the response
            response = self.model.generate_content(prompt, stream=True)
            answer = ""
            for chunk in response:
                answer += chunk.text
                yield chunk.text

            # Update the session history with the latest Q&A
            history.append(f"Q: {query}")
            history.append(f"A: {answer.strip()}")
        except Exception as e:
            raise RuntimeError(f"Error querying Gemini: {e}")

    def get_history(self):
        '''Retrieve the history of Q&A for the current session'''
        return list(QueryGemini.session_histories[self.session_id])

if __name__ == "__main__":
    session_id = input("Enter session ID: ")
    query = QueryGemini(session_id)
    try:
        while True:
            prompt = input("Enter your question (or press CTRL+C to exit): ")
            print("Answer:", end=' ')
            for chunk in query.query_gemini(prompt):
                print(chunk, end='')
    except KeyboardInterrupt:
        print("\nExiting. Goodbye!")
