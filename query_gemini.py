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

    def query_gemini(self, prompt: str):
        '''Function to query Google's Gemini API'''
        # Get the history for the current session
        history = QueryGemini.session_histories[self.session_id]
        history_context = "\n".join(
            [f"Q: {item['question']}\nA: {item['answer']}" for item in history]
        )
        last_answer = history[-1]['answer'] if history else ""
        full_prompt = (
            f"The following is a conversation history. Use it to answer the next question. "
            f"Continue the conversation based on the context provided:\n"
            f"{history_context}\nLast Answer: {last_answer}\nQ: {prompt}" if history_context else prompt
        )

        response = self.model.generate_content(full_prompt, stream=True)
        answer = ""
        for chunk in response:
            answer += chunk.text
            yield chunk.text
        history.append({"question": prompt, "answer": answer.strip()})  # Save Q&A to session-specific history

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
            #print("\nHistory:", query.get_history())
    except KeyboardInterrupt:
        print("\nExiting. Goodbye!")
