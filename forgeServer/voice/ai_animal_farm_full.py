from langgraph.graph import StateGraph, START
from minecraft_interface import mob_fetch,mob_respond,stop_listen
from audio_recognition import record_and_transcribe
from ai_pydantic_models import AnimalResponse
import ai_pydantic_models
import ai_prompts
from typing import Literal
from typing_extensions import TypedDict
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os
import json

load_dotenv()
openai_llm = ChatOpenAI(
        model="gpt-4.1-nano",
        temperature=0.4,
        api_key=os.getenv("OPENAI_API_KEY")
    )
class State(TypedDict):
    sent_message: str
    animal: str
    received_message: AnimalResponse
    traits: str = "Curious" #Personality grabbed from the user
    context: str = "First Meeting"
    tags: list[str]
    
"""Gathers Audio Information from the User"""
def audio_recognition_node(state) -> State:
  print("🔁 Begin Interaction, Hold Down C to start Recording and Release to Speak:-")
  user_message = record_and_transcribe()
  print("User: " + user_message)
  return {"sent_message": user_message}
  
"""Emits the Sound to Nearby Mobs, and selects one"""
def mob_fetch_node(state) -> State:
  print("-----Mob Listening-----")
  nearby_mobs = mob_fetch(state['sent_message'],suppressEcho=False)
  
  if not nearby_mobs:
    stop_listen()
    print("No Nearby Mobs")
    return {"sent_message": state['sent_message'], 
            "animal": "None"}
  
  else:
    tag_indexer = {mob['name']:mob.get('tags',[]) for mob in nearby_mobs}
    mob_names = list(tag_indexer.keys())

    selector_llm = openai_llm.with_structured_output(ai_pydantic_models.create_classifier_model(mob_names))
    chain = ai_prompts.ANIMAL_SELECT_PROMPT | selector_llm
    content = chain.invoke({"input": state['sent_message'], "nearby_animals": mob_names})

    print("🐾 Selected Animal: ", content.animal)

    return {"sent_message": state['sent_message'], 
            "animal": content.animal,
            "tags": tag_indexer[content.animal]}
  
  
"""Checks for Nearby mobs, else has to return back to taking Audio input"""
def mob_check(state):
  if state["animal"] == "None":
    print("⛔ No Mobs Found, Retrying...")
    return "input_audio"
  return ["assign_personality","fetch_context"]

def personality_assign_node(state) -> State:
  print("-----Assigning Personality-----")
  #Lookup File
  personality_data = []
  with open('personality_traits.json') as f:
    personality_data = json.load(f)['animals']
  animal_database = [personality_data['name'] for personality_data in personality_data]

  #Fetch Closest Animal
  personality_llm = openai_llm.with_structured_output(ai_pydantic_models.create_classifier_model(animal_database))
  chain = ai_prompts.PERSONALITY_SELECT_PROMPT | personality_llm
  content = chain.invoke({"selected_animal": state['animal']})
  traits = "Curious"

  #Use the Animal to make a Key Comparison
  for animal_info in personality_data:
     if animal_info['name'] == content.animal:
        traits = animal_info['traits']
  print("Personality Traits: ",traits)

  return {"traits": traits}

#Unfinished
def fetch_context_node(state) -> State:
  print("-----Fetching Context-----")
  
  #First Meeting
  context = "You are meeting the User for the first time"
  nearBarn = "aiNearBarn" in state['tags']
  
  repeatedInteraction = "aiSpokenTo" in state['tags']

  #Home showcase
  if nearBarn and repeatedInteraction:
    context = "You are being Introduced to your new Home by the User, you are grateful to them for their now home"
  #Repeated Interaction
  elif repeatedInteraction:
    context = "You are being Spoken to by the User, you are familiar with them."
  elif nearBarn:
    context = "You are near a local Barn and are curious to know more about it from the User who happens to own it"

  return {"context": context}
  
"""Processes the node User Text, and responds with an LLM"""
def animal_response_node(state) -> State:
    print("-----Animal Response-----")
    animal_llm = openai_llm.with_structured_output(AnimalResponse)
    chain =  ai_prompts.create_animal_response_prompt(state['animal'],state['traits']) | animal_llm
    content = chain.invoke({"input": state['sent_message'], "context": state['context']})

    #Getting State
    print("GPT Input:",state)

    #Fetch Response Object
    print("GPT Output:",content)

    #Parse and Send to MC
    mob_name = content.animal
    message = content.message
    affinity = content.affinity
    emotion = content.emotion
    mob_respond(mob_name,message,affinity=affinity,emotion=emotion)

    #After message is sent stop listening
    stop_listen()

    return {"received_message": content}

def build_graph():
    # state
    builder = StateGraph(State)

    # nodes
    builder.add_node("input_audio", audio_recognition_node)
    builder.add_node("mob_fetch", mob_fetch_node) 
    builder.add_node("assign_personality", personality_assign_node)
    builder.add_node("fetch_context", fetch_context_node)
    builder.add_node("generate_response", animal_response_node)

    # edges
    builder.add_edge(START, "input_audio")
    builder.add_edge("input_audio", "mob_fetch")
    builder.add_conditional_edges("mob_fetch", mob_check)
    builder.add_edge("assign_personality", "generate_response")
    builder.add_edge("fetch_context", "generate_response")
    builder.add_edge("generate_response", "input_audio")

    # compile
    graph = builder.compile()
    return graph

if __name__ == "__main__":
  graph = build_graph()
  print(graph.invoke({}, {"recursion_limit": 10_000_000}))
