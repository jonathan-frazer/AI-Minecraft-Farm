import os
import openai
import keyboard
import time
import sounddevice as sd
from scipy.io.wavfile import write
import tempfile
from pydantic import BaseModel, Field
from typing import Literal
from mcrcon import MCRcon
import speech_recognition as sr
import numpy as np
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()
recognizer = sr.Recognizer()
animal_prompt = ChatPromptTemplate.from_messages([
    ("system", (
        "You are a talking animal chatbot, and you respond to users. "
        "You are ONLY allowed to pick from the nearby animals to respond as. "
        "If there are no animals, you must respond as the server, informing there is no one to talk to."
        "Make sure to display a wide range of emotions, such as happy, sad, curious, and angry."
        "Prioritize closer animals unless others are appropriate to respond to"
    )),
    ("human", "User: {input}, Nearby Mobs(Sorted by Distance to Player): {nearby_mobs}")
])

# Whisper 음성 인식 함수
def record_and_transcribe(fs=44100,chunk_duration=0.5):
    audio_chunks = []
    try:
        keyboard.wait('c')
        with sd.InputStream(samplerate=fs, channels=1, dtype='int16') as stream:
            while keyboard.is_pressed('c'):
                chunk, _ = stream.read(int(fs * chunk_duration))
                audio_chunks.append(chunk)
                print(f"⏺️ ...recording {len(audio_chunks)*chunk_duration:.1f}s", end="\r")

        # Combine all chunks into one array
        final_audio = np.concatenate(audio_chunks, axis=0)

        # Save to temp WAV file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmpfile:
            write(tmpfile.name, fs, final_audio)
            with open(tmpfile.name, "rb") as f:
                result = openai.audio.transcriptions.create(
                    model="whisper-1",
                    file=f
                )
                return result.text

    except KeyboardInterrupt:
        print("\n⛔ Interrupted by user.")
        return None

# GPT 응답 모델 정의
class AnimalResponse(BaseModel):
    animal: str = Field(description="The name of the animal, Capitalized")
    emotion: Literal["happy", "sad", "curious", "angry"] = Field(description="The Emotion of the Response")
    message: str = Field(description="The message the animal is saying back")
    affinity: int = Field(ge=-100, le=100, description="Integer Ranging from -100 to 100. -ve for hate, +ve for love. the value being the intensity of the emotion")

    def __str__(self):
        return f"🐾 {self.animal}: {self.message},\nEmotion:{self.emotion}\nAffinity:{self.affinity}"

def get_nearby_mobs():
    with MCRcon(os.getenv("RCON_HOST"), os.getenv("RCON_PASSWORD"),port=int(os.getenv("RCON_PORT"))) as mcr:
        mcr.command('execute as @p at @s positioned ^ ^ ^3 run function ai_farm:data_store/0')
        results = mcr.command('data get storage ai_farm:mobs nearby_mobs')
        nearby_mobs = (results.replace("Storage ai_farm:mobs has the following contents: ",''))

        return nearby_mobs
    
# GPT 응답 생성 함수
def get_gpt_response(prompt_text):
    llm = ChatOpenAI(
        model="gpt-4.1-nano",
        temperature=0,
        api_key=os.getenv("OPENAI_API_KEY")
    )
    animal_llm = llm.with_structured_output(AnimalResponse)
    chain = animal_prompt | animal_llm
    content = chain.invoke({"input": prompt_text, "nearby_mobs": get_nearby_mobs()})
    print("🤖 GPT Response:", content)
    try:
        return content
    except Exception as e:
        print("❌ Error parsing GPT JSON:", e)
        return None

# 마인크래프트 명령 전송 함수
def send_to_minecraft(animal_resp: AnimalResponse):
    try:
        with MCRcon(os.getenv("RCON_HOST"), os.getenv("RCON_PASSWORD"),port=int(os.getenv("RCON_PORT"))) as mcr:
            mcr.command(f'tellraw @a {{"text":"{animal_resp.animal}: {animal_resp.message}","color":"{emotion_to_color_text(animal_resp.emotion)}"}}')
            mcr.command(f'title @a actionbar {{"text":"Affinity {animal_resp.affinity}"}}')
            mcr.command(f'scoreboard players add {animal_resp.animal} affinity {animal_resp.affinity}')
            mcr.command(f'scoreboard players set {animal_resp.animal} emotion {emotion_to_score(animal_resp.emotion)}')

    except Exception as e:
        print("❌ Error sending to Minecraft:", e)

# 감정 문자열 → 점수 매핑
def emotion_to_score(emotion):
    mapping = { "happy": 1, "sad": 2, "curious": 3, "angry": 4 }
    return mapping.get(emotion.lower(), 0)

def emotion_to_color_text(emotion):
    mapping = { "happy": "green", "sad": "blue", "curious": "yellow", "angry": "red"}
    return mapping.get(emotion.lower(), 0)

# 🔁 전체 흐름 제어 (키보드 C 입력)
def run_ai_interaction():
    print("🔁 Begin Interaction, Hold Down C to start Recording and Release to Speak:-")
    while True:
        text = record_and_transcribe()
        print("User:"+text)
        if text:
            response = get_gpt_response(text)
            if response:
                send_to_minecraft(response)
        time.sleep(2)
            
# 실행
if __name__ == "__main__":
    run_ai_interaction()