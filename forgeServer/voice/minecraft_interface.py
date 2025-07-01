from mcrcon import MCRcon
from dotenv import load_dotenv
import re
import os
import json
from pydantic import BaseModel, Field
from typing import Literal

#Load ENV Variables
load_dotenv()

PLAYER_NAME = os.getenv("PLAYER_NAME")
RCON_HOST = os.getenv("RCON_HOST")
RCON_PASSWORD = os.getenv("RCON_PASSWORD")
RCON_PORT = int(os.getenv("RCON_PORT"))

"""
Causes a Mob to Look at you and Listen and for a Given Duration
Returns a list of the Nearby Mobs who are listening
"""
def mob_fetch(text,suppressEcho=True,radius=6):
    try:
        with MCRcon(RCON_HOST, RCON_PASSWORD,port=RCON_PORT) as mcr:   
            if not suppressEcho and text:
                mcr.command(f'execute as {PLAYER_NAME} run say {text}')

            mcr.command(r"data merge storage ai_farm:mobs {nearby_mobs:[]}")
            mcr.command(f'execute as {PLAYER_NAME} at @s positioned ^ ^ ^{radius//2-1} as @e[type=!#ai_farm:nalive,distance=..{radius},type=!player] at @s run function ai_farm:data_store/1')
            results = mcr.command('data get storage ai_farm:mobs nearby_mobs')
            results = results.replace("Storage ai_farm:mobs has the following contents: ",'').strip()
            results = re.sub(r'([{,])\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1 "\2":', results)
            nearby_mobs = json.loads(results)
            print("MOB_FETCH_JSON:",nearby_mobs)
            
            return nearby_mobs
        
    except Exception as e:
        print("Could Not Connect to MC Server:",e)

def attention_grab(radius=6,max_duration=300):
    try:
        with MCRcon(RCON_HOST, RCON_PASSWORD,port=RCON_PORT) as mcr:   
            mcr.command(f'scoreboard players set {PLAYER_NAME} playerSpeakDur {max_duration}')
            mcr.command(f'execute as {PLAYER_NAME} at @s positioned ^ ^ ^{radius//2-1} as @e[type=!#ai_farm:nalive,distance=..{radius},type=!player] run scoreboard players set @e[type=!#ai_farm:nalive,distance=..{radius},type=!player] mbListenDur {max_duration}')
            mcr.command(f'effect give {PLAYER_NAME} slowness 2 4 true')
            mcr.command(f'effect give {PLAYER_NAME} weakness 2 4 true')
            mcr.command(f'effect give {PLAYER_NAME} jump_boost 2 144 true')
    except Exception as e:
        print("Could Not Connect to MC Server:",e)

def mob_respond(mob_name, message, affinity=0, emotion="curious"):
    def emotion_to_score(emotion):
        mapping = { "happy": 1, "sad": 2, "curious": 3, "angry": 4 }
        return mapping.get(emotion.lower(), 0)

    def emotion_to_color_text(emotion):
        mapping = { "happy": "green", "sad": "blue", "curious": "yellow", "angry": "red"}
        return mapping.get(emotion.lower(), 0)
    try:
        with MCRcon(RCON_HOST, RCON_PASSWORD,RCON_PORT) as mcr:
            mcr.command(f'tellraw @a {{"text":"{mob_name}: {message}","color":"{emotion_to_color_text(emotion)}"}}')
            mcr.command(f'title @a actionbar {{"text":"Affinity {affinity}"}}')
            mcr.command(f'scoreboard players add {mob_name} affinity {affinity}')
            mcr.command(f'scoreboard players set {mob_name} emotion {emotion_to_score(emotion)}')

    except Exception as e:
        print("❌ Error sending to Minecraft:", e)

def stop_listen():
    try:
        with MCRcon(RCON_HOST, RCON_PASSWORD,port=RCON_PORT) as mcr:   
            mcr.command(f'scoreboard players set {PLAYER_NAME} playerSpeakDur 15')
            mcr.command('execute as @e[type=!#ai_farm:nalive,type=!player,scores={mbListenDur=1..}] run function ai_farm:speech/hear')
    except Exception as e:
        print("Could Not Connect to MC Server:",e)

