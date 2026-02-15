from pydantic import BaseModel, Field
from typing import Union

from pydantic import BaseModel, Field
from typing import Union

__all__ = ["Weather", "GeneralChat", "Contact", "WeatherReport", "Choices"]

class Weather(BaseModel):
    """
    Represents a request for weather information for a specific city.
    """
    city: str = Field(description="Name of the city. The field should not be empty.")

class GeneralChat(BaseModel):
    """
    Represents a general chat message.
    """
    message : str = Field(description="Response to any user message by the LLM that is not about tool choice Weather or tool choice Contact")

class Contact(BaseModel):
    """
    Represents a general chat message.
    """
    name : str = Field(description="Name of the user if they want to get in touch. Ask the user for their name if they have not given it already. The field should not be empty.")
    email : str = Field(description="Email of the user if they want to get touch. Ask the user for their email if they have not given it already. The Field should not be empty. The field should have a valid email format")


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
