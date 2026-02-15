from AbstractModel import AbstractChatClient
import requests
from Pushover import PushOver
from instructor import Instructor, from_litellm
from functools import singledispatchmethod
from litellm import completion

# from pydantic import BaseModel, Field
from Models import GeneralChat, Weather, Contact, Choices, WeatherReport

    
class ChatTwin(AbstractChatClient):
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
        self.client = from_litellm(completion)

    @singledispatchmethod    
    def process_llm_tool_call(self, bm, completion):
        self.add_tool_message(completion.choices[0].message, "I cannot find the information for this request. Please try again.")

    @process_llm_tool_call.register(GeneralChat)
    def _(self, general_chat, completion):
        content = general_chat.message
        super().add_message(self.ASSISTANT_ROLE, content)


    @process_llm_tool_call.register(Weather)
    def _(self, weather, completion):
        # Get the weather report for the specified city.
        if(weather.city is None or weather.city.strip() == ""):
            self.add_tool_message(completion.choices[0].message, "Please ask them the name of the city that they want to know the weather for.")
        else :
            weather_report = self.get_weather_object(city_name=weather.city)

            if(weather_report is not None):
                # Add messages to the context to guide the model's final response.
                self.add_tool_message(completion.choices[0].message, f"The weather in {weather_report.city} is {weather_report.temperature} degrees Celsius with {weather_report.humidity}% humidity.")
                # Make another call to the model to get a natural language response based on the weather data.
            else:
                self.add_tool_message(completion.choices[0].message, f"I cannot find the information for {weather_report.city}")
        self.chat(callback=True) 

    @process_llm_tool_call.register(Contact)
    def _(self, contact, completion):
        # Add messages to the context to guide the model's final response.
        if(contact.name is None or contact.name.strip() == "" or contact.email is None or contact.email.strip() == ""):
            self.add_tool_message(completion.choices[0].message, content="Please ask them for their name if they have not given it already and ask them for their emailid")
        else:
            PushOver().send_message("The person would like to get in touch with you")
            self.add_tool_message(completion.choices[0].message, "Let the user know you will connect with them shortly and thank them for their interest.")
        # # Make another call to the model to get a natural language response based on the weather data.
        self.chat(callback=True) 


    def chat(self, prompt=None, temperature=0, max_tokens=500, model=None, print_messages = True, callback : bool = False) -> str:
    # Usage
        response : Choices
        # Allow the user to change the model for a specific chat, but maintain the conversation history.
        if(prompt is not None):
            self.add_message(self.USER_ROLE, prompt)
        if model is None:
            model = self.model_name
        try:             
            # Create a completion request to the language model.
            # The 'response_model' parameter tells the instructor client to parse the response into the 'Common' Pydantic model.
            if(callback == False):
                response, completion = self.client.chat.create_with_completion(
                    model=model,
                    messages=self.get_messages(),
                    response_model=Choices)            
                self.process_llm_tool_call(response.choice, completion)
            else :
                chat_response = self.client.chat.completions.create(model=model, messages=self.get_messages(), response_model=GeneralChat)
                if isinstance(chat_response, GeneralChat):
                    self.add_message(self.ASSISTANT_ROLE, chat_response.message)
        except Exception as e:
            print(f"An error occurred: {e}")
            return "I seem to have lost my marbles. Can you please try again? If I can't seem to find it can you please come back later?"
        return self.get_last_message(role=self.ASSISTANT_ROLE)

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


        


