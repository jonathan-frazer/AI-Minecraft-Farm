#Decrement Timer
scoreboard players remove @s mbListenDur 1

#Look At Player
execute facing entity @p[scores={playerSpeakDur=1..}] feet run tp @s ~ ~ ~ ~ ~

#End Once timer Drops to Zero
execute if score @s mbListenDur matches ..0 run function ai_farm:speech/end