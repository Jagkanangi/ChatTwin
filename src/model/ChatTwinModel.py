from model.AbstractModel import AbstractChatClient
from externalservices.Pushover import PushOver
from instructor import Instructor, from_litellm
from functools import singledispatchmethod
from litellm import completion
from externalservices.Weather import WeatherService
from typing import List
from decorators.AutoLog import log_vo
import logging
# from pydantic import BaseModel, Field
from vo.Models import GeneralChat, Weather, Contact, Choices
import traceback

logger = logging.getLogger(__name__)
    
class ChatTwin(AbstractChatClient):
    """
    An AI model that can cache responses and interact with a weather API.
    It inherits from AbstractChatClient and uses the litellm library to communicate with different chat models.
    The model uses the `instructor` library to process tool calls from the LLM and dispatch them to the appropriate methods.
    """
    def __init__(self, model_name="gpt-4o-mini-2024-07-18", model_key="", model_role_type="You are an assistant"):
        """
        Initializes the CachingAIModel.

        Args:
            model_name (str, optional): The name of the language model to use. Defaults to "openai/gpt-5-nano-2025-08-07".
            model_key (str, optional): The API key for the language model. Defaults to "".
            model_role_type (str, optional): The role of the model in the chat. Defaults to "You are an assistant".
        """
        super().__init__(model_name, model_key, model_role_type=model_role_type)
        self.client : Instructor
        self.initialize_client()
        self.num_calls = 0


    def initialize_client(self):
        """
        Initializes the instructor client using litellm.
        This allows the model to respond with Pydantic models for tool calls.
        """
        self.client = from_litellm(completion)

    @singledispatchmethod    
    def process_llm_tool_call(self, bm, completion) -> bool:
        """
        Default method for processing LLM tool calls.
        This method is called when no specific tool call is matched.
        """
        self.add_tool_message(completion.choices[0].message, "I cannot find the information for this request. Please try again.")
        return True

    @process_llm_tool_call.register(GeneralChat)
    @log_vo
    def _(self, general_chat, completion) -> bool:
        """
        Processes a general chat message from the LLM.
        """
        content = general_chat.message
        super().add_message(self.ASSISTANT_ROLE, content)
        return False


    @process_llm_tool_call.register(Weather)
    @log_vo
    def _(self, weather, completion) -> bool:
        """
        Processes a weather tool call from the LLM.
        It gets the weather for the specified city and then calls the chat again to get a natural language response.
        """
        # Get the weather report for the specified city. 
        if(weather is None):
            return True # Some unknown reason LLM returns with an empty object ignore it. This is not consistent behaviour. Consider it a Model vagary.  
        
        if(weather.city is None or weather.city.strip() == ""): 
            return True # Some unknown reason LLM returns with an empty object ignore it. This is not consistent behaviour. Consider it a Model vagary.  
        else :
            weather_service = WeatherService()
            weather_report = weather_service.get_weather_object(city_name=weather.city)

            if(weather_report is not None):
                # Add messages to the context to guide the model's final response.
                self.add_tool_message(completion.choices[0].message, f"The weather in {weather_report.city} is {weather_report.temperature} degrees Celsius with {weather_report.humidity}% humidity.")
                # Make another call to the model to get a natural language response based on the weather data.
            else:
                self.add_tool_message(completion.choices[0].message, f"I cannot find the information for {weather.city}")
        return True
        # self.chat(callback=True) 

    @process_llm_tool_call.register(Contact)
    @log_vo
    def _(self, contact, completion) -> bool:
        """
        Processes a contact tool call from the LLM.
        It sends a pushover notification and then calls the chat again to get a natural language response.
        """
        if(contact is None):
            return True # Some unknown reason LLM returns with an empty object ignore it. This is not consistent behaviour. Consider it a Model vagary.  
        # Add messages to the context to guide the model's final response.
        if(contact.name is None or contact.name.strip() == "" or contact.email is None or contact.email.strip() == ""):
            return True # Some unknown reason LLM returns with an empty object ignore it. This is not consistent behaviour. Consider it a Model vagary.  

        else:
            PushOver().send_message(f"The person {contact.name} would like to get in touch with you. His or her email is {contact.email} and their phone number is {contact.phone}")
            self.add_tool_message(completion.choices[0].message, "Let the user know you will connect with them shortly and thank the user for their interest.")
        # # Make another call to the model to get a natural language response based on the weather data.
        # self.chat(callback=True) 
        return True


    def chat(self, prompt=None, temperature=0, max_tokens=500, model=None, print_messages = True) -> str:
        """
        Main chat method. It sends a message to the LLM and processes the response.
        
        Args:
            prompt (str, optional): The user's message. Defaults to None.
            temperature (int, optional): The temperature for the LLM. Defaults to 0.
            max_tokens (int, optional): The maximum number of tokens for the LLM to generate. Defaults to 500.
            model (str, optional): The name of the language model to use. Defaults to None.
            print_messages (bool, optional): Whether to print the messages. Defaults to True.
            callback (bool, optional): Whether this is a callback from a tool call. Defaults to False.

        Returns:
            str: The LLM's response.
        """
        response : List
        # Allow the user to change the model for a specific chat, but maintain the conversation history.
        if(prompt is not None):
            self.add_message(self.USER_ROLE, prompt)
        if model is None:
            model = self.model_name
        try:             
            # If this is not a callback, it's a new user message.
            # The 'response_model' parameter tells the instructor client to parse the response into the 'Choices' Pydantic model.
            response, completion = self.client.chat.create_with_completion(
                model=model,
                messages=self.get_messages(),
                response_model=List[Choices])
            
            call_back_LLM : bool = False
            """
              This code handles the following
              1. If it is a tool call but a general chat
              2. If it is a tool call with multiple entries example What is the weather in Toronto, Phoenix and Melbourne
              3. If it is a multiple tool call (e.g. weather in Toronto and contact me)
              Note that if it is a General Chat we don't have to call the LLM back but any other type we will have to call the LLM back
              to get a natural language response.
            """ 

            for choices in response:
                """
                    The self.process_llm_tool_call is decorated with @singledispatchmethod. This is an elegant way 
                    to let the python interpretor decide at runtime which of the appropriate methods it needs to call.
                    We avoid any if else logic and if we need to add a new tool, we just add a new method. This logic
                    will never have to change. This is Python's solution to OOP's to handle overloaded method. 
                    A more elegant way would be to use DuckTyping but singledispatchmethod is more explicit and for our
                    current simplistic need we will encapsulate it in this class. 
                """
                should_call_back =self.process_llm_tool_call(choices.choice, completion)
                """Process the entire response before calling the LLM again."""
                if(call_back_LLM == False and should_call_back == True):
                    call_back_LLM = True                     
            if(call_back_LLM):
                chat_response = self.client.chat.completions.create(model=model, messages=self.get_messages(), response_model=GeneralChat)
                """ 
                Can only be a GeneralChat but we will type check it to make sure it is that and not another type that the Instructor or 
                the LLM thought it would be.
                """
                if isinstance(chat_response, GeneralChat):
                    self.add_message(self.ASSISTANT_ROLE, chat_response.message)
            self.num_calls += 1
        except Exception as e:
            logger.error(f"An error occurred: {e}", exc_info=True)
            return """This is embarrasing. I am an AI assistant who ever so often start hallucinating or stop following instruction.\
              I try my best not to do that but you caught me red handed. I have lost my marbles.\
              Can you please refresh and try again? If I still fail you can you please come back later?"""
        return self.get_last_message(role=self.ASSISTANT_ROLE)
