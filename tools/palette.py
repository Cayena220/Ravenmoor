"""Ravenmoor's world palette: every structural colour on the map, by family, shared by the village and
Whisperwood (tools/build.py) and the academy (tools/academy.py). Builders use these names instead of RGB
values. Colours that are content, such as a shop's plaster, a house's colour or an NPC's robe, stay with
their data.
"""

# Stone. The castle uses two-tone stone with limestone dressings over a cobbled base course; the village
# uses granite and cobbled plinths.
CASTLE_STONE=(118,114,104); WEATHERED=(96,94,88); LIMESTONE=(176,166,142); COURSE=(92,90,84)
ARCH_SHADOW=(38,40,44); VILLAGE_STONE=(150,150,146); PLINTH=(118,112,104); GRANITE=(96,98,102)
RUNESTONE=(79,111,123); ROCK=(83,94,94); ROCK_DARK=(68,73,88); BRICK=(140,82,66)

# Roofs and metal.
SLATE=(54,60,68); RIDGE=(40,44,50); COPPER=(86,124,112); IRON=(52,54,58); GOLD=(202,160,83)

# Timber.
BEAM=(74,54,40); PLANK=(120,86,58); FLOORBOARD=(138,104,72); DOOR=(96,58,40); SIGNBOARD=(58,42,34)

# Paving, from main route to worn track. Roads and avenues, then squares, plazas and terraces, then garden
# paths, then the dirt where the forest path wears through.
ROAD=(146,139,121); PLAZA=(150,144,128); PLAZA_TILE=(128,120,106); PATH=(176,164,138); WORN=(122,100,72)
CURB=(104,108,112); VERGE=(104,98,70); ROAD_BAND=(118,110,96); FLOOR=(137,142,148)

# Ground and foliage. Every tree draws its canopy from the three FOLIAGE tones.
MEADOW=(108,130,102); FOREST_FLOOR=(66,83,70); CLEARING=(86,95,76); SHORE=(161,155,124)
FOLIAGE=((48,76,62),(54,86,66),(62,96,70)); TRUNK=(78,70,59); HEDGE=(66,92,58); WATER=(74,140,155)

# Light. One warm colour for every window and lantern that lights after dark, and for the light it casts.
# NIGHT_GLASS is an unlit window.
LAMPLIGHT=(255,196,128); NIGHT_GLASS=(58,68,80); CLEAR_GLASS=(214,232,236)

# Lettering on signs and floating nameplates.
SIGN_TEXT=(236,205,140); NAMEPLATE_TEXT=(249,231,191)
