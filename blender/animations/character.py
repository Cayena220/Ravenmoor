"""Character animations for R15 avatars: Walk, Sprint, a Tumble to the left, the right, forward and back, the pose
for riding a broom (BroomRide), a ride of its own for flying each broom (BroomRideAshwind, BroomRideStoutbough,
BroomRideSwiftquill and BroomRideNightwing), each house's dash through the air on each broom
(BroomDash<House><Broom>), and Scintara's casts: the spark bolt's flick (ScintaraBolt) and the spark lance's thrust
(ScintaraBeamStart) and braced hold (ScintaraBeam).

The rig's bones are the R15 joints, named after the part each one moves (LowerTorso is the Root joint, UpperTorso
the Waist, LeftUpperLeg the LeftHip, and so on), with their pivots at a Studio avatar's rest pose in studs from the
HumanoidRootPart. Every bone stands upright and is turned so its axes are Roblox's: X right, Y up, Z back. The R15
joint frames are axis-aligned too, so a bone's keyed rotation is exactly the joint's Transform in game:
+X swings a hanging limb forward, -X leans the torso forward, +Y turns to the left, and Z rolls to a side.

Each clip exports as Character<Name>.fbx with a preview strip of four frames; a ride or dash is previewed on its
broom, from exports/Brooms.blend, and a Scintara cast from the wand side with a preview-only wand in hand.
CharacterAnimations.json lists every key pose as Roblox CFrames (position and quaternion) per part, with the clip's
length, looping and priority. tools/place_animations.py builds the KeyframeSequences from it in the place, as
EffectsController expects under ReplicatedStorage.Animations.
"""
import json
import math
import bpy
from mathutils import Euler, Matrix, Vector
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
# Tumble forward and back are the same tuck turning about X instead: a somersault toward -Z over the head, and a
# back roll toward +Z over the shoulders.
def tuck(turn, move, open=0.0):
    k = 1 - open
    return P(LowerTorso=(turn, move), UpperTorso=(-28 * k, 0, 0), Head=(-22 * k, 0, 0),
             LeftUpperLeg=(80 * k, 0, 0), LeftLowerLeg=(-115 * k, 0, 0), LeftFoot=(10 * k, 0, 0),
             RightUpperLeg=(80 * k, 0, 0), RightLowerLeg=(-115 * k, 0, 0), RightFoot=(10 * k, 0, 0),
             LeftUpperArm=(55 * k, 0, 20 * k), LeftLowerArm=(105 * k, 0, 0),
             RightUpperArm=(55 * k, 0, -20 * k), RightLowerArm=(105 * k, 0, 0))


FLOOR = -2.971   # the floor under the rig: a standing avatar's HumanoidRootPart is 2.971 studs up
CLEAR = 0.04     # how far the rolling body stays off it


def extent(pose, axis):
    """Pose the rig (no clip playing) and return the deformed mannequin's lowest point and its middle along
    Roblox X (axis 0) or Z (axis 2)."""
    for bone in MOVING:
        turn, move = pose.get(bone, ((0, 0, 0), (0, 0, 0)))
        pb = rig.obj.pose.bones[bone]; pb.location = move; pb.rotation_euler = [math.radians(a) for a in turn]
    bpy.context.view_layer.update()
    shown = mannequin.evaluated_get(bpy.context.evaluated_depsgraph_get()); mesh = shown.to_mesh()
    points = [shown.matrix_world @ v.co for v in mesh.vertices]; shown.to_mesh_clear()
    along = [-p.x if axis == 0 else p.y for p in points]   # Roblox X is Blender -X, Roblox Z is Blender Y
    return min(p.z for p in points), (min(along) + max(along)) / 2


def settled(turn, axis, at, open=0.0):
    """The tuck turned by `turn` degrees, its middle `at` studs along `axis` and its lowest point on the floor."""
    low, middle = extent(tuck(turn, (0, 0, 0), open), axis)
    move = [0, FLOOR + CLEAR - low, 0]; move[axis] = at - middle
    return tuck(turn, tuple(move), open)


def tumble(turn, axis, start):
    """A twelve-frame roll, `turn` degrees a frame, from `start` studs along `axis` in to the root, then a stand."""
    rise = lambda f: 0.55 * max(0, f - 9) / 3
    return [(f, settled(tuple(a * f for a in turn), axis, start - start * f / 12, rise(f))) for f in range(13)] + [(15, P())]


tumble_right = tumble((0, 0, -30), 0, -3)
tumble_forward = tumble((-30, 0, 0), 2, 3)
tumble_back = tumble((30, 0, 0), 2, -3)

# Broom ride: two seconds, looped, astride a broom whose seat is 1.35 studs under the HumanoidRootPart (BroomData's
# SeatDrop). The body leans into the flight with the head up to see ahead, both hands reach down to the grip in
# front, and the legs splay round the shaft and hang back to the stirrups behind the seat. Only the breathing moves.
def ride(lean, look, reach):
    return P(UpperTorso=(-lean, 0, 0), Head=(look, 0, 0),
             LeftUpperArm=(reach, 0, 44), LeftLowerArm=(10, 0, 0), LeftHand=(-10, 0, 0),
             RightUpperArm=(reach - 8, 0, -40), RightLowerArm=(14, 0, 0), RightHand=(-10, 0, 0),
             LeftUpperLeg=(-8, 0, -16), LeftLowerLeg=(-26, 0, 0), LeftFoot=(-20, 0, 0),
             RightUpperLeg=(-8, 0, 16), RightLowerLeg=(-26, 0, 0), RightFoot=(-20, 0, 0))
for bone in MOVING: rig.obj.pose.bones[bone].matrix_basis.identity()


# Flying each broom: a ride of its own, looped while you fly it (FlightController plays BroomRide<Broom>). The broom
# is welded to the HumanoidRootPart, so in the rig's space it never moves: brooms.py's point (x, y, z) is
# (x, y, z - SEAT_DROP) here. A ride is written as the body's motion over one loop, sampled every STEP frames; at
# each key the hands that hold on are bent onto the grip and the feet onto the stirrups (fit), so the body sways and
# rolls while the hands and feet stay where they belong on that broom.
SEAT_DROP = 1.35   # BroomData.SeatDrop
STEP = 3
REST = {b.name: b.matrix_local.copy() for b in rig.obj.data.bones}
LINK = {name: (REST[parent].inverted() if parent else Matrix.Identity(4)) @ REST[name]
        for name, (parent, *_) in JOINTS.items()}


def broom(x, y, z): return Vector((x, y, z - SEAT_DROP))


def placed(pose):
    """Every bone's posed matrix in the rig's space, as Blender poses it: the parent's, the rest offset, the key."""
    out = {}
    for name, (parent, *_) in JOINTS.items():
        turn, move = pose.get(name, ((0, 0, 0), (0, 0, 0)))
        key = Matrix.Translation(move) @ Euler([math.radians(a) for a in turn]).to_matrix().to_4x4()
        out[name] = (out[parent] if parent else Matrix.Identity(4)) @ LINK[name] @ key
    return out


def on(mats, bone, point):
    """A Roblox rest point (studs from the HumanoidRootPart) carried by `bone`, where the pose puts it."""
    return mats[bone] @ REST[bone].inverted() @ Vector(bl(*point))


def fit(pose, free, aim, give=0.0015, seed=None):
    """Bend the angles in `free`, (bone, axis, lowest, highest) in degrees, so that `aim` (posed matrices to a list
    of misses in studs) comes to nothing. Every degree an angle moves off the written pose counts as `give` studs
    of miss, so the limb bends the least it can and its elbow or knee goes the way the pose leans it. The search
    starts from `seed`'s angles when given (the key before), so a limb with two ways to reach keeps to one. Damped
    Gauss-Newton on a numerical Jacobian. Returns the pose and how far `aim` still misses."""
    import numpy as np

    def bent(x):
        out = dict(pose)
        for (b, axis, *_), v in zip(free, x):
            turn, move = out.get(b, ((0, 0, 0), (0, 0, 0)))
            turn = list(turn); turn[axis] = float(v); out[b] = (tuple(turn), move)
        return out

    lo, hi = np.array([f[2] for f in free], float), np.array([f[3] for f in free], float)
    start = np.clip([pose.get(b, ((0, 0, 0),))[0][axis] for b, axis, *_ in free], lo, hi)
    misses = lambda x: np.concatenate([np.asarray(aim(placed(bent(x))), float), give * (x - start)])
    x = np.clip([seed.get(b, ((0, 0, 0),))[0][axis] for b, axis, *_ in free], lo, hi) if seed else start
    r, damp = misses(x), 1e-3
    for _ in range(80):
        jac = np.empty((len(r), len(x)))
        for i in range(len(x)):
            dx = x.copy(); dx[i] += 0.01; jac[:, i] = (misses(dx) - r) / 0.01
        step = np.linalg.solve(jac.T @ jac + damp * np.eye(len(x)), -jac.T @ r)
        nx = np.clip(x + step, lo, hi); nr = misses(nx)
        if nr @ nr >= r @ r:
            damp *= 10
            if damp > 1e6: break
            continue
        done = np.abs(nx - x).max() < 1e-3
        x, r, damp = nx, nr, max(damp * 0.3, 1e-7)
        if done: break
    return bent(x), float(np.linalg.norm(aim(placed(bent(x)))))


def hold(pose, side, target, seed=None):
    """Bend the arm so the hand closes round `target`, a point in the rig's space or a function of the posed bones."""
    hand = JOINTS[side + 'Hand'][2]
    free = [(side + 'UpperArm', 0, -90, 200), (side + 'UpperArm', 1, -90, 90), (side + 'UpperArm', 2, -150, 150),
            (side + 'LowerArm', 0, 0, 150)]
    goal = lambda mats: target(mats) if callable(target) else target
    return fit(pose, free, lambda mats: list(on(mats, side + 'Hand', hand) - goal(mats)), seed=seed)


def plant(pose, side, target, toes, ball, seed=None):
    """Bend the leg so the sole stands on `target`, `ball` studs toward the toes from the middle of the foot, with
    the toes `toes` degrees down. The miss returned is the sole's, in studs."""
    x, _, z = JOINTS[side + 'Foot'][2]
    sole = (x, FLOOR, z - ball)
    up = Vector(bl(0, math.cos(math.radians(toes)), -math.sin(math.radians(toes))))
    free = [(side + 'UpperLeg', 0, -60, 130), (side + 'UpperLeg', 1, -50, 50), (side + 'UpperLeg', 2, -60, 60),
            (side + 'LowerLeg', 0, -150, 0), (side + 'Foot', 0, -80, 60)]
    pose, _ = fit(pose, free, lambda mats: [*(on(mats, side + 'Foot', sole) - target),
                                            *(0.6 * (mats[side + 'Foot'].to_3x3().col[1] - up))], seed=seed)
    return pose, (on(placed(pose), side + 'Foot', sole) - target).length


def wave(t, n, phase=0.0):
    """A sine that turns `n` times a loop, so it ends where it began."""
    return math.sin(2 * math.pi * (n * t + phase))


def hump(t, at, width):
    """A smooth rise and fall, 1 at `at` in the loop and 0 beyond `width` either side."""
    d = abs((t - at + 0.5) % 1 - 0.5)
    return 0.5 + 0.5 * math.cos(math.pi * d / width) if d < width else 0.0


def legs(swing, splay, knee, foot):
    """Both legs written alike: thighs swung forward and splayed round the shaft, knees bent, feet pointed."""
    return dict(LeftUpperLeg=(swing, 0, -splay), LeftLowerLeg=(-knee, 0, 0), LeftFoot=(foot, 0, 0),
                RightUpperLeg=(swing, 0, splay), RightLowerLeg=(-knee, 0, 0), RightFoot=(foot, 0, 0))


STIRRUPS = {   # broom: where the left foot stands (the right mirrors it), toes down, how far toward the toes
    'Ashwind': ((0.48, 0.69, -1.21), 8, 0.0),           # brass stirrups
    'Stoutbough': ((0.52, 0.58, -1.255), 0, 0.0),       # the plank footboard
    'Swiftquill': ((0.33, 1.04, -1.0), 35, 0.35),       # foot pegs on the fins, up on the toes
    'Nightwing': ((0.5, 0.73, -1.16), 10, 0.1),         # the branch stubs
}


def stirrups(name):
    x, y, z = STIRRUPS[name][0]
    return {'Right': broom(-x, y, z), 'Left': broom(x, y, z)}


# Ashwind, the academy's steady broom: a first-year's easy cruise. A comfortable lean, both hands on the grip with
# the right ahead of the left, knees in. The body rocks gently side to side and bobs twice a loop, and the head looks
# round, left and then right, at the view.
def ride_ashwind(t):
    look = 28 * hump(t, 0.28, 0.17) - 24 * hump(t, 0.72, 0.15)
    pose = P(LowerTorso=((-22 + 1.2 * wave(t, 2, 0.1), 0, 2 * wave(t, 1)), (0, 0.06 + 0.03 * wave(t, 2), 0)),
             UpperTorso=(-30 + 1.5 * wave(t, 2, 0.2), 2 * wave(t, 1, 0.25), -1.2 * wave(t, 1)),
             Head=(46 + 2 * wave(t, 2, 0.4), look, -wave(t, 1)),
             LeftUpperArm=(50, 0, 40), LeftLowerArm=(20, 0, 0), LeftHand=(-15, 0, 0),
             RightUpperArm=(55, 0, -40), RightLowerArm=(20, 0, 0), RightHand=(-15, 0, 0),
             **legs(20, 12, 70, -10))
    return pose, {'Right': broom(-0.15, -1.6, 0.32), 'Left': broom(0.15, -1.0, 0.32)}


# Stoutbough, the hauler: sat deep in its saddle and in no hurry. One hand drives at the back of the grip and the
# other sits on the hip, elbow out; boots flat on the footboard. The whole body rolls slowly forward and back with
# the heavy broom, the shoulders swing with it and the head nods along.
def ride_stoutbough(t):
    rock = wave(t, 1)
    pose = P(LowerTorso=((-24 - 3 * rock, 0, 1.5 * wave(t, 1, 0.25)), (0, 0.08 + 0.05 * wave(t, 1, 0.1), 0.04 * rock)),
             UpperTorso=(-30 + 2 * wave(t, 1, 0.15), 6 * wave(t, 1, 0.3), 0),
             Head=(48 + 5 * wave(t, 1, 0.35), -5 * wave(t, 1, 0.3), 0),
             LeftUpperArm=(-15, 0, -55), LeftLowerArm=(95, 0, 0), LeftHand=(0, 0, 0),
             RightUpperArm=(45, 0, -50), RightLowerArm=(15, 0, 0), RightHand=(-10, 0, 0),
             **legs(28, 30, 70, 0))
    return pose, {'Right': broom(-0.15, -1.2, 0.32), 'Left': lambda mats: on(mats, 'LowerTorso', (-1.15, -0.7, 0.05))}


# Swiftquill, the racer: a jockey's tuck. Chest down along the shaft, head up to see the line, both hands far
# forward on the bare birch with the elbows in, and the legs folded up and back onto the pegs, up on the toes. The
# wind shakes the rider in quick small tremors.
def ride_swiftquill(t):
    buffet = 0.6 * wave(t, 3) + 0.4 * wave(t, 5, 0.3)
    pose = P(LowerTorso=((-30 + 1.2 * wave(t, 2), 0, 1.2 * wave(t, 1)), (0, 0.14 + 0.015 * buffet, 0.1)),
             UpperTorso=(-40 + wave(t, 3, 0.2), 0, 0.8 * wave(t, 2, 0.1)),
             Head=(64 + 1.5 * wave(t, 3, 0.4), 0, 0),
             LeftUpperArm=(65, -45, 5), LeftLowerArm=(55, 0, 0), LeftHand=(-20, 0, 0),
             RightUpperArm=(75, 45, -5), RightLowerArm=(45, 0, 0), RightHand=(-20, 0, 0),
             **legs(45, 10, 110, -30))
    return pose, {'Right': broom(-0.06, -2.1, 0.13), 'Left': broom(0.06, -1.55, 0.13)}


# Nightwing, the wild one: ridden like a bucking beast. Both hands clamped on the grip, the body rolls hard from
# side to side and twists with it, knees clamped round the thorny shaft.
def ride_nightwing(t):
    pose = P(LowerTorso=((-20 + 3 * wave(t, 2, 0.1), 3 * wave(t, 1, 0.2), 7 * wave(t, 1)),
                         (0, 0.08 + 0.06 * wave(t, 2, 0.15), 0)),
             UpperTorso=(-34 + 4 * wave(t, 2, 0.3), 5 * wave(t, 1, 0.9), -4 * wave(t, 1, 0.05)),
             Head=(42 + 4 * wave(t, 2, 0.45), -6 * wave(t, 1, 0.2), -5 * wave(t, 1)),
             LeftUpperArm=(50, 0, 45), LeftLowerArm=(15, 0, 0), LeftHand=(-10, 0, 0),
             RightUpperArm=(50, 0, -45), RightLowerArm=(15, 0, 0), RightHand=(-10, 0, 0),
             **legs(15, 10, 65, -10))
    return pose, {'Right': broom(-0.18, -1.4, 0.36), 'Left': broom(0.18, -0.85, 0.36)}


RIDES = {   # broom: (ride, frames a loop)
    'Ashwind': (ride_ashwind, 72),
    'Stoutbough': (ride_stoutbough, 96),
    'Swiftquill': (ride_swiftquill, 36),
    'Nightwing': (ride_nightwing, 48),
}


# Dashing through the air: flown flat out, a rider tucks low into the wind in their house's own way, and
# FlightController plays BroomDash<House><Broom> instead of the ride. Each house's dash is the body's motion over a
# short loop, with the wind's buffeting on top; it is fitted to every broom's grip and stirrups as the rides are,
# so there are sixteen dashes. They are keyed every DASH_STEP frames, fine enough for the quick shakes.
DASH_STEP = 2
DASH_SEAT = {   # broom: (how far up the rider sits off the seat, where the right and left hands hold on)
    'Ashwind': (0.04, broom(-0.15, -1.75, 0.32), broom(0.15, -1.15, 0.32)),
    'Stoutbough': (0.06, broom(-0.15, -1.6, 0.34), broom(0.15, -1.05, 0.34)),
    'Swiftquill': (0.14, broom(-0.06, -2.0, 0.13), broom(0.06, -1.45, 0.13)),
    'Nightwing': (0.05, broom(-0.18, -1.55, 0.36), broom(0.18, -1.0, 0.36)),
}


def gust(t, n, phase=0.0):
    """The wind buffeting a rider: two quick shakes, `n` times a loop, laid over each other. Between -1 and 1."""
    return 0.6 * wave(t, n[0], phase) + 0.4 * wave(t, n[1], phase + 0.37)


# Emberclaw (courage): the charge. Head down like a ram and elbows flared wide, the rider drives forward twice a
# second as if spurring the broom on, and the wind hammers back at the shoulders.
def dash_emberclaw(t):
    surge, shake = wave(t, 2), gust(t, (3, 5))
    return P(LowerTorso=((-31 - 3 * surge, 0, 1.2 * shake), (0, 0.015 * shake, -0.04 - 0.04 * surge)),
             UpperTorso=(-41 - 4 * surge + 1.5 * shake, 0, 1.5 * gust(t, (3, 5), 0.3)),
             Head=(58 + 3 * surge - shake, 0, -shake),
             LeftUpperArm=(35, 0, 15), LeftLowerArm=(80, 0, 0), LeftHand=(-15, 0, 0),
             RightUpperArm=(35, 0, -15), RightLowerArm=(80, 0, 0), RightHand=(-15, 0, 0),
             **legs(25, 18, 80, -10))


# Stoneroot (loyalty): the brace. Low, square and still, elbows locked in and knees clamped, eyes level ahead. The
# rider gives nothing to the wind but a slow heave and a fine shudder running through the shoulders.
def dash_stoneroot(t):
    shudder = gust(t, (4, 6))
    return P(LowerTorso=((-30 + wave(t, 1), 0, 0.6 * shudder), (0, 0.01 * shudder, 0)),
             UpperTorso=(-36 + 0.8 * shudder, 0, 0.8 * gust(t, (4, 6), 0.5)),
             Head=(64 - 0.6 * shudder, 0, -0.6 * shudder),
             LeftUpperArm=(60, -15, 20), LeftLowerArm=(60, 0, 0), LeftHand=(-15, 0, 0),
             RightUpperArm=(60, 15, -20), RightLowerArm=(60, 0, 0), RightHand=(-15, 0, 0),
             **legs(20, 6, 80, -10))


# Skyquill (wisdom): the glide. Flat and streamlined like a diving hawk, elbows out like wings, the rider carves a
# long slow curve to one side and back to the other, keeping the head level as the body banks.
def dash_skyquill(t):
    carve, shake = wave(t, 1), gust(t, (6, 8))
    return P(LowerTorso=((-32 + 0.8 * wave(t, 2, 0.2), 3 * wave(t, 1, 0.25), 7 * carve), (0, 0.01 * shake, 0)),
             UpperTorso=(-38 + 1.5 * wave(t, 2, 0.3) + 0.6 * shake, 3 * wave(t, 1, 0.25), 4 * carve),
             Head=(66, -4 * wave(t, 1, 0.25), -10 * carve - 0.6 * shake),
             LeftUpperArm=(40, 0, -10), LeftLowerArm=(75, 0, 0), LeftHand=(-15, 0, 0),
             RightUpperArm=(40, 0, 10), RightLowerArm=(75, 0, 0), RightHand=(-15, 0, 0),
             **legs(12, 8, 75, -20))


# Nightfang (ambition): the prowl. Low and coiled, the rider weaves like a serpent: the hips sway one way while the
# shoulders twist the other, and the head stays locked on what lies ahead.
def dash_nightfang(t):
    weave, shake = wave(t, 1), gust(t, (4, 6))
    return P(LowerTorso=((-30 + 0.8 * shake, 6 * weave, -3 * weave), (0.08 * weave, 0.01 * shake, 0)),
             UpperTorso=(-36 + 1.5 * wave(t, 2, 0.15), -11 * weave, 5 * weave + 0.8 * shake),
             Head=(62, 5 * weave, -2 * weave - 0.6 * shake),
             LeftUpperArm=(60, -10, 25), LeftLowerArm=(55, 0, 0), LeftHand=(-15, 0, 0),
             RightUpperArm=(60, 10, -25), RightLowerArm=(55, 0, 0), RightHand=(-15, 0, 0),
             **legs(18, 8, 80, -10))


DASHES = {   # house (Config.Houses): (dash, frames a loop)
    'Emberclaw': (dash_emberclaw, 30),
    'Stoneroot': (dash_stoneroot, 36),
    'Skyquill': (dash_skyquill, 48),
    'Nightfang': (dash_nightfang, 36),
}


def fitted(clip, broom_name, sample, frames, step):
    """Key `sample(t)`, a pose and where its hands hold on, every `step` frames over a loop, with the hands bent onto
    their holds and the feet onto the broom's stirrups. Each key's limbs start from the key before, and the loop is
    gone round twice so its first key starts from its last: a limb that could reach two ways keeps to one all the
    way round. Checks that every hand and foot reaches."""
    _, toes, ball = STIRRUPS[broom_name]
    before = None
    for lap in range(2):
        keys, worst = [], {'hands': 0.0, 'feet': 0.0}
        for frame in range(0, frames + 1, step):
            pose, hands = sample(frame / frames)
            for side, target in stirrups(broom_name).items():
                pose, miss = plant(pose, side, target, toes, ball, before); worst['feet'] = max(worst['feet'], miss)
            for side, target in hands.items():
                pose, miss = hold(pose, side, target, before); worst['hands'] = max(worst['hands'], miss)
            keys.append((frame, pose)); before = pose
    keys[-1] = (frames, keys[0][1])   # the same moment of the loop, so it joins exactly
    rbx.say(f'{clip}: hands within {worst["hands"]:.3f} studs of their holds, feet within {worst["feet"]:.3f} '
            'of the stirrups')
    assert max(worst.values()) < 0.1, f'{clip}: a hand or foot cannot reach the broom'
    return keys


def dash_sample(house, broom_name):
    """A house's dash on one broom: the rider lifted to its seat, hands on its grip."""
    lift, right, left = DASH_SEAT[broom_name]

    def sample(t):
        pose = DASHES[house][0](t)
        turn, move = pose['LowerTorso']
        pose['LowerTorso'] = (turn, (move[0], move[1] + lift, move[2]))
        return pose, {'Right': right, 'Left': left}
    return sample


# Scintara, the spark spell every wand knows (SpellService, EffectsController). Only the upper body is keyed, so the
# legs keep walking under a cast. The wand is welded 0.2 studs down from the right hand's middle and points along the
# hand's front (WandService, WandModel), so a hanging arm holds it level and a raised one points it up. Where a cast
# aims the wand, the wrist is solved to point it straight ahead whatever the arm and body do (aimed).
FORWARD = Vector((0, -1, 0))   # Roblox's forward, -Z, in the rig's space


def aimed(pose, seed=None):
    """Bend and roll the right wrist so the wand points straight ahead and level."""
    free = [('RightHand', 0, -130, 60), ('RightHand', 2, -70, 70)]
    pose, miss = fit(pose, free, lambda mats: list(mats['RightHand'].to_3x3() @ Vector((0, 0, -1)) - FORWARD), seed=seed)
    assert miss < 0.02, f'the wand points {math.degrees(miss):.1f} degrees off ahead'
    return pose


def nudged(pose, bone, turn):
    """The pose with `turn` degrees added to `bone`."""
    old, move = pose.get(bone, ((0, 0, 0), (0, 0, 0)))
    return {**pose, bone: (tuple(a + b for a, b in zip(old, turn)), move)}


# ScintaraBolt, a left click: 0.4 s. From ready, the shoulders turn right and the wand is cocked back over the
# shoulder, then flicked out level at frame 4 (0.13 s; the server lets the bolt go after Scintara's 0.12 s CastTime)
# as the body turns into it. The wrist dips through, and the arm settles.
CAST_READY = P(RightUpperArm=(30, 0, 0), RightLowerArm=(30, 0, 0), RightHand=(-50, 0, 0),
               LeftUpperArm=(10, 0, 0), LeftLowerArm=(15, 0, 0))
bolt_cock = P(UpperTorso=(8, -18, 0), Head=(-4, 16, 0),
              RightUpperArm=(150, 0, -12), RightLowerArm=(35, 0, 0), RightHand=(-65, 0, 0),
              LeftUpperArm=(40, 0, 10), LeftLowerArm=(30, 0, 0))
bolt_flick = aimed(P(UpperTorso=(-8, 10, 0), Head=(6, -10, 0), RightUpperArm=(92, 8, 0), RightHand=(-80, 0, 0),
                     LeftUpperArm=(-20, 0, 8), LeftLowerArm=(25, 0, 0)))
bolt_through = nudged(aimed(P(UpperTorso=(-5, 6, 0), Head=(4, -6, 0), RightUpperArm=(75, 4, 0),
                              RightLowerArm=(12, 0, 0), RightHand=(-85, 0, 0),
                              LeftUpperArm=(-8, 0, 6), LeftLowerArm=(20, 0, 0))), 'RightHand', (-18, 0, 0))
bolt_settle = P(RightUpperArm=(20, 0, 0), RightLowerArm=(20, 0, 0), RightHand=(-30, 0, 0))
scintara_bolt = [(0, CAST_READY), (2, bolt_cock), (4, bolt_flick), (8, bolt_through), (12, bolt_settle)]

# ScintaraBeamStart, a right click held: 0.2 s. The wand is drawn in to the chest with the left hand coming up to
# it, then thrust out at the aim with both arms, braced like a heavy crossbow: the shoulders turn a little right, the
# wand arm reaches in across them so the wand stands in front of the chest, and the left hand closes under the wand
# wrist. The body leans back against the pour.
# ScintaraBeam: 0.6 s, looped while the button is held. The braced pose shakes: a quick tremor runs through the wand
# arm and wrist, and a slow heave pushes the shoulders back. Every frame is a key, joined by straight lines, with the
# wand aimed ahead and the left hand fitted under the wrist each time.
BRACE = (1.31, -0.32, 0.5)   # under the wand wrist: the forearm's rest-pose back is its underside when held level


def lance(t):
    heave = 0.5 + 0.5 * wave(t, 1)
    return P(UpperTorso=(6 + 3 * heave, -24, 0), Head=(-6 - 2 * heave, 24, 0),
             RightUpperArm=(84 - 3 * heave + 1.5 * wave(t, 6), 42 + 0.8 * wave(t, 5, 0.3), 0),
             RightLowerArm=(15, 0, 0), RightHand=(-85, 0, 20),
             LeftUpperArm=(75, -35, 0), LeftLowerArm=(30, 0, 0), LeftHand=(-20, 0, 0))


def braced(t, seed=None):
    """The lance's pose at `t` through the loop, aimed, with the wrist's tremor on top and the left hand under it."""
    pose = nudged(aimed(lance(t), seed), 'RightHand', (1.2 * wave(t, 4, 0.25), 0, 0))
    pose, miss = hold(pose, 'Left', lambda mats: on(mats, 'RightLowerArm', BRACE), seed)
    assert miss < 0.25, f'the left hand misses the wand wrist by {miss:.2f} studs'   # less than half a hand
    return pose, miss


LANCE = 18
lance_keys, before, worst = [], None, 0.0
for frame in range(LANCE):
    before, miss = braced(frame / LANCE, before); lance_keys.append((frame, before)); worst = max(worst, miss)
lance_keys.append((LANCE, lance_keys[0][1]))   # the same moment of the loop, so it joins exactly
rbx.say(f'ScintaraBeam: the left hand within {worst:.3f} studs of the wand wrist')
lance_draw = P(UpperTorso=(4, -10, 0), Head=(-2, 10, 0),
               RightUpperArm=(55, 15, 0), RightLowerArm=(70, 0, 0), RightHand=(-60, 0, 0),
               LeftUpperArm=(45, 0, 25), LeftLowerArm=(70, 0, 0))
scintara_beam_start = [(0, CAST_READY), (3, lance_draw), (6, lance_keys[0][1])]

# A wand for the Scintara previews only, in the hand as WandService welds it; it is never exported. The leading
# underscore keeps world/world.py from bringing it into the world scene.
GRIP = (1.383, -1.141, 0.002)
stick = rbx.Mesh('_Wand')
stick.tube([bl(GRIP[0], GRIP[1], 0.45), bl(GRIP[0], GRIP[1], -2.2)], [0.08, 0.055], (122, 86, 54), bone='RightHand')
stick.sphere(0.13, bl(GRIP[0], GRIP[1], -2.25), (199, 180, 255), segments=10, bone='RightHand')
wand = stick.finish(sharp=40, rig=rig)
for bone in MOVING: rig.obj.pose.bones[bone].matrix_basis.identity()


CLIPS = {   # name: (keys, last frame, loops, priority, easing per part)
    'Walk': ([(0, walk_contact), (8, walk_passing), (15, mirror(walk_contact)), (23, mirror(walk_passing)),
              (30, walk_contact)], 30, True, 'Movement', {}),
    'Sprint': ([(0, sprint_contact), (5, sprint_flight), (9, mirror(sprint_contact)), (14, mirror(sprint_flight)),
                (18, sprint_contact)], 18, True, 'Movement', {}),
    'TumbleRight': (tumble_right, 15, False, 'Action', {'LowerTorso': 'Linear'}),
    'TumbleLeft': ([(f, mirror(p)) for f, p in tumble_right], 15, False, 'Action', {'LowerTorso': 'Linear'}),
    'TumbleForward': (tumble_forward, 15, False, 'Action', {'LowerTorso': 'Linear'}),
    'TumbleBack': (tumble_back, 15, False, 'Action', {'LowerTorso': 'Linear'}),
    'BroomRide': ([(0, ride(40, 30, 60)), (30, ride(36, 27, 57)), (60, ride(40, 30, 60))], 60, True, 'Action', {}),
    'ScintaraBolt': (scintara_bolt, 12, False, 'Action2', {}),
    'ScintaraBeamStart': (scintara_beam_start, 6, False, 'Action2', {}),
    'ScintaraBeam': (lance_keys, LANCE, True, 'Action2', {bone: 'Linear' for bone in MOVING}),
}
# Rides and dashes are keyed every few frames, so straight lines between keys keep the motion even.
ON_BROOM = {}   # clip: (broom, frames a loop)
for name, (ride, frames) in RIDES.items():
    ON_BROOM['BroomRide' + name] = (name, frames)
    CLIPS['BroomRide' + name] = (fitted('BroomRide' + name, name, ride, frames, STEP), frames, True, 'Action',
                                 {bone: 'Linear' for bone in MOVING})
for house, (_, frames) in DASHES.items():
    for name in RIDES:
        clip = f'BroomDash{house}{name}'
        ON_BROOM[clip] = (name, frames)
        CLIPS[clip] = (fitted(clip, name, dash_sample(house, name), frames, DASH_STEP), frames, True, 'Action',
                       {bone: 'Linear' for bone in MOVING})
PREVIEW_FRAMES = {'Walk': [0, 8, 15, 23], 'Sprint': [0, 5, 9, 14], 'BroomRide': [0, 15, 30, 45]}
PREVIEW_FRAMES.update({name: [0, 4, 8, 12] for name in CLIPS if name.startswith('Tumble')})
PREVIEW_FRAMES.update({clip: [frames * k // 4 for k in range(4)] for clip, (_, frames) in ON_BROOM.items()})
PREVIEW_FRAMES.update({'ScintaraBolt': [0, 2, 4, 8], 'ScintaraBeamStart': [0, 2, 4, 6], 'ScintaraBeam': [0, 4, 9, 13]})

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
    # A Scintara cast is previewed from the wand side with the preview wand in hand.
    scintara = name.startswith('Scintara')
    wand.hide_render = not scintara
    rbx.export('Character' + name, [mannequin, rig.obj], animation=True, preview_frames=PREVIEW_FRAMES[name],
               auto_preview=name not in ON_BROOM and not scintara)
    if scintara and rbx.PREVIEW:
        rbx.strip('Character' + name, PREVIEW_FRAMES[name], bl(11, 0.4, -2.2), bl(0, 0.2, -1.6))
wand.hide_render = True


def preview_rides():
    """Render each ride and dash with the mannequin on its broom, from exports/Brooms.blend. Every file is written
    by now, so the brooms never reach Character.blend."""
    path = rbx.EXPORTS / 'Brooms.blend'
    if not path.exists(): return rbx.say('Ride previews skipped: build blender/models/brooms.py first')
    with bpy.data.libraries.load(str(path)) as (source, target):
        target.objects = [n for n in source.objects if not n.startswith('_')]
    models = {o.name: o for o in target.objects if o and o.name in RIDES}
    for o in target.objects:
        if o: sc.collection.objects.link(o)
    # brooms.py lays them out SPACING studs apart along X, Ashwind at the origin; stand each one's seat under the rig.
    spacing = 3.2
    for k, name in enumerate(('Ashwind', 'Swiftquill', 'Stoutbough', 'Nightwing')):
        models[name].parent.location = (0, 0, -SEAT_DROP)
        models[name].location = (-spacing * k, 0, 0)
    for clip, (name, frames) in ON_BROOM.items():
        for other, model in models.items():
            for o in model.children: o.hide_render = other != name
        action = bpy.data.actions['Character' + clip]
        rig.obj.animation_data.action = action
        if getattr(action, 'slots', None): rig.obj.animation_data.action_slot = action.slots[0]
        sc.frame_start, sc.frame_end = 0, frames
        rbx.preview('Character' + clip, [mannequin, *models[name].children], PREVIEW_FRAMES[clip])


if rbx.PREVIEW: preview_rides()
rbx.viewport((0, 0, -0.5), 12, turn=(80, 0, 35))
out = rbx.EXPORTS / 'CharacterAnimations.json'
out.write_text(json.dumps(data, separators=(',', ':')), encoding='utf-8')
summary = ', '.join('%s (%d keys)' % (n, len(d['keys'])) for n, d in data.items())
rbx.say(f'exports/{out.name}: {summary}')
