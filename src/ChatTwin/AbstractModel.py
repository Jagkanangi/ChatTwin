from abc import ABC, abstractmethod
from typing import Any
from dotenv import load_dotenv
from openai.types.chat import ChatCompletionMessage
from openai import OpenAI
client = OpenAI()

class AbstractChatClient(ABC):
    def __init__(self, model_name, model_key, model_role_type = "You are an assistant"):
        load_dotenv()
        self.model_name = model_name
        self.model_key = model_key
        self.messages = []
        self.model_role_type = model_role_type
        self.SYSTEM_ROLE = "system"
        self.USER_ROLE = "user"
        self.ASSISTANT_ROLE = "assistant"
        self.TOOL_ROLE = "tool"
        self.add_message(self.SYSTEM_ROLE, model_role_type)

    @abstractmethod
    def initialize_client(self):        
        pass 
    
    @abstractmethod
    def chat(self, prompt, temperature = 0, max_tokens = 500, model = None) -> str:
        pass

    # convenience method to create role type tool and add it to the message history
    def add_tool_message(self, assistant_msg : ChatCompletionMessage, content : str):
        self.messages.append(assistant_msg.model_dump())
        if(assistant_msg.tool_calls is not None and len(assistant_msg.tool_calls) > 0):
            self.messages.append(
                {"role": self.TOOL_ROLE,
                "tool_call_id": assistant_msg.tool_calls[0].id,
                "content": content
                }
            )
    # convenience method to add text to message history
    def add_message(self, role, content):
        # if(role == self.USER_ROLE):
        #     self.filterMessageForHarmfulness(content)
        self.messages.append({"role": role, "content": content})

    def clear_messages(self):
        self.messages = []

    # convenience method to get all messages
    def get_messages(self):
        return self.messages
    
    # convenience method to get the last message of a specific role
    def get_last_message(self, role = None) -> str:
        if(role is None):
            role = self.SYSTEM_ROLE
        last_message = ""
        if self.messages:
            for message in reversed(self.messages):
                if(isinstance(message, dict)):
                    if message['role'] == role:
                        last_message = message["content"]
                        break
        return last_message
    # print all messages
    def print_messages(self):
        for message in self.messages:
            print(f"{message['role']}: {message['content']}")

    # print the last message that was recieved from the LLM 
    def print_last_message(self, role = "system"):
        last_message = self.get_last_message(role)
        if last_message:
            print(f"{role}: {last_message}")
        else:
            print(f"No {role} messages found.")
    
    def filterMessageForHarmfulness(self, message : str):
        response = client.moderations.create(
            model="omni-moderation-latest",
            input=message,
        )
        flagged : bool = False

        output = response.results
        for moderation_result in output:
            if(moderation_result.flagged):
                flagged = True
            # You can see exactly why it was flagged:
            for category, is_flagged in moderation_result.categories:
                if is_flagged:
                    print(f"- Flagged for: {category}")
                    if(flagged == False):
                        flagged = True
        if(flagged):
            raise ValueError("Harmful content detected in message.")
    



    