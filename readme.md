This is a combination of a Python Script and a Datapack
Combined with the flexibility of a Server to make realistic sounds to Minecraft

Currently it requires the user to run the script along side the game

## How to Install

1. Install a normal Minecraft server for Forge 1.20.1.
2. Place the `mods` in the mods folder
3. Use the same `run.bat` script
4. Copy and Paste the `server.properties` in
5. Go into world -> datapacks -> Drop the `AI Farm Datapack` inside
6. Python Installation

- Open a terminal and cd into `voice`
- Do `pipenv install` if you haven't installed pipenv before
- Do `pipenv shell` to enter into the virtual environment
- Do `pip install -r requirements.txt` to install all the dependencies

Done

## How to Run

For this to Run all three components must be running simultaneously

### Server

If you've installed the server correctly, click run.bat and it should run the Server

### Python Script

-Open Terminal
-cd to forgeServer/voice
-Do `pipenv shell`
-Type in `python ai_animal_farm_full.py`
-And keep it running in the background

### Game

-Open Minecraft on Forge 1.20.1, with the same mods installed as the server
-Go to `Multiplayer` -> `Direct Connection` and type in `localhost`
-You should login

Now Simply walk up to an entity and Hold down C to Talk, and Release C to finish Talking

Note: This is a Concept, to Truly go one step further it could be taken in as a Java Mod to Really take advantage of the AI.
