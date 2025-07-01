import re
from langchain.prompts import ChatPromptTemplate
ANIMAL_SELECT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", (
        "Animal Selection Agent, your job is to route messages"
        "Select an animal from the nearby animals to route the message to."
        "Prioritize closer animals unless others are appropriate to respond to"
    )),
    ("human", "User: {input}, Nearby Animals(Sorted by Distance to Player): {nearby_animals}")
])

#Loads from the JSON File
import json
personality_data = []
with open('personality_traits.json') as f:
    personality_data = json.load(f)['animals']
animal_database = [personality_data['name'] for personality_data in personality_data]
PERSONALITY_SELECT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", (
        "You are an Animal Classification Agent, Your Job is to classify animals."
        "Given a user input, you must respond with the animal that best fits the user input."
        "You can only select options from your Animal Database."
        f"Animal Database: {animal_database}"
        "If there is no exact match you must select one that is similar"
    )),
    ("human", "Animal: {selected_animal}")
])

#It must be a function because it is dynamic
def create_animal_response_prompt(animal, personality):
    trimmed_animal = re.sub(r'"([a-zA-Z0-9_]+):([^"]+)"', r'"\2"',animal)
    system_prompt = f"You are a talking animal chatbot, and you respond to **Users**. \nYou must behave like a \"{trimmed_animal}\" \nwith the following personality traits: ```{personality}```\nAdditionally, you must take into account the **Context** under which you will be responding to the user."

    print("System Prompt: "+system_prompt)

    return ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "Message: {input}, Context: {context}")
    ])