from dotenv import load_dotenv
import google.generativeai as genai
import os
from collections import deque

class QueryGemini:
    '''class to handle Gemini queries'''
    def __init__(self):
        load_dotenv()
        gemini_key = os.getenv("GEMINI_KEY")
        genai.configure(api_key=gemini_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        self.history = deque(maxlen=10)  # Store up to the last 10 Q&A pairs

    def query_gemini(self, prompt: str):
        '''Function to query Google's Gemini API'''
        # Include history in the prompt with explicit instructions
        history_context = "\n".join(
            [f"Q: {item['question']}\nA: {item['answer']}" for item in self.history]
        )
        full_prompt = (
            f"The following is a conversation history. Use it to answer the next question:\n"
            f"{history_context}\nQ: {prompt}" if history_context else prompt
        )

        response = self.model.generate_content(full_prompt, stream=True)
        answer = ""
        for chunk in response:
            answer += chunk.text
            yield chunk.text
        self.history.append({"question": prompt, "answer": answer})  # Save Q&A to history

    def get_history(self):
        '''Retrieve the history of Q&A'''
        return list(self.history)

if __name__ == "__main__":
    query = QueryGemini()
    try:
        while True:
            prompt = input("Enter your question (or press CTRL+C to exit): ")
            print("Answer:", end=' ')
            for chunk in query.query_gemini(prompt):
                print(chunk, end='')
            print("\nHistory:", query.get_history())
    except KeyboardInterrupt:
        print("\nExiting. Goodbye!")
