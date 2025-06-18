import speech_recognition as sr
import openai
import time
import os
import keyboard
from mcrcon import MCRcon

# Set your OpenAI API key and RCON password here
openai.api_key = os.getenv("OPENAI_API_KEY")
rcon_host = os.getenv("RCON_HOST")
rcon_port = int(os.getenv("RCON_PORT"))
rcon_password = os.getenv("10101")

# Initialize recognizer
recognizer = sr.Recognizer()

# Animal profiles with personality
animal_profiles = {
    "minecraft:pig": "I love carrots and rolling in the mud!",
    "minecraft:cow": "I enjoy grazing and watching the clouds.",
    "minecraft:sheep": "I love my wool and jumping in fields!",
    "minecraft:chicken": "Pecking seeds is my favorite hobby.",
    "alexsmobs:elephant": "I am strong and gentle. I love water.",
    "alexsmobs:raccoon": "I am curious and like shiny things.",
    "alexsmobs:kangaroo": "I love jumping and boxing!",
    # Add more animal types as needed
}

# Emotion response examples
emotion_response_map = {
    "happy": "I'm feeling really good!",
    "sad": "I'm a bit down...",
    "angry": "Leave me alone!",
    "anxious": "I'm feeling nervous...",
    "neutral": "Just chilling."
}

# Connect to Minecraft RCON
def connect_rcon():
    return MCRcon(rcon_host, rcon_password, port=rcon_port)

# Detect nearest animal based on player's facing direction
def detect_nearest_animal(mcr) -> str:
    try:
        mcr.command('tag @e[tag=target_animal] remove target_animal')
        mcr.command('execute as @p at @s run tag @e[type=!player,distance=..5,sort=nearest,limit=1] add target_animal')
        result = mcr.command('data get entity @e[tag=target_animal,limit=1] Id')
        print(f"Detected entity raw result: {result}")
        mob = extract_mob_id(result)
        print(f"Detected mob: {mob}")
        return mob
    except Exception as e:
        print(f"Detection error: {e}")
        return "unknown"

def extract_mob_id(entity_data: str) -> str:
    import re
    match = re.search(r'"id":"([^"]+)"', entity_data)
    if match:
        return match.group(1)
    match = re.search(r'Id: ([\w:.]+)', entity_data)
    if match:
        return match.group(1)
    return "unknown"

# Analyze emotion using OpenAI
def analyze_emotion(text: str) -> str:
    try:
        system_prompt = (
            "You are an AI that detects human emotions. "
            "Return only one word: happy, sad, angry, anxious, or neutral "
            "based on the following sentence."
        )
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ]
        )
        result = response["choices"][0]["message"]["content"].strip().lower()
        if result in emotion_response_map:
            return result
        return "neutral"
    except Exception as e:
        print("Emotion analysis error:", e)
        return "neutral"

# Main loop
with connect_rcon() as mcr:
    print("System ready. Press 'C' to talk to an animal.")
    while True:
        if keyboard.is_pressed('c'):
            with sr.Microphone() as source:
                print("Listening...")
                try:
                    audio = recognizer.listen(source, timeout=5)
                    text = recognizer.recognize_google(audio, language="en-US")
                    print(f"You said: {text}")
                    emotion = analyze_emotion(text)

                    mcr.command(f'bossbar set emotion_bar name "Emotion: {emotion.capitalize()}"')
                    mcr.command(f'bossbar set emotion_bar value 100')
                    mcr.command(f'bossbar set emotion_bar visible true')
                    mcr.command(f'bossbar set emotion_bar players @a')

                    mob_id = detect_nearest_animal(mcr)
                    profile = animal_profiles.get(mob_id, "I'm just a neutral mob.")
                    animal_response = emotion_response_map.get(emotion, "Hmm.")
                    final_text = f"I am a {mob_id.split(':')[-1]}, and I feel {emotion}. {profile} {animal_response}"

                    print(f"Animal: {final_text}")
                    mcr.command(f'tellraw @a ["",{{"text":"[AI Animal] ","color":"gold"}},{{"text":"{final_text}","color":"white"}}]')

                    time.sleep(1)

                except sr.UnknownValueError:
                    print("Could not understand audio.")
                except Exception as e:
                    print("Error:", e)
        time.sleep(0.1)