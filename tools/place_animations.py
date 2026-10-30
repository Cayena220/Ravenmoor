#!/usr/bin/env python3
"""Write character clips from blender/exports/CharacterAnimations.json and CastAnimations.json into the .rbxlx, as
the Animations in ReplicatedStorage.Animations that EffectsController plays: an Animation per clip holding its
KeyframeSequence, with a KeyframeMarker on each keyframe the clip marks (a cast gesture's Release).

    python tools/place_animations.py                          list the clips, and which the place lacks
    python tools/place_animations.py BroomRideAshwind ...     add those clips, or replace them (writes a .bak first)

Build the JSON first with `python tools/blender.py blender/animations/character.py blender/animations/casting.py`.
Close the place in Studio before writing; like sync_scripts.py this refuses while Studio's lock file is there, unless
--force. A replaced clip that was published keeps its AnimationId, which still plays the old animation until you
publish it again.
"""
import json
import math
import shutil
import sys
import uuid
from pathlib import Path
from sync_scripts import PLACE, escape, scan

EXPORTS = Path(__file__).resolve().parents[1] / 'blender' / 'exports'
SOURCES = {'CharacterAnimations.json': 'character.py', 'CastAnimations.json': 'casting.py'}   # JSON: its script
FOLDER = 'ReplicatedStorage/Animations'
PARENT = {'LowerTorso': 'HumanoidRootPart', 'UpperTorso': 'LowerTorso', 'Head': 'UpperTorso'}
for side in ('Left', 'Right'):
    PARENT.update({side + 'UpperArm': 'UpperTorso', side + 'LowerArm': side + 'UpperArm', side + 'Hand': side + 'LowerArm',
                   side + 'UpperLeg': 'LowerTorso', side + 'LowerLeg': side + 'UpperLeg', side + 'Foot': side + 'LowerLeg'})
EASING = {'Linear': 0, 'Constant': 1, 'Elastic': 2, 'Cubic': 3, 'Bounce': 4, 'CubicV2': 5}   # Enum.PoseEasingStyle
PRIORITY = {'Idle': 0, 'Movement': 1, 'Action': 2, 'Action2': 3, 'Action3': 4, 'Action4': 5, 'Core': 1000}


def ref(): return 'RBX' + uuid.uuid4().hex.upper()


def number(v):
    v = round(v, 7) + 0.0
    return str(int(v)) if v == int(v) else repr(v)


def cframe(x, y, z, qx, qy, qz, qw):
    """A CoordinateFrame from a position and a quaternion."""
    n = math.sqrt(qx * qx + qy * qy + qz * qz + qw * qw); qx, qy, qz, qw = qx / n, qy / n, qz / n, qw / n
    r = [[1 - 2 * (qy * qy + qz * qz), 2 * (qx * qy - qz * qw), 2 * (qx * qz + qy * qw)],
         [2 * (qx * qy + qz * qw), 1 - 2 * (qx * qx + qz * qz), 2 * (qy * qz - qx * qw)],
         [2 * (qx * qz - qy * qw), 2 * (qy * qz + qx * qw), 1 - 2 * (qx * qx + qy * qy)]]
    cells = [('X', x), ('Y', y), ('Z', z)] + [(f'R{i}{j}', r[i][j]) for i in range(3) for j in range(3)]
    return '<CoordinateFrame name="CFrame">' + ''.join(f'<{k}>{number(v)}</{k}>' for k, v in cells) + '</CoordinateFrame>'


def pose(part, keyed, easing):
    """The Pose for `part` and the Poses of the parts under it. Parts the clip doesn't key are there only to hold
    the chain, with no weight."""
    children = ''.join(pose(child, keyed, easing) for child in PARENT if PARENT[child] == part and wanted(child, keyed))
    value = keyed.get(part, [0, 0, 0, 0, 0, 0, 1])
    return (f'<Item class="Pose" referent="{ref()}"><Properties>{cframe(*value)}'
            f'<token name="EasingDirection">2</token><token name="EasingStyle">{EASING[easing.get(part, "Cubic")]}</token>'
            f'<float name="Weight">{1 if part in keyed else 0}</float><string name="Name">{part}</string>'
            f'</Properties>{children}</Item>')


def wanted(part, keyed):
    """Whether the Pose tree needs `part`: it is keyed, or a part under it is."""
    return part in keyed or any(PARENT[c] == part and wanted(c, keyed) for c in PARENT)


def markers(clip, time):
    """The KeyframeMarkers for the keyframe at `time`: AnimationTrack:GetMarkerReachedSignal(name) fires there."""
    return ''.join(f'<Item class="KeyframeMarker" referent="{ref()}"><Properties><string name="Name">{escape(name)}</string>'
                   f'<string name="Value"></string></Properties></Item>'
                   for at, name in clip.get('markers', []) if abs(at - time) < 1e-4)


def animation(name, clip):
    frames = ''.join(f'<Item class="Keyframe" referent="{ref()}"><Properties><float name="Time">{number(time)}</float>'
                     f'<string name="Name">Keyframe</string></Properties>{pose("HumanoidRootPart", keyed, clip["easing"])}'
                     f'{markers(clip, time)}</Item>'
                     for time, keyed in clip['keys'])
    return (f'<Item class="Animation" referent="{ref()}"><Properties><Content name="AnimationId"><null></null></Content>'
            f'<string name="Name">{escape(name)}</string></Properties>'
            f'<Item class="KeyframeSequence" referent="{ref()}"><Properties>'
            f'<bool name="Loop">{"true" if clip["loop"] else "false"}</bool>'
            f'<token name="Priority">{PRIORITY[clip["priority"]]}</token><string name="Name">{escape(name)}</string>'
            f'</Properties>{frames}</Item></Item>\n')


def main():
    names = [a for a in sys.argv[1:] if not a.startswith('--')]
    clips = {}
    for source, script in SOURCES.items():
        path = EXPORTS / source
        if not path.exists():
            raise SystemExit(f'{path.relative_to(PLACE.parent)} is missing: python tools/blender.py blender/animations/{script}')
        clips.update(json.loads(path.read_text(encoding='utf-8')))
    text = PLACE.read_bytes().decode('utf-8')
    nodes = scan(text)
    if FOLDER not in nodes: raise SystemExit(f'{FOLDER} is missing from {PLACE.name}.')
    if not names:
        for name, clip in clips.items():
            print(f'{name:22} {clip["length"]:4} s, {len(clip["keys"]):2} keys',
                  '' if f'{FOLDER}/{name}' in nodes else '  (not in the place)')
        print(__doc__.split('\n\n')[1])
        return 0
    unknown = [n for n in names if n not in clips]
    if unknown: raise SystemExit('Not in the JSON: ' + ', '.join(unknown))
    lock = PLACE.with_name(PLACE.name + '.lock')
    if lock.exists() and '--force' not in sys.argv:
        print(f'Roblox Studio has {PLACE.name} open ({lock.name} exists).')
        print('Save any Studio edits, close the place in Studio, then run this again.')
        print('(If Studio is already closed, the lock is stale: delete it or pass --force.)')
        return 2
    edits = []
    for name in names:
        node = nodes.get(f'{FOLDER}/{name}')
        if node is None:
            edits.append((nodes[FOLDER]['close'], nodes[FOLDER]['close'], animation(name, clips[name]))); print('add    ', name)
            continue
        if node['cls'] != 'Animation': raise SystemExit(f'{FOLDER}/{name} is a {node["cls"]}, not an Animation.')
        start, end = node['open'], node['close'] + len('</Item>')
        published = text.find('<Content name="AnimationId"><url>', start, text.find('</Properties>', start))
        item = animation(name, clips[name]).rstrip('\n')
        if published >= 0:   # keep the published id, so a live game still plays something
            at = text.index('</Content>', published) + len('</Content>')
            item = item.replace('<Content name="AnimationId"><null></null></Content>', text[published:at], 1)
            print(f'replace {name} (published: save its KeyframeSequence to Roblox again and update the AnimationId)')
        else:
            print('replace', name)
        edits.append((start, end, item))
    for start, end, new in sorted(edits, key=lambda e: e[0], reverse=True):
        text = text[:start] + new + text[end:]
    backup = PLACE.with_name(PLACE.name + '.bak')
    shutil.copyfile(PLACE, backup)
    PLACE.write_bytes(text.encode('utf-8'))
    print(f'Wrote {len(names)} clips to {FOLDER} in {PLACE.name}. Previous version: {backup.name}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
