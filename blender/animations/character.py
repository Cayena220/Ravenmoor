"""Character animations for R15 avatars: Walk, Sprint, and a sideways Tumble to the left and to the right.

The rig's bones are the R15 joints, named after the part each one moves (LowerTorso is the Root joint, UpperTorso
the Waist, LeftUpperLeg the LeftHip, and so on), with their pivots at a Studio avatar's rest pose in studs from the
HumanoidRootPart. Every bone stands upright and is turned so its axes are Roblox's: X right, Y up, Z back. The R15
joint frames are axis-aligned too, so a bone's keyed rotation is exactly the joint's Transform in game:
+X swings a hanging limb forward, -X leans the torso forward, +Y turns to the left, and Z rolls to a side.

Each clip exports as Character<Name>.fbx with a preview strip of four frames. CharacterAnimations.json lists every
key pose as Roblox CFrames (position and quaternion) per part, with the clip's length, looping and priority. Studio
builds the KeyframeSequences from it, as EffectsController expects under ReplicatedStorage.Animations.
"""
import json
import math
import bpy
import rbx

SKIN = (212, 169, 126); ROBE = (76, 101, 120); TROUSERS = (58, 52, 48); BOOTS = (74, 54, 40)


def bl(x, y, z):
    """A Roblox position (X right, Y up, Z back) in Blender (Z up, front -Y): Blender -X is Roblox +X."""
    return (-x, z, y)


# Pivots and parts of the left side, in studs from the HumanoidRootPart; the right side mirrors X.
LEFT = {
    'UpperArm': ('UpperTorso', (-1.0, 0.763, 0), (-1.193, 0.301, 0.019), (0.570, 1.095, 0.783), ROBE),
    'LowerArm': ('UpperArm', (-1.5, 0.035, 0), (-1.310, -0.246, 0.102), (0.627, 0.948, 0.617), ROBE),
    'Hand': ('LowerArm', (-1.5, -0.725, 0), (-1.383, -0.941, 0.002), (0.693, 1.102, 0.744), SKIN),
    'UpperLeg': ('LowerTorso', (-0.5, -1.0, 0), (-0.424, -1.439, -0.058), (0.760, 1.478, 0.769), TROUSERS),
    'LowerLeg': ('UpperLeg', (-0.5, -1.937, 0), (-0.446, -2.255, 0.045), (0.742, 1.144, 0.821), TROUSERS),
    'Foot': ('LowerLeg', (-0.453, -2.611, 0.011), (-0.453, -2.657, -0.139), (0.836, 0.628, 1.242), BOOTS),
}
JOINTS = {   # part: (parent, pivot, part centre, part size, colour)
    'HumanoidRootPart': (None, (0, 0, 0), None, None, None),
    'LowerTorso': ('HumanoidRootPart', (0, -1.0, 0), (0, -0.870, -0.100), (1.696, 0.935, 0.952), ROBE),
    'UpperTorso': ('LowerTorso', (0, -0.6, 0), (0, 0.144, -0.044), (1.815, 1.773, 1.110), ROBE),
    'Head': ('UpperTorso', (0, 1.0, 0), (0, 1.491, 0), (1.171, 1.191, 1.171), SKIN),
}
for side, sign in (('Left', 1), ('Right', -1)):
    for limb, (parent, pivot, centre, size, colour) in LEFT.items():
        flip = lambda p: (p[0] * sign, p[1], p[2])
        parent = parent if parent in JOINTS else side + parent
        JOINTS[side + limb] = (parent, flip(pivot), flip(centre), size, colour)
MOVING = [name for name in JOINTS if name != 'HumanoidRootPart']

rbx.scene('Character', frames=(0, 30))
rig = rbx.Rig('CharacterRig', [(name, parent, bl(*pivot), [a + b for a, b in zip(bl(*pivot), (0, 0, 0.4))])
                               for name, (parent, pivot, *_) in JOINTS.items()])
# Turn every upright bone half a turn about itself, so its X axis is Roblox's +X (Blender -X) and its Z axis Roblox's
# +Z (Blender +Y). Then a bone's local rotation reads in Roblox's axes.
bpy.context.view_layer.objects.active = rig.obj
bpy.ops.object.mode_set(mode='EDIT')
for bone in rig.obj.data.edit_bones: bone.roll = math.pi
bpy.ops.object.mode_set(mode='OBJECT')
for bone in rig.obj.data.bones:
    axes = bone.matrix_local.to_3x3()
    assert all(abs(axes[i][j] - want) < 1e-5 for (i, j), want in
               {(0, 0): -1, (2, 1): 1, (1, 2): 1}.items()), f'{bone.name} is not aligned to Roblox axes'

body = rbx.Mesh('Mannequin')
for name, (_, _, centre, size, colour) in JOINTS.items():
    if not size: continue
    if name == 'Head': body.sphere(0.6, bl(*centre), colour, segments=16, bone=name)
    else: body.box((size[0], size[2], size[1]), bl(*centre), colour, bone=name)
body.box((0.7, 0.12, 0.18), bl(0, 1.55, -0.57), TROUSERS, bone='Head')   # a visor, so the face reads in previews
mannequin = body.finish(sharp=40, rig=rig)


def mirror(pose):
    """The same pose on the other side: Left and Right swap, turns about Y and Z reverse, X moves reverse."""
    out = {}
    for name, (turn, move) in pose.items():
        swapped = name.replace('Left', '#').replace('Right', 'Left').replace('#', 'Right')
        out[swapped] = ((turn[0], -turn[1], -turn[2]), (-move[0], move[1], move[2]))
    return out


def P(**bones):
    """A pose: each bone given as (rx, ry, rz) degrees, or ((rx, ry, rz), (x, y, z)) with a move in studs."""
    return {name: (v if len(v) == 2 and isinstance(v[0], tuple) else (v, (0, 0, 0))) for name, v in bones.items()}


# Walk: one second a cycle. The leading leg strikes heel first while the other pushes off its toes; the arms
# swing against the legs and the shoulders turn against the hips, while the head keeps looking ahead.
walk_contact = P(LowerTorso=((0, 4, 0), (0, -0.08, 0)), UpperTorso=(0, -8, 0), Head=(0, 4, 0),
                 RightUpperLeg=(28, 0, 0), RightLowerLeg=(-4, 0, 0), RightFoot=(10, 0, 0),
                 LeftUpperLeg=(-22, 0, 0), LeftLowerLeg=(-18, 0, 0), LeftFoot=(-14, 0, 0),
                 LeftUpperArm=(20, 0, 0), LeftLowerArm=(16, 0, 0), RightUpperArm=(-20, 0, 0), RightLowerArm=(8, 0, 0))
walk_passing = P(LowerTorso=((0, 0, 0), (0, 0.06, 0)),
                 RightUpperLeg=(2, 0, 0), RightLowerLeg=(-6, 0, 0),
                 LeftUpperLeg=(8, 0, 0), LeftLowerLeg=(-42, 0, 0), LeftFoot=(6, 0, 0),
                 LeftUpperArm=(3, 0, 0), LeftLowerArm=(12, 0, 0), RightUpperArm=(-3, 0, 0), RightLowerArm=(10, 0, 0))

# Sprint: 0.6 s a cycle with a flight phase. The body leans in, the knee drives high, the trailing heel kicks up
# and the arms pump with bent elbows.
sprint_contact = P(LowerTorso=((-6, 6, 0), (0, -0.14, 0)), UpperTorso=(-10, -14, 0), Head=(14, 8, 0),
                   RightUpperLeg=(42, 0, 0), RightLowerLeg=(-14, 0, 0), RightFoot=(8, 0, 0),
                   LeftUpperLeg=(-26, 0, 0), LeftLowerLeg=(-62, 0, 0), LeftFoot=(-20, 0, 0),
                   LeftUpperArm=(48, 0, 0), LeftLowerArm=(80, 0, 0), RightUpperArm=(-42, 0, 0), RightLowerArm=(72, 0, 0))
sprint_flight = P(LowerTorso=((-6, 0, 0), (0, 0.18, 0)), UpperTorso=(-10, 0, 0), Head=(14, 0, 0),
                  RightUpperLeg=(-28, 0, 0), RightLowerLeg=(-30, 0, 0), RightFoot=(-28, 0, 0),
                  LeftUpperLeg=(56, 0, 0), LeftLowerLeg=(-92, 0, 0), LeftFoot=(6, 0, 0),
                  LeftUpperArm=(-30, 0, 0), LeftLowerArm=(70, 0, 0), RightUpperArm=(40, 0, 0), RightLowerArm=(84, 0, 0))


# Tumble right: half a second. The character drops into a tuck, rolls a full turn toward +X along the ground,
# coming in from 3 studs back toward where the dash began, then rises out of a crouch. Every frame of the roll is a
# key, a twelfth of a turn apart, so the turn's direction is never ambiguous and nothing dips between keys. Each
# key is settled on the mannequin: posed, measured, then moved so the body's middle follows the path and its lowest
# point just clears the floor, which a turn about the hips alone would not do (the tucked head sinks through).
def tuck(roll, x, y, open=0.0):
    k = 1 - open
    return P(LowerTorso=((0, 0, roll), (x, y, 0)), UpperTorso=(-28 * k, 0, 0), Head=(-22 * k, 0, 0),
             LeftUpperLeg=(80 * k, 0, 0), LeftLowerLeg=(-115 * k, 0, 0), LeftFoot=(10 * k, 0, 0),
             RightUpperLeg=(80 * k, 0, 0), RightLowerLeg=(-115 * k, 0, 0), RightFoot=(10 * k, 0, 0),
             LeftUpperArm=(55 * k, 0, 20 * k), LeftLowerArm=(105 * k, 0, 0),
             RightUpperArm=(55 * k, 0, -20 * k), RightLowerArm=(105 * k, 0, 0))


FLOOR = -2.971   # the floor under the rig: a standing avatar's HumanoidRootPart is 2.971 studs up
CLEAR = 0.04     # how far the rolling body stays off it


def extent(pose):
    """Pose the rig (no clip playing) and return the deformed mannequin's lowest point and its middle along
    Roblox X."""
    for bone in MOVING:
        turn, move = pose.get(bone, ((0, 0, 0), (0, 0, 0)))
        pb = rig.obj.pose.bones[bone]; pb.location = move; pb.rotation_euler = [math.radians(a) for a in turn]
    bpy.context.view_layer.update()
    shown = mannequin.evaluated_get(bpy.context.evaluated_depsgraph_get()); mesh = shown.to_mesh()
    points = [shown.matrix_world @ v.co for v in mesh.vertices]; shown.to_mesh_clear()
    return min(p.z for p in points), -(min(p.x for p in points) + max(p.x for p in points)) / 2


def settled(roll, x, open=0.0):
    low, middle = extent(tuck(roll, 0, 0, open))
    return tuck(roll, x - middle, FLOOR + CLEAR - low, open)


tumble_right = [(f, settled(-30 * f, -3 + 0.25 * f, 0.55 * max(0, f - 9) / 3)) for f in range(13)] + [(15, P())]
for bone in MOVING: rig.obj.pose.bones[bone].matrix_basis.identity()

CLIPS = {   # name: (keys, last frame, loops, priority, easing per part)
    'Walk': ([(0, walk_contact), (8, walk_passing), (15, mirror(walk_contact)), (23, mirror(walk_passing)),
              (30, walk_contact)], 30, True, 'Movement', {}),
    'Sprint': ([(0, sprint_contact), (5, sprint_flight), (9, mirror(sprint_contact)), (14, mirror(sprint_flight)),
                (18, sprint_contact)], 18, True, 'Movement', {}),
    'TumbleRight': (tumble_right, 15, False, 'Action', {'LowerTorso': 'Linear'}),
    'TumbleLeft': ([(f, mirror(p)) for f, p in tumble_right], 15, False, 'Action', {'LowerTorso': 'Linear'}),
}
PREVIEW_FRAMES = {'Walk': [0, 8, 15, 23], 'Sprint': [0, 5, 9, 14], 'TumbleRight': [0, 4, 8, 12], 'TumbleLeft': [0, 4, 8, 12]}

sc = bpy.context.scene
rig.obj.animation_data_create()
data = {}
for name, (keys, last, loops, priority, easing) in CLIPS.items():
    action = bpy.data.actions.new('Character' + name); action.use_fake_user = True
    rig.obj.animation_data.action = action
    sc.frame_start, sc.frame_end = 0, last
    for frame, pose in keys:
        for bone in MOVING:
            turn, move = pose.get(bone, ((0, 0, 0), (0, 0, 0)))
            rig.key(frame, bone, move=move, turn=turn)
    # Read each key pose back as the joint Transform Roblox will apply: the bone's pose in its own (Roblox) axes.
    moved = {b for _, pose in keys for b in pose}
    poses = []
    for frame, _ in keys:
        sc.frame_set(frame)
        pose = {}
        for bone in sorted(moved):
            m = rig.obj.pose.bones[bone].matrix_basis
            t, q = m.to_translation(), m.to_quaternion()
            pose[bone] = [round(v, 4) + 0.0 for v in (t.x, t.y, t.z, q.x, q.y, q.z, q.w)]
        poses.append([round(frame / rbx.FPS, 4), pose])
    data[name] = {'length': round(last / rbx.FPS, 4), 'loop': loops, 'priority': priority, 'easing': easing, 'keys': poses}
    rbx.export('Character' + name, [mannequin, rig.obj], animation=True, preview_frames=PREVIEW_FRAMES[name])

rbx.viewport((0, 0, -0.5), 12, turn=(80, 0, 35))
out = rbx.EXPORTS / 'CharacterAnimations.json'
out.write_text(json.dumps(data, separators=(',', ':')), encoding='utf-8')
summary = ', '.join('%s (%d keys)' % (n, len(d['keys'])) for n, d in data.items())
rbx.say(f'exports/{out.name}: {summary}')
