"""Iron cauldron for brewing: a pot-bellied pot on three legs, with two ring handles and a Health Draught on the
boil. About 4 studs across and 3.1 tall, so a 5.5-stud player looks down into it. One mesh, no rig."""
import math
import rbx
from palette import IRON

DRAUGHT = (92, 184, 116); BUBBLE = (150, 222, 160)

rbx.scene('Cauldron')
pot = rbx.Mesh('Cauldron')
# Up the outside from the base, over the lip, then down the inside to the floor of the pot.
pot.lathe([(0, 0.45), (0.9, 0.5), (1.45, 0.8), (1.8, 1.35), (1.9, 1.9), (1.78, 2.45), (1.55, 2.8), (1.72, 2.95),
           (1.72, 3.1), (1.45, 3.1), (1.36, 2.8), (1.6, 2.4), (1.72, 1.9), (1.62, 1.4), (1.3, 0.95), (0.8, 0.7),
           (0, 0.65)], IRON)
pot.cylinder(1.58, 0.06, (0, 0, 2.33), DRAUGHT, segments=32)
for x, y, r in ((0.5, 0.3, 0.2), (-0.6, 0.55, 0.14), (0.1, -0.7, 0.17)):
    pot.sphere(r, (x, y, 2.36), BUBBLE, scale=(1, 1, 0.6))
for k in range(3):
    a = 2 * math.pi * k / 3 + math.pi / 6
    pot.cylinder(0.2, 0.7, (1.05 * math.cos(a), 1.05 * math.sin(a), 0.35), IRON, top=0.3, segments=10)
for side in (-1, 1):
    pot.box((0.4, 0.22, 0.28), (1.82 * side, 0, 2.62), IRON)
    pot.torus(0.3, 0.06, (1.98 * side, 0, 2.32), IRON, turn=(0, 90, 0))

rbx.export('Cauldron', [pot.finish(sharp=40)])
