summon area_effect_cloud ~ ~-0.3 ~ {Duration:1}
execute positioned ~ ~-0.3 ~ run ride @s mount @e[type=area_effect_cloud,limit=1,sort=nearest,distance=..0.1]

#Store Object
execute positioned ~ ~-0.3 ~ run data modify storage ai_farm:mobs current set value {}
execute positioned ~ ~-0.3 ~ run data modify storage ai_farm:mobs current.name set from entity @e[type=area_effect_cloud,limit=1,sort=nearest,distance=..0.1] Passengers[0].id
execute positioned ~ ~-0.3 ~ run data modify storage ai_farm:mobs current.tags set from entity @e[type=area_effect_cloud,limit=1,sort=nearest,distance=..0.1] Passengers[0].Tags

execute positioned ~ ~-0.3 ~ run data modify storage ai_farm:mobs nearby_mobs append from storage ai_farm:mobs current

ride @s dismount