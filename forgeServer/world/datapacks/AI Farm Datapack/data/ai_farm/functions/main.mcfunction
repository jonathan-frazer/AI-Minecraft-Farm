#Player Speaking
execute as @a[scores={playerSpeakDur=1..}] at @s run function ai_farm:speech/0

#Mob Listening
execute as @e[type=!player,type=!#ai_farm:nalive,scores={mbListenDur=1..}] at @s run function ai_farm:speech/1

#Proximity to Barn
execute as @e[type=marker,tag=barnMarker] at @s as @e[distance=..16,type=!#ai_farm:nalive,type=!player,tag=!aiNearBarn] run tag @s add aiNearBarn
execute as @e[type=!#ai_farm:nalive,type=!player,tag=aiNearBarn] at @s unless entity @e[type=marker,tag=barnMarker,limit=1,distance=..16] run tag @s remove aiNearBarn