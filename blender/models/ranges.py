"""The mountain ranges and woods round Ravenmoor (blender/terrain.py): exports/Ranges.fbx for Studio, and Ranges.blend.

They fill the land the map leaves open. Knife-edged ridges and needle spires rise from 18 studs off every road and
every area players walk, and the tallest ranges close the world in beyond the meadow. The script replays
tools/build.py and tools/layout.py, so the ranges always fit the map they are made for: rebuild them after the
layout or an area changes.

Ranges.fbx is one model, Ranges, holding two models: Mountains, about 16 tiles of under 20,000 triangles, and Woods,
about 5,000 trees in meshes of 300. Everything is coloured by vertex colours and stands where the game has it. Import
it with Insert Using Scene Position, then run blender/place_ranges.lua (blender/README.md).
"""
import xml.etree.ElementTree as ET
import build
import layout
import rbx
import terrain

# Each area players walk, by its top group in the map, and how far past its parts' centres the land stays flat.
AREAS = {'Hollowmere': 16, 'Ravenmoor Academy': 12, 'Castle Grounds': 10, 'Dueling Club': 10, 'Whisperwood': 14,
         'Mirrorlake': 54, **{name: 10 for name in layout.GROUNDS}}   # Mirrorlake's parts all stand near its middle


def name_of(node): return node.findtext("Properties/string[@name='Name']")


def centres(node):
    for part in node.iter('Item'):
        cf = part.find("Properties/CoordinateFrame[@name='CFrame']")
        if part.get('class') in ('Part', 'WedgePart') and cf is not None:
            yield float(cf.findtext('X')), float(cf.findtext('Z'))


rbx.scene('Ranges')
world, _, _ = build.make_world(build.item(ET.Element('roblox'), 'Workspace', 'Workspace'))
areas = []
for top in world.findall('Item'):
    name = name_of(top)
    if name in AREAS:
        xs, zs = zip(*centres(top)); pad = AREAS[name]
        areas.append((min(xs) - pad, max(xs) + pad, min(zs) - pad, max(zs) + pad))
    elif name.startswith('RuneChest'):
        x, z = next(centres(top)); areas.append((x - 8, x + 8, z - 8, z + 8))
land = terrain.Land(layout.ROADS, areas, layout.MEADOW)
heights, mountains = terrain.ranges(land)
woods, trees = terrain.woods(land, heights)
ranges = rbx.group('Ranges', [rbx.group('Mountains', mountains), rbx.group('Woods', woods)])
rbx.export('Ranges', [ranges, *ranges.children_recursive], auto_preview=False)
rbx.say(f'exports/Ranges.fbx: {len(mountains)} mountain tiles and {trees:,} trees in {len(woods)} meshes')
rbx.shot('Ranges', terrain.bl(520, 420, 640), terrain.bl(100, 0, 30), lens=26, resolution=(1800, 1100))
