import json
import requests
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.propagate = False

class GraniteChat:
    def __init__(self, model="granite3-dense"):
        self.model = model
        self.messages = []

    def chat(self, user_input):
        logging.info(f"User input: {user_input}")
        self.messages.append({"role": "user", "content": user_input})
        payload = {"model": self.model, "messages": self.messages, "stream": True}
        
        try:
            r = requests.post(
                "http://0.0.0.0:11434/api/chat",
                json=payload,
                stream=True
            )
            r.raise_for_status()
        except requests.exceptions.RequestException as e:
            logging.error(f"HTTP request failed: {e}")
            return

        output = ""
        for line in r.iter_lines():
            if line.strip():  # Ensure the line isn't empty
                body = json.loads(line)
                if body.get("done") is False:
                    content = body.get("message", {}).get("content", "")
                    output += content
                    print(content, end="", flush=True)  # Print each chunk as it arrives
                    yield content

                if body.get("done", False):
                    self.messages.append({"role": "assistant", "content": output})
                    print()  # Print a newline after completion
                    return output  # Return the full response

    def run(self):
        while True:
            user_input = input("Enter a prompt: ")
            if not user_input:
                exit()
            complete_response = self.chat(user_input)
            logging.info(f"\nComplete response: {complete_response}\n")

if __name__ == "__main__":
    chat_instance = GraniteChat()
    chat_instance.run()
