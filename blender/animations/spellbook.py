"""Floating spellbook for the Library: a leather tome that rises and throws its front cover open, holds, then
settles shut, in a two-second loop. The model (Spellbook.fbx) and its animation (Spellbook_Open.fbx) share
one two-bone rig. Book carries the back cover, spine and pages; Cover carries the front cover and its brass,
and hinges along the spine."""
import rbx
from palette import GOLD

LEATHER = (112, 38, 42); PAGES = (232, 220, 188)
W, D, T, C = 3.0, 4.0, 0.8, 0.12     # width (X), depth (Y), thickness (Z) and cover board, in studs

rbx.scene('Spellbook', frames=(0, 60))
book = rbx.Mesh('Spellbook')
book.box((W, D, C), (0, 0, C / 2 - T / 2), LEATHER, bone='Book')
book.box((C, D, T), (-W / 2 - C / 2, 0, 0), LEATHER, bone='Book')
book.box((W - 0.2, D - 0.24, T - 2 * C), (-0.08, 0, 0), PAGES, bone='Book')
book.box((W, D, C), (0, 0, T / 2 - C / 2), LEATHER, bone='Cover')
book.cylinder(0.55, 0.05, (0.1, 0, T / 2 + 0.02), GOLD, segments=24, bone='Cover')
book.box((0.08, 0.6, 0.55), (W / 2 + 0.04, 0, T / 2 - 0.3), GOLD, bone='Cover')
for y in (-1, 1):
    book.box((0.42, 0.42, 0.04), (W / 2 - 0.21, y * (D / 2 - 0.21), T / 2 + 0.02), GOLD, bone='Cover')
    book.box((0.42, 0.42, 0.04), (W / 2 - 0.21, y * (D / 2 - 0.21), -T / 2 - 0.02), GOLD, bone='Book')

rig = rbx.Rig('SpellbookRig', [('Book', None, (0, -D / 2, 0), (0, D / 2, 0)),
                                ('Cover', 'Book', (-W / 2, -D / 2, T / 2 - C / 2), (-W / 2, D / 2, T / 2 - C / 2))])
# Turning the cover about the spine (Y) by a negative angle lifts its free edge up and over to the left.
for frame, lift, cover in ((0, 0, 0), (20, 0.35, -150), (40, 0.35, -150), (60, 0, 0)):
    rig.key(frame, 'Book', move=(0, 0, lift))
    rig.key(frame, 'Cover', turn=(0, cover, 0))

body = book.finish(sharp=30, rig=rig)
rbx.export('Spellbook', [body, rig.obj])
rbx.export('Spellbook_Open', [body, rig.obj], animation=True, preview_frames=[0, 10, 30, 50])
