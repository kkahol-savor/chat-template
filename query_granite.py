import json
import requests

class GraniteChat:
    def __init__(self, model="granite3.1-dense:8b"):
        self.model = model
        self.messages = []

    def chat(self, user_input):
        self.messages.append({"role": "user", "content": user_input})
        payload = {"model": self.model, "messages": self.messages, "stream": True}
        print(f"Sending payload: {json.dumps(payload, indent=2)}")  # Log the payload
        r = requests.post(
            "http://0.0.0.0:11434/api/chat",
            json=payload,
            stream=True
        )
        r.raise_for_status()
        output = ""

        for line in r.iter_lines():
            body = json.loads(line)
            print(f"body: {body}")
            if "error" in body:
                raise Exception(body["error"])
            if body.get("done") is False:
                message = body.get("message", "")
                content = message.get("content", "")
                yield content
                output += content
                # the response streams one token at a time, print that as we receive it
                print(content, end="", flush=True)

            if body.get("done", False):
                message["content"] = output
                self.messages.append(message)
                return message

    def run(self):
        while True:
            user_input = input("Enter a prompt: ")
            if not user_input:
                exit()
            print()
            message = self.chat(user_input)
            print("\n\n")

if __name__ == "__main__":
    chat_instance = GraniteChat()
    chat_instance.run()