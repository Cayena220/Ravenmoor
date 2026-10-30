"""Wand gestures for casting spells, for R15 avatars (r15.py's rig): a clip per gesture, Cast<Motion>, which
EffectsController plays when the server accepts a cast. SpellData gives each spell its Motion.

A gesture is written as where the hands go. At each key: the middle of the wand hand and the way the wand points,
and the middle of the off hand with the way its palm faces and its fingers point. Each arm is bent onto its marks
(arm(): a small least-squares solve over the shoulder, elbow, forearm twist and wrist), so the wand truly points
where the key says. The wand is held as WandService welds it: 0.2 studs down the right hand and pointing along the
hand's front (-Z), here 2.1 studs long like an ash wand. A hanging arm holds it level and an outstretched one
points it up, so a strike bends the wrist down to aim it, as Scintara's casts do (character.py). R15 hands have no
fingers, so the hands gesture from the wrist. Spark Bolt is not here: Scintara's casts are character.py's.

Every gesture is timed to the server. It starts when the cast is accepted, and the server fires the spell
CastTime later (SpellData: 0.2 s), so the wand strikes then. That key carries a Release
marker, where EffectsController flashes the wand tip. A gesture keys the arms, upper torso and head only, at
priority Action2, so the legs go on walking, sprinting or riding under it; the head turns against the torso to
keep looking ahead.

Each clip exports as Cast<Motion>.fbx. With --preview, three strips of four frames: Cast<Motion>.png from the front
right, Cast<Motion>_third.png from the game's over-the-shoulder camera, and Cast<Motion>_first.png from the
first-person camera, which draws only the forearms, hands and wand and lifts the arms into view, as the game does.
CastAnimations.json lists every key pose as Roblox CFrames, like CharacterAnimations.json, with the Release marker;
tools/place_animations.py builds the KeyframeSequences from it in the place.
"""
import json
import math
import bpy
from mathutils import Matrix, Vector
import rbx
import r15
from r15 import P, bl

rig = r15.build('Casting', frames=(0, 30))
# The forearms and hands are a mesh of their own, so the first-person shots can draw them alone, as in game.
ARMS = [side + part for side in ('Left', 'Right') for part in ('LowerArm', 'Hand')]
body = r15.mannequin(rig, 'Mannequin', [part for part in r15.MOVING if part not in ARMS])
arms = r15.mannequin(rig, 'Arms', ARMS)

WAND = 2.1   # an ash wand's length (WandData), the commonest
HAND = {side: r15.JOINTS[side + 'Hand'][2] for side in ('Left', 'Right')}
WAND_AXIS = (0, 0, -1)   # the way the wand points from the hand, at rest


def along(d):
    """The point `d` studs along the wand from its grip toward the tip, at rest. The handle runs from -0.45, the
    pommel's end, to 0.35."""
    x, y, z = HAND['Right']
    return x + d * WAND_AXIS[0], y - 0.2 + d * WAND_AXIS[1], z + d * WAND_AXIS[2]


# Not exported: a stand-in for the wand in the previews, built like WandModel's: handle, pommel, shaft and tip.
wand = rbx.Mesh('_Wand')
wand.tube([bl(*along(-0.45)), bl(*along(0.35))], 0.12, (143, 122, 92), bone='RightHand')
wand.sphere(0.13, bl(*along(-0.5)), (176, 141, 87), bone='RightHand')
wand.tube([bl(*along(0.35)), bl(*along(WAND))], [0.075, 0.06], (198, 170, 128), bone='RightHand')
wand.sphere(0.09, bl(*along(WAND)), (194, 163, 255), bone='RightHand')
wand = wand.finish(rig=rig)

BACK = (1, 0, 0)                                   # at rest the back of the right hand faces out
PALM = (1, 0, 0)                                   # and the left palm faces in, its fingers pointing down
FINGERS = (0, -1, 0)
F, U, D = (0, 0, -1), (0, 1, 0), (0, -1, 0)        # forward, up and down
# A palm pushed out at the aim. A wrist bends back only so far, so it faces forward and a little down, its fingers
# angled up.
PUSH = ((0, -0.45, -0.9), (0, 0.9, -0.45))
# A strike: the wand hand out beside the right shoulder, where it shows past the body from the over-the-shoulder
# camera, with the wand turned a little in toward the line the spell flies.
AIM = (-0.12, 0, -1)


# How much each mark counts, per stud of miss at the hand or per unit of an axis turned away. Where a mark cannot
# all be met, the wand's aim wins: a hand a fraction of a stud off its mark doesn't show, a wand off its aim does.
# The palm counts more than which way the fingers point.
def W(at, way, back=None):
    """The wand hand: its middle at `at`, the wand pointing `way`, and if given the back of the hand facing `back`."""
    return at, [(WAND_AXIS, way, 1.5)] + ([(BACK, back, 0.7)] if back else [])


def O(at, palm, fingers):
    """The off hand: its middle at `at`, the palm facing `palm` and the fingers pointing `fingers`."""
    return at, [(PALM, palm, 0.7), (FINGERS, fingers, 0.35)]


READY = W((1.15, -0.55, -0.45), (0, 0.08, -1))           # the wand low before the hip, close to the rest pose
LOW = O((-1.3, -0.8, -0.1), (1, 0, 0), (0, -1, 0))       # the off hand back at the side


def arm(pose, side, mark):
    """Bend `side`'s arm onto `mark`: where the middle of the hand goes, and the hand axes that must point a given
    way, as (axis at rest, way, weight); all in Roblox axes, studs from the HumanoidRootPart. Returns the pose, how
    far the hand misses in studs, and how far the first axis (the wand's, or the palm's) misses in degrees."""
    at, axes = mark
    free = [(side + 'UpperArm', 0, -90, 200), (side + 'UpperArm', 1, -90, 90), (side + 'UpperArm', 2, -150, 150),
            (side + 'LowerArm', 0, 0, 150), (side + 'LowerArm', 1, -100, 100),  # the elbow, and the forearm's twist
            # The wrist: tipped, which the wand hand needs a long way to aim from an outstretched arm, and bent.
            (side + 'Hand', 0, *((-130, 60) if side == 'Right' else (-70, 70))), (side + 'Hand', 2, -80, 80)]
    goal = Vector(bl(*at)); wants = [(rest, Vector(bl(*way)).normalized(), weight) for rest, way, weight in axes]

    def aim(mats):
        miss = list(r15.on(mats, side + 'Hand', HAND[side]) - goal)
        for rest, want, weight in wants: miss += list(weight * (r15.toward(mats, side + 'Hand', rest) - want))
        return miss

    def angles(p): return [p.get(b, ((0, 0, 0),))[0][axis] for b, axis, *_ in free]

    # Start from the key before, and from arms raised in turn forward, high and overhead, the elbow straight or
    # bent and the forearm turned either way: a far mark can trap a single start. Of the poses that land on the
    # mark, keep the one that moves least from the key before, so the arm never flips between keys.
    sign = 1 if side == 'Right' else -1
    starts = [dict(pose)] if side + 'UpperArm' in pose else []
    starts += [{**pose, **P(**{side + 'UpperArm': (ux, 0, sign * 15), side + 'LowerArm': (lx, ly, 0),
                               side + 'Hand': (0, 0, 0)})}
               for ux in (30, 90, 150) for lx in (20, 90) for ly in (-60, 0, 60)]
    before = angles(pose) if starts and side + 'UpperArm' in pose else None
    best = None
    for start in starts:
        # A loose pull back to the start: these arms swing a long way, and must still land on their marks.
        bent, _ = r15.fit(start, free, aim, give=0.0003)
        mats = r15.placed(bent)
        off = (r15.on(mats, side + 'Hand', HAND[side]) - goal).length
        rest, want, _ = wants[0]; turned = math.degrees(r15.toward(mats, side + 'Hand', rest).angle(want))
        moved = sum(abs(a - b) for a, b in zip(angles(bent), before)) if before else 0
        score = off + 0.005 * turned + 0.0004 * moved
        if best is None or score < best[0]: best = (score, bent, off, turned)
    return best[1], best[2], best[3]


def posed(name, keys):
    """Pose each key: lean, turn and bend the upper torso (the head turns back against it), then bend each arm onto
    its marks. An arm a key leaves out holds as the key before left it, and an arm no key gives is not keyed, so the
    walk or ride beneath swings it. Checks that every hand reaches its mark."""
    out, last, misses = [], {}, []
    for frame, (lean, twist, bend), right, left in keys:
        pose = dict(last)
        pose['UpperTorso'] = ((-lean, twist, bend), (0, 0, 0))
        pose['Head'] = ((0.8 * lean, -0.8 * twist, -0.8 * bend), (0, 0, 0))
        for side, mark in (('Right', right), ('Left', left)):
            if not mark: continue
            pose, off, turned = arm(pose, side, mark)
            misses.append((off, turned, f'{side.lower()} hand at frame {frame}'))
        out.append((frame, pose)); last = pose
    off, turned = max(m[0] for m in misses), max(m[1] for m in misses)
    rbx.say(f'Cast{name}: hands within {off:.2f} studs of their marks, wand and palms within {turned:.0f} degrees')
    # The wand's aim wins over where its hand goes (W), so a strike's hand can sit a fraction of a stud off.
    bad = [f'{where} misses by {o:.2f} studs and {t:.0f} degrees' for o, t, where in misses if o >= 0.6 or t >= 40]
    assert not bad, f'Cast{name}: a hand cannot reach its mark: ' + '; '.join(bad)
    return out


def circle(centre, radius, frames, start, lean, spin=1):
    """Keys every frame from `start` to `start` + `frames`: the wand hand circling `centre` once, `radius` studs out,
    with the wand up and leaning out from the middle, so its tip draws a wider ring."""
    keys = []
    for f in range(frames + 1):
        a = spin * 2 * math.pi * f / frames
        c, s = math.cos(a), math.sin(a)
        hand = (centre[0] + radius * c, centre[1], centre[2] + radius * s)
        keys.append((start + f, lean, W(hand, (0.45 * c, 1, 0.45 * s)), None))
    return keys


Z = (0, 0, 0)   # the torso upright
GESTURES = {   # motion: (keys as (frame, torso (lean forward, turn left, bend), wand hand, off hand), release frame)
    # Flame Lash: a whip. The wand is drawn back high over the shoulder while the off hand points the way, then
    # lashes down and across the body to the far hip, the shoulders turning through and the off hand swept back.
    'Lash': ([(0, (-4, -24, 4), W((1.25, 1.55, 0.3), (0.3, 0.55, 1)), O((-0.85, 0.55, -1.25), *PUSH)),
              (3, (0, -8, 2), W((1.05, 1.5, -0.55), (0.1, 1, -0.4)), O((-1.0, 0.3, -0.9), *PUSH)),
              (6, (8, 16, -3), W((0.65, 0.65, -1.45), (-0.3, -0.15, -1)), O((-1.3, -0.3, 0.3), (1, 0, 0), D)),
              (10, (10, 24, -4), W((-0.2, -0.15, -1.1), (-0.6, -0.55, -0.6)), O((-1.35, -0.45, 0.45), (1, 0, 0), D)),
              (21, Z, READY, LOW)], 6),
    # Frost Shard and Disarm: a fencer's lunge. The wand is chambered at the ribs with the off hand out as a guide,
    # then stabbed straight at the aim at full stretch while the off hand sweeps back to the hip.
    'Thrust': ([(0, (-2, -18, 0), W((1.2, 0.45, 0.15), (0, 0.1, -1)), O((-0.55, 0.55, -1.15), *PUSH)),
                (3, (2, -6, 0), W((1.05, 0.5, -0.5), F), O((-0.75, 0.35, -0.95), *PUSH)),
                (6, (8, 14, 0), W((0.95, 0.72, -1.5), AIM), O((-1.3, -0.35, 0.35), (1, 0, 0), D)),
                (10, (8, 14, 0), W((0.95, 0.7, -1.48), (-0.12, -0.04, -1)), O((-1.3, -0.35, 0.35), (1, 0, 0), D)),
                (18, Z, READY, LOW)], 6),
    # Blast Hex: both hands. The wand stands over the cupped off hand as if holding an orb at the chest, draws it
    # in, then both hands hurl it out at the aim, palm and wand forward.
    'Hurl': ([(0, (-4, 0, 0), W((0.45, 0.55, -0.75), (-0.1, 0.9, -0.4)), O((-0.45, 0.05, -0.8), U, (0.3, 0, -1))),
              (3, (-8, 0, 0), W((0.5, 0.6, -0.5), (0, 1, -0.1)), O((-0.5, 0.1, -0.5), U, (0.3, 0, -1))),
              (6, (10, 0, 0), W((0.75, 0.75, -1.5), (-0.1, 0, -1)), O((-0.6, 0.7, -1.45), *PUSH)),
              (11, (10, 0, 0), W((0.77, 0.73, -1.47), (-0.1, -0.03, -1)), O((-0.62, 0.68, -1.42), *PUSH)),
              (24, Z, READY, LOW)], 6),
    # Chain Lightning: the wand raised high, then struck down at the aim and held there, the off hand bracing the
    # wand arm from below while the wand shudders with the discharge.
    'Zap': ([(0, (-6, -10, 0), W((0.95, 1.75, -0.35), (0.15, 1, -0.3)), O((-0.7, 0.6, -1.2), *PUSH)),
             (6, (8, 10, 0), W((0.95, 0.75, -1.5), AIM), O((0.25, 0.5, -1.0), U, (1, 0, -0.3))),
             (8, (8, 10, 0), W((0.97, 0.82, -1.47), (-0.1, 0.07, -1)), None),
             (10, (8, 10, 0), W((0.94, 0.72, -1.51), (-0.14, -0.04, -1)), None),
             (13, (8, 10, 0), W((0.96, 0.78, -1.48), (-0.12, 0.04, -1)), None),
             (24, Z, READY, LOW)], 6),
    # Pull: both hands reach out at the aim as the beam takes hold, then yank back to the chest, leaning away.
    'Pull': ([(0, (4, 6, 0), W((0.9, 0.72, -1.45), AIM), O((-0.6, 0.7, -1.4), *PUSH)),
              (6, (6, 8, 0), W((0.88, 0.75, -1.55), AIM), O((-0.55, 0.72, -1.5), *PUSH)),
              (10, (-8, -4, 0), W((1.05, 0.55, -0.35), (0, 0.75, -0.65)),
               O((-0.7, 0.45, -0.45), (1, 0, 0), (0, 0.2, -1))),
              (15, (-8, -4, 0), W((1.07, 0.57, -0.33), (0, 0.78, -0.62)), None),
              (26, Z, READY, LOW)], 6),
    # Lift: a scoop. Both hands low and palm up, then swept up together, the wand rising past the aim.
    'Uplift': ([(0, (6, -4, 0), W((0.75, -0.35, -1.15), (0, -0.6, -0.8)), O((-0.65, -0.2, -1.0), U, F)),
                (6, (-2, 4, 0), W((0.65, 0.85, -1.45), (0, 0.55, -0.85)), O((-0.55, 0.75, -1.35), U, F)),
                (10, (-6, 4, 0), W((0.7, 1.35, -1.05), (0, 1, -0.35)), O((-0.6, 1.2, -1.0), U, F)),
                (20, Z, READY, LOW)], 6),
    # Stone Bind: an overhead chop, the wand brought down hard at the aim while the off hand drops to the side.
    'Chop': ([(0, (-8, -6, 0), W((0.6, 2.0, -0.35), (0, 0.75, 0.65)), O((-0.75, 0.5, -1.0), *PUSH)),
              (6, (14, 4, 0), W((0.55, 0.3, -1.5), (0, -0.45, -0.9)), O((-1.25, -0.35, -0.25), (1, 0, 0), D)),
              (9, (16, 4, 0), W((0.55, 0.0, -1.35), (0, -0.75, -0.65)), None),
              (20, Z, READY, LOW)], 6),
    # Slumber: a lullaby. The wand sways from side to side like a pendulum, releasing on the first swing, while the
    # off hand smooths the air, palm down.
    'Lull': ([(0, (0, 10, 0), W((0.15, 0.85, -1.35), (-0.55, 0.2, -0.8)), O((-0.85, 0.4, -1.05), D, F)),
              (6, (0, -6, 0), W((0.8, 0.7, -1.45), (0.1, 0, -1)), O((-0.8, 0.38, -1.1), D, F)),
              (13, (0, 8, 0), W((0.25, 0.8, -1.4), (-0.45, 0.1, -0.9)), O((-0.85, 0.4, -1.05), D, F)),
              (20, (0, -4, 0), W((0.75, 0.68, -1.45), (0.1, -0.05, -1)), O((-0.8, 0.38, -1.1), D, F)),
              (30, Z, READY, LOW)], 6),
    # Ward Shield, Mirror Ward and Stoneskin: the wand swept up to stand straight before the face, and the off hand
    # pushed out flat beside it, palm forward, like a shield.
    'Ward': ([(0, (-2, 8, 0), W((0.6, 0.15, -0.75), (-0.4, 0.5, -0.75)), O((-1.0, 0.1, -0.6), (1, 0, 0), F)),
              (6, (2, -6, 0), W((0.55, 1.05, -0.95), (-0.1, 1, -0.15)), O((-0.8, 0.75, -1.3), *PUSH)),
              (14, (2, -6, 0), W((0.56, 1.07, -0.96), (-0.1, 1, -0.17)), O((-0.81, 0.77, -1.32), *PUSH)),
              (24, Z, READY, LOW)], 6),
    # Bastion Dome: both hands low together, flung up overhead, then spread wide and drawn down round the sides,
    # tracing the dome.
    'Dome': ([(0, (6, 0, 0), W((0.35, -0.35, -0.95), (0, -0.5, -0.85)), O((-0.35, -0.35, -0.95), D, F)),
              (6, (-6, 0, 0), W((0.4, 2.3, -0.55), U), O((-0.4, 2.3, -0.55), (1, 0, 0), U)),
              (14, (-2, 0, 0), W((2.35, 1.4, -0.5), (0.7, 0.7, -0.1)), O((-2.35, 1.4, -0.5), F, (-0.7, 0.7, 0))),
              (22, Z, W((2.2, 0.0, -0.4), (0.6, -0.1, -0.8)), O((-2.2, 0.0, -0.4), F, (-0.7, -0.7, 0))),
              (32, Z, READY, LOW)], 6),
    # Light Orb and Swiftstep: the wand held up and stirred once round overhead, its tip ringing the air, then
    # flourished down to the front.
    'Swirl': (circle((0.65, 1.85, -0.7), 0.2, 6, 0, (-3, 0, 0)) +
              [(11, Z, W((0.7, 1.35, -1.05), (0, 0.8, -0.6)), None), (24, Z, READY, None)], 6),
    # Mend and Cleanse: the off hand held out palm up while the wand stirs above it, then the palm pushes the
    # healing out at the aim and the wand points after it.
    'Mend': ([(f, Z, W((0.8 + 0.15 * math.cos(a), 0.9, -0.9 + 0.15 * math.sin(a)),
                       (0.3 * math.cos(a), 1, 0.3 * math.sin(a))), O((-0.4, 0.4, -1.15), U, F))
              for f, a in ((0, 0), (2, 2.1), (4, 4.2))] +
             [(6, (4, 0, 0), W((0.9, 0.7, -1.35), (-0.12, 0.08, -1)), O((-0.55, 0.65, -1.45), *PUSH)),
              (14, (4, 0, 0), W((0.9, 0.69, -1.33), (-0.12, 0.06, -1)), O((-0.56, 0.64, -1.43), *PUSH)),
              (28, Z, READY, LOW)], 6),
    # Unseal: the wand pushed into the lock like a key, then turned.
    'Twist': ([(0, Z, W((0.85, 0.6, -1.15), AIM, (1, 0, 0)), None),
               (6, (4, 4, 0), W((0.85, 0.65, -1.55), AIM, (1, 0, 0)), None),
               (10, (4, 4, 0), W((0.85, 0.65, -1.55), AIM, (0.2, -1, 0)), None),
               (14, (4, 4, 0), W((0.85, 0.65, -1.53), AIM, (0.2, -1, 0)), None),
               (22, Z, READY, None)], 6),
}
LINEAR = {'Swirl'}   # keyed every frame, so straight lines between keys keep the circle round

# The game's cameras, for the previews. The camera follows a point 1.5 studs over the HumanoidRootPart. In first
# person it sits 0.5 studs behind that point, and FieldOfView 70 (vertical) on a 16:9 screen is a 14.5 mm lens on
# Blender's 36 mm sensor. In third person InputController sets the Humanoid's CameraOffset to (1.6, 0.5, 0), over
# the right shoulder, and the camera stands 9 studs back, looking a little down; the preview turns from there to
# the character and closes in on it with a 30 mm lens.
FIRST = (bl(0, 1.5, 0.5), bl(0, 1.5, -10), 14.5)
THIRD = (bl(1.6, 2.0 + 9 * math.sin(math.radians(10)), 9 * math.cos(math.radians(10))), bl(0.5, 0.7, -0.6), 30)
# In first person the arms would play low at the bottom of the view, the camera being a stud over the shoulders.
# So while a gesture plays there, EffectsController lifts the arms LIFT degrees about the shoulders and turns them
# TURN degrees in toward the middle of the view, by the shoulders' C0, ahead of the clip's own turn. It draws only
# the forearms, hands and wand there: the upper arms, a stud from the camera, would fill the view. The first-person
# previews show them so.
LIFT, TURN = 14, 8


def lifted(pose):
    """The pose with each upper arm lifted and turned in as EffectsController does in first person."""
    out = dict(pose)
    for side, turn in (('Right', TURN), ('Left', -TURN)):
        if side + 'UpperArm' not in out: continue
        (rx, ry, rz), move = out[side + 'UpperArm']
        # CFrame.Angles(lift, turn, 0) after C0, then the clip's Transform; Blender's XYZ Euler turns X first.
        shift = Matrix.Rotation(math.radians(LIFT), 3, 'X') @ Matrix.Rotation(math.radians(turn), 3, 'Y')
        turned = shift @ Matrix.Rotation(math.radians(rz), 3, 'Z') @ Matrix.Rotation(math.radians(ry), 3, 'Y') \
            @ Matrix.Rotation(math.radians(rx), 3, 'X')
        out[side + 'UpperArm'] = (tuple(math.degrees(a) for a in turned.to_euler('XYZ')), move)
    return out


data = {}
for name, (keys, release) in GESTURES.items():
    clip, last = 'Cast' + name, keys[-1][0]
    keyed = posed(name, keys)
    poses = r15.bake(rig, clip, keyed, last)
    data[clip] = {'length': round(last / rbx.FPS, 4), 'loop': False, 'priority': 'Action2',
                  'easing': {bone: 'Linear' for bone in r15.MOVING} if name in LINEAR else {},
                  'keys': poses, 'markers': [[round(release / rbx.FPS, 4), 'Release']]}
    shots = [0, release, release + 4, release + 8]
    rbx.export(clip, [body, arms, rig.obj], animation=True, preview_frames=shots)
    if rbx.PREVIEW:
        rbx.strip(clip + '_third', shots, *THIRD, resolution=(800, 450))
        r15.bake(rig, clip + 'FirstPerson', [(f, lifted(pose)) for f, pose in keyed], last)
        body.hide_render = True
        rbx.strip(clip + '_first', shots, *FIRST, resolution=(800, 450))
        body.hide_render = False
        bpy.data.actions.remove(bpy.data.actions[clip + 'FirstPerson'])

rbx.viewport((0, 0, 0.5), 9, turn=(80, 0, 35))
out = rbx.EXPORTS / 'CastAnimations.json'
out.write_text(json.dumps(data, separators=(',', ':')), encoding='utf-8')
rbx.say(f'exports/{out.name}: ' + ', '.join('%s (%d keys)' % (n, len(d['keys'])) for n, d in data.items()))
