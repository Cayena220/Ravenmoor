"""Choose which of WorldPlan's oaks stand in the game, so the woods read as woods and not as a wall of crowns.

    python blender/thin_forest.py [--inside 16] [--outside 22]

WorldPlan stands 4,316 oaks a median 8.6 studs apart, while each crown is about 24 studs across. This keeps the largest
tree first and drops any oak closer than SPACING studs to one already kept: 16 inside Config.WorldBounds, where players
walk among them, and 22 on the far slopes, where they are scenery. Oaks whose crowns reach into the academy or a house
are dropped too. The garden's and Hollowmere's own trees are part of their design, so only the spacing thins them.

Reads exports/RobloxWorld/manifest.json and writes exports/RobloxWorld/forest_thinning.json: the manifest's
source_sha256, how many trees it lists, and the numbers of the oaks kept (Oak 0001 is the manifest's first tree).
thin_forest.lua removes the others from the place, and tools/validate.py checks the place against the list.
Run both again after an export that changes the manifest.
"""
import json, math, sys
from collections import defaultdict
from pathlib import Path

ARGS = sys.argv[1:]
SPACING = {'inside': float(ARGS[ARGS.index('--inside') + 1]) if '--inside' in ARGS else 16,
           'outside': float(ARGS[ARGS.index('--outside') + 1]) if '--outside' in ARGS else 22}
BOUNDS = {'MinX': -640, 'MaxX': 340, 'MinZ': -955, 'MaxZ': 290}   # src/shared/Config.lua, WorldBounds
CLEAR = ('AcademyExterior', 'EmberClaw', 'Stoneroot', 'Skyquill', 'Nightfang')
CROWN = 22   # studs from an oak's root to the edge of its crown, at scale 1 (the largest template is 46 across)
OUT = Path(__file__).resolve().parent / 'exports' / 'RobloxWorld'

manifest = json.loads((OUT / 'manifest.json').read_text())
trees = manifest['trees']
# A tree's matrix is in Roblox space; its last column is the root, its first the scaled X axis.
roots = [(t['matrix'][0][3], t['matrix'][2][3]) for t in trees]
scales = [math.hypot(t['matrix'][0][0], t['matrix'][1][0], t['matrix'][2][0]) for t in trees]

footprints = {}
for row in manifest['meshes']:
    if row['group'] not in CLEAR: continue
    (x, _, z), (sx, _, sz) = row['position'], row['size']
    lo = footprints.setdefault(row['group'], [math.inf, math.inf, -math.inf, -math.inf])
    lo[:] = [min(lo[0], x - sx / 2), min(lo[1], z - sz / 2), max(lo[2], x + sx / 2), max(lo[3], z + sz / 2)]


def crowds(i):
    """Whether oak i's crown reaches into one of the CLEAR buildings' footprints."""
    (x, z), reach = roots[i], CROWN * scales[i] + 4
    return any(a - reach < x < c + reach and b - reach < z < d + reach for a, b, c, d in footprints.values())


def inside(i):
    x, z = roots[i]
    return BOUNDS['MinX'] < x < BOUNDS['MaxX'] and BOUNDS['MinZ'] < z < BOUNDS['MaxZ']


cell = max(SPACING.values())
grid, kept, crowded = defaultdict(list), [], 0
for i in sorted(range(len(trees)), key=lambda i: (-scales[i], i)):
    if crowds(i): crowded += 1; continue
    (x, z), gap = roots[i], SPACING['inside' if inside(i) else 'outside']
    gx, gz = int(x // cell), int(z // cell)
    if any(math.hypot(x - roots[j][0], z - roots[j][1]) < gap
           for dx in (-1, 0, 1) for dz in (-1, 0, 1) for j in grid[(gx + dx, gz + dz)]): continue
    grid[(gx, gz)].append(i); kept.append(i)

kept = sorted(i + 1 for i in kept)
(OUT / 'forest_thinning.json').write_text(json.dumps({
    'source_sha256': manifest['source_sha256'], 'trees_in_manifest': len(trees), 'spacing': SPACING,
    'kept': kept}, indent=1))
print(f'{len(kept)} of {len(trees)} oaks kept ({sum(inside(i - 1) for i in kept)} inside the world bounds); '
      f'{crowded} dropped for crowding a building, the rest for spacing. Wrote {OUT / "forest_thinning.json"}')
