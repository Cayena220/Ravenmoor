"""A layout plan for Ravenmoor: blender/exports/WorldPlan.blend, the whole world (world.py) with the academy and
Whisperwood moved away from Hollowmere, so that players travel further between them. Only the Blender scene changes:
the game keeps its layout until a plan is chosen and made in tools/build.py, and World.blend still shows the game.

PLAN gives each area's move in Roblox studs (X east, Y up, Z south). Hollowmere stays, since players spawn there. The
academy goes north with its grounds (the training yard, the duel arena, Mirrorlake, its lamps, teachers and lesson
targets), and Whisperwood goes west with its monsters, chests and gate, and with Tobb, who sends players into it. The
academy road and the forest path are carried out to them, a forest road runs straight from the academy gate to the
forest path, and the meadow widens to hold them.

GROUNDS stands the Castle Grounds landmarks (tools/grounds.py) on the open land between: the flying pitch east of the
academy road, the Ruins of Old Ravenmoor between the three roads, the greenhouses near the village and the
groundskeeper's hut by Tobb at the forest edge. Each has its centre and the point on a road where its path starts.

Mountain ranges and woods (blender/terrain.py) fill the land round all of it, and --preview adds EEVEE pictures. The
build prints walking times between the places players walk to. Change the numbers and run this again to try another
layout.
"""
import runpy
from pathlib import Path

PLAN = {'Academy': (0, 0, -300), 'Forest': (-300, 0, 0)}
GROUNDS = {   # landmark: (centre, where its path leaves a road), Roblox (x, z)
    'Flying pitch': ((215, -32), (96, -4)),                  # off the academy road's east side
    'Ruins of Old Ravenmoor': ((-20, -60), (-20, 10.5)),     # off the forest path's north side
    'Greenhouses': ((-130, 90), (-130, 25.5)),               # off the forest path's south side
    "Groundskeeper's hut": ((-290, 54), (-290, 25.5)),       # across the forest path from Tobb
}

runpy.run_path(str(Path(__file__).with_name('world.py')), init_globals={'PLAN': PLAN, 'GROUNDS': GROUNDS})
