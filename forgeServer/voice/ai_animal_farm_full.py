from langgraph.graph import StateGraph, START, END
from minecraft_interface import mob_fetch,mob_respond,stop_listen,echo_message
from audio_recognition import record_and_transcribe
from ai_pydantic_models import AnimalResponse
import ai_pydantic_models
import ai_prompts
from typing import Literal
from typing_extensions import TypedDict
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import keyboard
from collections import defaultdict
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
    animal_description: str = "Cautious" #Personality grabbed from the user
    received_message: AnimalResponse
    context: str = "First Meeting"
    nearby_mobs: list[dict] = [] #List of nearby mobs
    tags: list[str]
    
def initialization_node(state) -> State:
    """Initializes the State with Default Values"""
    print("🔁 Begin Interaction, Hold Down C to start Recording and Release to Speak:-")
    keyboard.wait('c')
    return {
        "nearby_mobs": [],
        "sent_message": "",
        "animal": "None",
        "animal_description": "Cautious",  # Default personality
        "received_message": None,
        "context": "First Meeting",
        "tags": []
    }

"""Gathers Audio Information from the User"""
def audio_recognition_node(state) -> State:
  user_message = record_and_transcribe()
  print("User🎤: " + user_message)

  #THIS LINE ECHOS BACK TO MINECRAFT, DELETE IT TO REMOVE ECHOING TO MC
  if user_message:  echo_message(user_message)

  return {"sent_message": user_message}

"""Scans for Nearby Mobs and Fetches their Information"""
def mob_scan_node(state)-> State:
  print("🔍-----Mob Scan-----")
  nearby_mobs = mob_fetch()
  return {"nearby_mobs": nearby_mobs}
  
"""Selects a Mob based on the User Input and Nearby Mobs"""
def mob_selector_node(state) -> State:
  print("👂-----Mob Listening-----")
  
  if not state.get('nearby_mobs',[]):
    stop_listen()
    print("⛔No Nearby Mobs")
    return {"sent_message": state['sent_message'], 
            "animal": "None"}
  
  else:
    tag_indexer = defaultdict(list)
    for mob in state['nearby_mobs']:
      mob_name = mob['name']
      mob_tags = mob.get('tags', [])
      tag_indexer[mob_name].extend(mob_tags)
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
    return "initialization"
  return ["assign_personality","fetch_context"]

"""Assigns a Personality to the Animal based on the Given JSON File"""
def personality_assign_node(state) -> State:
  print("😃-----Assigning Personality-----")
  #Lookup File
  personality_data = []
  with open('personality_traits.json') as f:
    personality_data = json.load(f)['animals']
  animal_database = [personality_data['name'] for personality_data in personality_data]

  #Fetch Closest Animal
  personality_llm = openai_llm.with_structured_output(ai_pydantic_models.create_classifier_model(animal_database))
  chain = ai_prompts.PERSONALITY_SELECT_PROMPT | personality_llm
  content = chain.invoke({"selected_animal": state['animal']})
  description = "Cautious of the User"

  #Use the Animal to make a Key Comparison
  for animal_info in personality_data:
     if animal_info['name'] == content.animal:
        description = animal_info['description']
  print("Animal Description: ",description)

  return {"animal_description": description}

"""Fetches the Context Node based on the Tags"""
def fetch_context_node(state) -> State:
  print("📝-----Fetching Context-----")
  
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

  #Print out Context
  print("Context:", context)

  return {"context": context}
  
"""Processes the node User Text, and responds with an LLM"""
def animal_response_node(state) -> State:
    print("💬-----Animal Response-----")
    animal_llm = openai_llm.with_structured_output(AnimalResponse)
    chain =  ai_prompts.create_animal_response_prompt(state['animal'],state['animal_description']) | animal_llm
    content = chain.invoke({"input": state['sent_message'], "context": state['context']})

    #Fetch Response Object
    print("GPT Output:",content)

    #Parse and Send to MC
    mob_name = (state['animal'].split(':')[1].strip() if ':' in state['animal'] else state['animal']).title()
    message = content.message;affinity = content.affinity;emotion = content.emotion
    mob_respond(mob_name,message,affinity=affinity,emotion=emotion)

    #After message is sent stop listening
    stop_listen()

    return {"received_message": content}

def build_graph():
    # state
    builder = StateGraph(State)

    # nodes
    builder.add_node("initialization", initialization_node)
    builder.add_node("input_audio", audio_recognition_node)
    builder.add_node("mob_scan", mob_scan_node)
    builder.add_node("mob_select", mob_selector_node) 
    builder.add_node("assign_personality", personality_assign_node)
    builder.add_node("fetch_context", fetch_context_node)
    builder.add_node("generate_response", animal_response_node)

    # edges
    builder.add_edge(START, "initialization")
    builder.add_edge("initialization", "mob_scan")
    builder.add_edge("initialization", "input_audio")
    builder.add_edge("mob_scan", END)

    builder.add_edge("input_audio", "mob_select")
    builder.add_conditional_edges("mob_select", mob_check)
    builder.add_edge("fetch_context", "generate_response")
    builder.add_edge("assign_personality", "generate_response")
    builder.add_edge("generate_response", "initialization")

    # compile
    graph = builder.compile()
    return graph

if __name__ == "__main__":
  graph = build_graph()
  graph.invoke({}, {"recursion_limit": 10_000_000})
