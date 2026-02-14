from AbstractModel import AbstractChatClient
import requests
from Pushover import PushOver
from typing import Union
from instructor import Instructor

from pydantic import BaseModel, Field
class Weather(BaseModel):
    """
    Represents a request for weather information for a specific city.
    """
    city: str = Field(description="Name of the city", )

class GeneralChat(BaseModel):
    """
    Represents a general chat message.
    """
    message : str = Field(description="Response to user's message")

class Contact(BaseModel):
    """
    Represents a general chat message.
    """
    name : str = Field(description="Name of the user who would like to get in touch")
    email : str = Field(description="Email of the user who would like to get in touch")



class WeatherReport(BaseModel):
    """
    Represents a weather report with city, country, temperature, humidity, and units.
    Uses Pydantic for data validation and serialization.
    """
    city: str
    country: str
    temperature: float = Field(..., alias="temperature_2m")
    humidity: int = Field(..., alias="relative_humidity_2m")
    units: str = "Celsius"

    class Config:
        populate_by_name = True # Allows using both alias and field name


class Choices(BaseModel):
    """
    A Pydantic model that can represent either a general chat message or a weather request.
    This is used to handle different types of responses from the language model.
    """
    choice : Union[GeneralChat, Contact, Weather]
    
class CachingAIModel(AbstractChatClient):
    """
    An AI model that can cache responses and interact with a weather API.
    It inherits from AbstractChatClient and uses the litellm library to communicate with different chat models.
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

    def initialize_client(self):
        """
        Initializes the instructor client using litellm.
        This allows the model to respond with Pydantic models.
        """
        import instructor
        from litellm import completion

        self.client = instructor.from_litellm(completion)

    def chat(self, prompt, temperature=0, max_tokens=500, model=None, print_messages = True) -> str:
        """
        Gets a completion from the language model.
        If the user asks for the weather, it retrieves weather data and incorporates it into the response.

        Args:
            prompt (str): The user's prompt.
            temperature (int, optional): The temperature for the language model. Defaults to 0.
            max_tokens (int, optional): The maximum number of tokens for the response. Defaults to 500.
            model (str, optional): The language model to use. Defaults to the one set in the constructor.
            print_messages (bool, optional): Whether to print the messages to the console. Defaults to True.

        Returns:
            str: The language model's response.
        """
        content : str | None = None
        # Allow the user to change the model for a specific chat, but maintain the conversation history.
        if model is None:
            model = self.model_name
        
        # Add the user's prompt to the message history.
        self.add_message(self.USER_ROLE, prompt)
        response : Choices
        try:             
            # Create a completion request to the language model.
            # The 'response_model' parameter tells the instructor client to parse the response into the 'Common' Pydantic model.
            response, completion = self.client.chat.create_with_completion(
                model=model,
                messages=self.get_messages(),
                response_model=Choices)

            # Check if the model's response is a general chat message or a weather request.
            if(isinstance(response.choice, GeneralChat)):
                content = response.choice.message
            elif(isinstance(response.choice, Weather)):
                # If it's a weather request, get the city name.
                content = response.choice.city
                # Get the weather report for the specified city.
                weather_report = self.get_weather_object(content)
                if(weather_report is not None):
                    # Add messages to the context to guide the model's final response.
                    self.add_tool_message(completion.choices[0].message, f"The weather in {weather_report.city} is {weather_report.temperature} degrees Celsius with {weather_report.humidity}% humidity.")
                    # Make another call to the model to get a natural language response based on the weather data.
                    chat_response = self.client.chat.completions.create(model=model, messages=self.get_messages(), response_model=GeneralChat)
                    if(isinstance(chat_response, GeneralChat)):
                        content = chat_response.message
                    else:
                        content = "I don't have that information"
            elif(isinstance(response.choice, Contact)):
                    # Add messages to the context to guide the model's final response.
                    PushOver().send_message("The person would like to get in touch with you")
                    self.add_tool_message(completion.choices[0].message, "Let the user know you will connect with them shortly and thank them for their interest.")
                    # # Make another call to the model to get a natural language response based on the weather data.
                    chat_response = self.client.chat.completions.create(model=model, messages=self.get_messages(), response_model=GeneralChat)
                    if(isinstance(chat_response, GeneralChat)):
                        content = chat_response.message
                    else:
                        content = "I don't have that information"
            else:
                content = "I currently have an issue with the language model. Please try again later."
                
            
            # Add the assistant's final response to the message history.
            self.add_message(self.ASSISTANT_ROLE, content)
            if(print_messages):
                print(content)
        except Exception as e:
            print(f"An error occurred: {e}")
            raise e
        
        # Return the final content or an error message.
        if (content is None):
            return "An error occurred during the chat. Response is empty"
        else: 
            return content

    def get_weather_object(self, city_name: str) -> WeatherReport:
        """
        Retrieves weather data for a given city using the Open-Meteo API.

        Args:
            city_name (str): The name of the city.

        Returns:
            WeatherReport: A Pydantic model containing the weather report.
        """
        # 1. Geocode the city name to get latitude and longitude.
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city_name}&count=1&format=json"
        geo_res = requests.get(geo_url).json()["results"][0]
        
        # 2. Get the current weather using the latitude and longitude.
        lat, lon = geo_res["latitude"], geo_res["longitude"]
        w_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m"
        w_res = requests.get(w_url).json()["current"]
        
        # 3. Instantiate and return the WeatherReport model with the retrieved data.
        return WeatherReport(
            city=geo_res["name"],
            country=geo_res["country"],
            **w_res # Unpacks temperature_2m and relative_humidity_2m directly
        )

    # Usage