summon area_effect_cloud ~ ~ ~ {Duration:1}
ride @s mount @e[type=area_effect_cloud,limit=1,sort=nearest,distance=..0.1]
data modify storage ai_farm:mobs nearby_mobs append from entity @e[type=area_effect_cloud,limit=1,sort=nearest,distance=..0.1] Passengers[0].id
ride @s dismount