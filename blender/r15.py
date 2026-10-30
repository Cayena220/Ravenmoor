"""The R15 avatar rig for character animation scripts, and the tools for posing it.

The rig's bones are the R15 joints, named after the part each one moves (LowerTorso is the Root joint, UpperTorso
the Waist, LeftUpperLeg the LeftHip, and so on), with their pivots at a Studio avatar's rest pose in studs from the
HumanoidRootPart. Every bone stands upright and is turned so its axes are Roblox's: X right, Y up, Z back. The R15
joint frames are axis-aligned too, so a bone's keyed rotation is exactly the joint's Transform in game:
+X swings a hanging limb forward, -X leans the torso forward, +Y turns to the left, and Z rolls to a side.

animations/casting.py builds on this module. animations/character.py still has its own copy of the same rig.
"""
import math
import bpy
from mathutils import Euler, Matrix, Vector
import rbx

SKIN = (212, 169, 126); ROBE = (76, 101, 120); TROUSERS = (58, 52, 48); BOOTS = (74, 54, 40)
FLOOR = -2.971   # the floor under the rig: a standing avatar's HumanoidRootPart is 2.971 studs up


def bl(x, y, z):
    """A Roblox position or direction (X right, Y up, Z back) in Blender (Z up, front -Y): Blender -X is Roblox +X."""
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
REST, LINK = {}, {}   # set by build(): each bone's rest matrix, and its rest matrix from its parent's


def build(name, frames):
    """Clear the scene and make the rig, CharacterRig. `frames` is the scene's first and last frame."""
    rbx.scene(name, frames=frames)
    rig = rbx.Rig('CharacterRig', [(bone, parent, bl(*pivot), [a + b for a, b in zip(bl(*pivot), (0, 0, 0.4))])
                                   for bone, (parent, pivot, *_) in JOINTS.items()])
    # Turn every upright bone half a turn about itself, so its X axis is Roblox's +X (Blender -X) and its Z axis
    # Roblox's +Z (Blender +Y). Then a bone's local rotation reads in Roblox's axes.
    bpy.context.view_layer.objects.active = rig.obj
    bpy.ops.object.mode_set(mode='EDIT')
    for bone in rig.obj.data.edit_bones: bone.roll = math.pi
    bpy.ops.object.mode_set(mode='OBJECT')
    for bone in rig.obj.data.bones:
        axes = bone.matrix_local.to_3x3()
        assert all(abs(axes[i][j] - want) < 1e-5 for (i, j), want in
                   {(0, 0): -1, (2, 1): 1, (1, 2): 1}.items()), f'{bone.name} is not aligned to Roblox axes'
    REST.update({b.name: b.matrix_local.copy() for b in rig.obj.data.bones})
    LINK.update({bone: (REST[parent].inverted() if parent else Matrix.Identity(4)) @ REST[bone]
                 for bone, (parent, *_) in JOINTS.items()})
    return rig


def mannequin(rig, name, parts):
    """A mesh of the mannequin's `parts`, each moved by its own bone: boxes, a ball for the head with a visor so
    the face reads in previews."""
    body = rbx.Mesh(name)
    for part in parts:
        _, _, centre, size, colour = JOINTS[part]
        if part == 'Head':
            body.sphere(0.6, bl(*centre), colour, segments=16, bone=part)
            body.box((0.7, 0.12, 0.18), bl(0, 1.55, -0.57), TROUSERS, bone=part)
        else: body.box((size[0], size[2], size[1]), bl(*centre), colour, bone=part)
    return body.finish(sharp=40, rig=rig)


def P(**bones):
    """A pose: each bone given as (rx, ry, rz) degrees, or ((rx, ry, rz), (x, y, z)) with a move in studs."""
    return {name: (v if len(v) == 2 and isinstance(v[0], tuple) else (v, (0, 0, 0))) for name, v in bones.items()}


def mirror(pose):
    """The same pose on the other side: Left and Right swap, turns about Y and Z reverse, X moves reverse."""
    out = {}
    for name, (turn, move) in pose.items():
        swapped = name.replace('Left', '#').replace('Right', 'Left').replace('#', 'Right')
        out[swapped] = ((turn[0], -turn[1], -turn[2]), (-move[0], move[1], move[2]))
    return out


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


def toward(mats, bone, direction):
    """A Roblox rest direction carried by `bone`, the way the pose turns it."""
    return mats[bone].to_3x3() @ REST[bone].to_3x3().inverted() @ Vector(bl(*direction))


def fit(pose, free, aim, give=0.0015):
    """Bend the angles in `free`, (bone, axis, lowest, highest) in degrees, so that `aim` (posed matrices to a list
    of misses in studs) comes to nothing. Every degree an angle moves off the written pose counts as `give` studs
    of miss, so the limb bends the least it can and its elbow or knee goes the way the pose leans it. Damped
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
    x, r, damp = start, misses(start), 1e-3
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


def bake(rig, name, keys, last):
    """Key a clip on the rig as the action `name`, and read each key pose back as the joint Transforms Roblox will
    apply: per bone, a position and a quaternion in the bone's own (Roblox) axes, at each key's time in seconds.
    Only bones some key moves are listed. Leaves the action on the rig, for export."""
    sc = bpy.context.scene
    action = bpy.data.actions.new(name); action.use_fake_user = True
    if not rig.obj.animation_data: rig.obj.animation_data_create()
    rig.obj.animation_data.action = action
    sc.frame_start, sc.frame_end = 0, last
    for frame, pose in keys:
        for bone in MOVING:
            turn, move = pose.get(bone, ((0, 0, 0), (0, 0, 0)))
            rig.key(frame, bone, move=move, turn=turn)
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
    return poses
