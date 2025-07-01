from typing import Literal,Annotated
from pydantic import BaseModel, create_model, Field

def create_classifier_model(valid_animals):
    AnimalLiteral = Literal[tuple(valid_animals)]
    return create_model(
        'ClassifierResponse',
        animal=(AnimalLiteral, Field(description="The animal selected")),
        __base__=BaseModel
    )

class AnimalResponse(BaseModel):
    animal: str = Field(description="The name of the animal, Capitalized")
    emotion: Literal["happy", "sad", "curious", "angry"] = Field(description="The Emotion of the Response")
    message: str = Field(description="The message the animal is saying back")
    affinity: int = Field(ge=-100, le=100, description="Integer Ranging from -100 to 100. -ve for hate, +ve for love. the value being the intensity of the emotion")

    def __str__(self):
        return f"🐾 {self.animal}: {self.message},\nEmotion:{self.emotion}\nAffinity:{self.affinity}"