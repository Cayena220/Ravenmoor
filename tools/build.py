#!/usr/bin/env python3
"""Dependency-free, deterministic Roblox XML place and Rojo map exporter."""
from pathlib import Path
import xml.etree.ElementTree as ET
import math
import random
import json
import copy
import sys
from academy import build_academy

ROOT = Path(__file__).resolve().parents[1]
RNG = random.Random(31021)
# The village uses its own stream so adding houses never moves forest trees, stones or candles.
VILLAGE_RNG = random.Random(1189)
counter = 0

def item(parent, cls, name):
    global counter
    counter += 1
    obj = ET.SubElement(parent, 'Item', {'class': cls, 'referent': f'RBX{counter:08X}'})
    ET.SubElement(obj, 'Properties')
    prop(obj, 'string', 'Name', name)
    return obj

def prop(obj, kind, name, value):
    p = ET.SubElement(obj.find('Properties'), kind, {'name': name})
    if kind == 'Vector3':
        for k, v in zip(('X', 'Y', 'Z'), value): ET.SubElement(p, k).text = str(v)
    elif kind == 'Color3':
        for k, v in zip(('R', 'G', 'B'), value): ET.SubElement(p, k).text = str(v / 255)
    elif kind == 'CoordinateFrame':
        if len(value) == 2:
            pos, yaw = value
            c, s = math.cos(yaw), math.sin(yaw)
            matrix = (c,0,s,0,1,0,-s,0,c)
        else:
            pos, yaw, pitch, roll = value
            matrix = rotation(yaw, pitch, roll)
        for k, v in zip(('X','Y','Z','R00','R01','R02','R10','R11','R12','R20','R21','R22'), (*pos,*matrix)):
            ET.SubElement(p, k).text = str(v)
    elif kind == 'UDim2':
        for k, v in zip(('XS','XO','YS','YO'), value): ET.SubElement(p, k).text = str(v)
    elif kind == 'bool': p.text = 'true' if value else 'false'
    else: p.text = str(value)
    return p

def rotation(yaw, pitch, roll):
    """Ry(yaw)·Rx(pitch)·Rz(roll), row-major, rounded so quarter turns stay exact."""
    cy, sy, cp, sp, cr, sr = math.cos(yaw), math.sin(yaw), math.cos(pitch), math.sin(pitch), math.cos(roll), math.sin(roll)
    ry = ((cy,0,sy),(0,1,0),(-sy,0,cy)); rx = ((1,0,0),(0,cp,-sp),(0,sp,cp)); rz = ((cr,-sr,0),(sr,cr,0),(0,0,1))
    mul = lambda a, b: tuple(tuple(sum(a[i][k]*b[k][j] for k in range(3)) for j in range(3)) for i in range(3))
    return tuple(round(v, 12) + 0.0 for row in mul(mul(ry, rx), rz) for v in row)

MATERIAL = {'Plastic':256, 'SmoothPlastic':272, 'Neon':288, 'Wood':512, 'WoodPlanks':528,
            'Marble':784, 'Slate':800, 'Concrete':816, 'Granite':832, 'Brick':848,
            'Cobblestone':880, 'Rock':896, 'Grass':1280, 'Sand':1296, 'Metal':1088,
            'Glass':1568, 'LeafyGrass':1284}
STONE=(80,91,109); DARK=(45,55,71); ROOF=(47,75,91); GOLD=(202,160,83)

def part(parent, name, pos, size, color, material='SmoothPlastic', shape=1, yaw=0, collide=True, transparent=0, query=True, cls='Part', pitch=0, roll=0):
    p=item(parent,cls,name)
    prop(p,'Vector3','size',size); prop(p,'CoordinateFrame','CFrame',(pos,yaw) if not (pitch or roll) else (pos,yaw,pitch,roll))
    prop(p,'Color3uint8','Color3uint8',(255<<24)+(color[0]<<16)+(color[1]<<8)+color[2])
    prop(p,'token','Material',MATERIAL[material])
    if cls in ('Part','SpawnLocation'): prop(p,'token','shape',shape)
    prop(p,'bool','Anchored',True); prop(p,'bool','CanCollide',collide)
    prop(p,'bool','CanTouch',False); prop(p,'bool','CanQuery',query)
    prop(p,'float','Transparency',transparent)
    prop(p,'token','TopSurface',0); prop(p,'token','BottomSurface',0)
    return p

def label(parent, title, subtitle='', offset=4, distance=100):
    gui=item(parent,'BillboardGui','Nameplate')
    prop(gui,'UDim2','Size',(0,220,0,65)); prop(gui,'Vector3','StudsOffset',(0,offset,0))
    prop(gui,'bool','AlwaysOnTop',False); prop(gui,'float','MaxDistance',distance)
    t=item(gui,'TextLabel','Title'); prop(t,'UDim2','Size',(1,0,1,0)); prop(t,'float','BackgroundTransparency',1)
    prop(t,'string','Text',title+ ('\n'+subtitle if subtitle else '')); prop(t,'float','TextSize',17)
    prop(t,'bool','TextWrapped',True); prop(t,'Color3','TextColor3',(249,231,191)); prop(t,'float','TextStrokeTransparency',0.4)
    return gui

def model(parent,name):
    m=item(parent,'Model',name); prop(m,'token','ModelStreamingMode',1); return m

POINTS={
    'Oakhart':(49,3,121),'Mirror':(85,3,-125),'Teacher_Hex':(29,3,-180),
    'Teacher_Ward':(58,3,-180),'Teacher_Charm':(87,3,-180),
    'Teacher_Restoration':(116,3,-180),'Teacher_Alteration':(145,3,-180),
    'Tobb':(-5,3,12),'Bank':(128,3,120),'Apothecary':(48,3,174),'Library':(146,3,-104),
    'Duelmaster':(190,3,-86),'Training':(166,3,8),
    'ForestGate':(-58,3,15),'SpiderClearing':(-145,3,65),'Moonwell':(-216,3,44),
    'HowlerDen':(-213,3,-76),'Rotbark':(-122,3,-87),'Vexweave':(-160,3,-183),
    'Waystone_Hollowmere':(90,3,157),'Waystone_Castle':(85,3,-48),'Waystone_Whisperwood':(-36,3,20),
}

def npc(parent,name,pos,color):
    n=model(parent,name)
    x,_,z=pos
    part(n,'Robe',(x,2.5,z),(2.3,3.6,1.5),color)
    part(n,'Head',(x,5,z),(1.6,1.6,1.6),(212,169,126),shape=0)
    part(n,'HatBrim',(x,5.85,z),(2.6,0.25,2.4),color)
    part(n,'HatCrown',(x,6.4,z),(1.1,1.1,1.1),color)
    for side in (-1,1): part(n,'Sleeve',(x+side*1.5,2.9,z),(0.7,2.5,1),color)
    part(n,'Wand',(x+1.6,2.2,z-1),(0.12,0.12,1.8),(111,78,43),'Wood')
    return n

# ---- Storybook village kit -------------------------------------------------------------
# Houses are designed in a local frame with the door on the +Z side, then turned in quarter
# steps. Decorative trim never collides or answers queries, so monster steering, sight lines
# and spell projectiles see the same solid walls as before.
FACING = {'+Z': (1, 0), '+X': (0, 1), '-X': (0, -1), '-Z': (-1, 0)}
ROOF_FLIP = False  # Set True if Studio shows the roof wedges forming a valley instead of a peak.
TRIM = {'collide': False, 'query': False}
BEAM=(74,54,40); PLINTH=(118,112,104); GLASS=(246,201,120); IRON=(52,54,58)
FLOWERS=((214,84,96),(240,196,86),(156,110,206),(236,236,236))
BOTTLES=((96,214,150),(178,108,232),(236,164,72))

def shade(color, k): return tuple(max(0, min(255, round(c*k))) for c in color)

def sign(board, text, color=(236,205,140)):
    gui=item(board,'SurfaceGui','Sign')
    prop(gui,'token','Face',5)            # NormalId.Front: the board's -Z face
    prop(gui,'token','SizingMode',1)      # PixelsPerStud keeps the lettering square
    prop(gui,'float','PixelsPerStud',40); prop(gui,'float','LightInfluence',0.6)
    t=item(gui,'TextLabel','Text'); prop(t,'UDim2','Size',(1,0,1,0)); prop(t,'float','BackgroundTransparency',1)
    prop(t,'string','Text',text); prop(t,'bool','TextScaled',True); prop(t,'token','Font',8)
    prop(t,'Color3','TextColor3',color)
    return gui

def placer(m, cx, cz, facing):
    """P(name, lx, y, lz, size, color, ...) places a part given in the house's local frame."""
    c, s = FACING[facing]; base = math.atan2(s, c)
    def P(name, lx, y, lz, size, color, material='SmoothPlastic', yaw=0, **kw):
        pos = (round(cx + c*lx + s*lz, 4), round(y, 4), round(cz - s*lx + c*lz, 4))
        return part(m, name, pos, size, color, material, yaw=base + yaw, **kw)
    return P

def face_point(w, front, back, face, u, out):
    """Local (x, z) of a point u along a wall face, `out` studs proud of it."""
    if face == 'front': return u, front + out
    if face == 'back': return -u, back - out
    zc = (front + back)/2
    return (w/2 + out, zc + u) if face == 'right' else (-w/2 - out, zc + u)

def face_size(face, along, height, thick):
    return (along, height, thick) if face in ('front', 'back') else (thick, height, along)

def window(P, w, front, back, face, u, y, ww, wh, level, spec, openings):
    shutter = spec.get('shutter') if face == 'front' else None
    openings[face].append((u, ww + (2.2 if shutter else 0.6)))
    x, z = face_point(w, front, back, face, u, 0.06)
    P('Window', x, y, z, face_size(face, ww, wh, 0.12), GLASS, 'Neon', **TRIM)
    x, z = face_point(w, front, back, face, u, 0.14)
    P('Window frame', x, y-wh/2-0.12, z, face_size(face, ww+0.5, 0.24, 0.28), BEAM, 'Wood', **TRIM)
    if face != 'front': return
    P('Window frame', x, y+wh/2+0.12, z, face_size(face, ww+0.5, 0.24, 0.28), BEAM, 'Wood', **TRIM)
    P('Mullion', x, y, z, face_size(face, 0.16, wh, 0.2), BEAM, 'Wood', **TRIM)
    if shutter:
        for side in (-1, 1):
            x, z = face_point(w, front, back, face, u + side*(ww/2+0.55), 0.1)
            P('Shutter', x, y, z, face_size(face, 0.9, wh, 0.12), shutter, 'WoodPlanks', **TRIM)
    bottles = spec.get('sill') == 'bottles' and level == 0
    x, z = face_point(w, front, back, face, u, 0.42)
    P('Window box', x, y-wh/2-0.5, z, face_size(face, ww+0.3, 0.5, 0.6), BEAM, 'Wood', **TRIM)
    for i, k in enumerate((-0.28, 0.28)):
        x, z = face_point(w, front, back, face, u + k*ww, 0.45)
        if bottles: P('Bottle', x, y-wh/2+0.1, z, (0.35, 0.7, 0.35), BOTTLES[i], 'Neon', **TRIM)
        else: P('Flowers', x, y-wh/2-0.12, z, (0.6, 0.6, 0.6), VILLAGE_RNG.choice(FLOWERS), shape=0, **TRIM)

def frame(P, w, front, back, y0, h, openings):
    """Half-timbering: rails at sill and wall plate, posts at corners and beside openings, braces in open bays."""
    depth = front - back
    for face, length in (('front', w), ('back', w), ('left', depth), ('right', depth)):
        for y in (y0+0.2, y0+h-0.2):
            x, z = face_point(w, front, back, face, 0, 0.08)
            P('Beam', x, y, z, face_size(face, length+0.3, 0.4, 0.2), BEAM, 'Wood', **TRIM)
        if face == 'front':  # Street side: posts frame every opening.
            posts = [-length/2, length/2] + [e for u, span in openings[face] for e in (u - span/2 - 0.2, u + span/2 + 0.2)]
        else:  # Plainer walls: corners belong to front and back faces, plus one post between windows.
            centers = sorted(u for u, _ in openings[face])
            posts = ([-length/2, length/2] if face == 'back' else []) + [(a+b)/2 for a, b in zip(centers, centers[1:])]
        kept = []
        for p in sorted(p for p in posts if abs(p) <= length/2):
            if not kept or p - kept[-1] > 1.2: kept.append(p)
        for p in kept:
            x, z = face_point(w, front, back, face, p, 0.08)
            P('Post', x, y0+h/2, z, face_size(face, 0.4, h-0.4, 0.2), BEAM, 'Wood', **TRIM)
        if face in ('front', 'back'):
            for a, b in zip(kept, kept[1:]):
                if b - a >= 2 and not any(a < u < b for u, _ in openings[face]): brace(P, w, front, back, face, a, b, y0, h)

def brace(P, w, front, back, face, a, b, y0, h):
    """A diagonal leaning toward the middle of the wall, from the bay's outer foot to its inner head."""
    run, rise = b - a - 0.4, h - 0.8
    roll = math.atan2(rise, run) * (1 if abs(a) > abs(b) else -1) * (-1 if face == 'back' else 1)
    x, z = face_point(w, front, back, face, (a+b)/2, 0.1)
    P('Brace', x, y0+h/2, z, (math.hypot(run, rise), 0.3, 0.18), BEAM, 'Wood', roll=roll, **TRIM)

def door(P, front, spec):
    dw, dh = spec['door']
    for side in (-1, 1): P('Door frame', side*(dw/2+0.2), 0.7+dh/2, front+0.1, (0.4, dh, 0.35), BEAM, 'Wood', **TRIM)
    P('Door frame', 0, 0.7+dh+0.2, front+0.1, (dw+0.8, 0.45, 0.35), BEAM, 'Wood', **TRIM)
    leaves = (-1, 1) if dw >= 6 else (-1,)
    leaf = dw/len(leaves)
    for side in leaves:  # Swung open against the inside of the wall, out of the walkway.
        x = side*(dw/2-0.2)
        P('Door', x, 0.7+dh/2, front-1-leaf/2, (0.25, dh-0.2, leaf), spec.get('door_color', (96,58,40)), 'WoodPlanks', **TRIM)
        if spec.get('iron_bands'):
            for y in (0.7+dh*0.3, 0.7+dh*0.75): P('Door band', x-side*0.15, y, front-1-leaf/2, (0.06, 0.3, leaf), IRON, 'Metal', **TRIM)
    if spec.get('sign'):
        board = P('Sign', 0, 0.7+dh+0.88, front+0.36, (dw+1.5, 0.9, 0.18), (58,42,34), 'Wood', yaw=math.pi, **TRIM)
        sign(board, spec['sign'])

def roof(P, w, front, back, top, spec):
    rh, over, eave = spec.get('pitch', 6), 1, 1.2
    zc = (front + back)/2; half = (front - back)/2 + eave
    back_yaw, front_yaw = (math.pi, 0) if ROOF_FLIP else (0, math.pi)
    for z, yaw in ((zc - half/2, back_yaw), (zc + half/2, front_yaw)):
        P('Roof', 0, top + rh/2, z, (w + 2*over, rh, half), spec['roof'], 'Slate', yaw=yaw, cls='WedgePart')
    P('Ridge', 0, top + rh + 0.12, zc, (w + 2*over + 0.4, 0.35, 0.7), shade(spec['roof'], 0.7), 'Slate', **TRIM)
    x, z = w/2 - 2.5, zc - half/2
    P('Chimney', x, top + (rh+2.2)/2, z, (2, rh+2.2, 2), (140,82,66), 'Brick')
    P('Chimney cap', x, top + rh + 2.4, z, (2.6, 0.4, 2.6), (60,60,64), 'Slate')

def timber_house(parent, name, cx, cz, facing, spec):
    """Storybook timber house: stone plinth, framed plaster storeys, gabled slate roof, chimney."""
    m = model(parent, name); P = placer(m, cx, cz, facing)
    w, d = spec['w'], spec['d']; dw, dh = spec['door']; jetty = spec.get('jetty', 0)
    P('Plinth', 0, 0.35, 0, (w+0.6, 0.7, d+0.6), PLINTH, 'Cobblestone')  # 0.7 tall: the NPCs stand on this height
    P('Floorboards', 0, 0.72, 0, (w-1.2, 0.05, d-1.2), (138,104,72), 'WoodPlanks', **TRIM)
    P('Door step', 0, 0.2, d/2+1.05, (dw+1, 0.4, 1.5), PLINTH, 'Granite')
    y0 = 0.7
    for level, h in enumerate(spec['heights']):
        front, back = d/2 + (jetty if level else 0), -d/2
        depth, zc = front - back, (front + back)/2
        stone = level == 0 and spec.get('ground') == 'stone'
        color, material = ((150,150,146), 'Granite') if stone else (spec['plaster'], 'Concrete')
        openings = {'front': [], 'back': [], 'left': [], 'right': []}
        P('Wall', 0, y0+h/2, back+0.5, (w, h, 1), color, material)
        for side in (-1, 1): P('Wall', side*(w/2-0.5), y0+h/2, zc, (1, h, depth), color, material)
        if level == 0:
            pier = (w - dw)/2
            for side in (-1, 1): P('Wall', side*(dw/2+pier/2), y0+h/2, front-0.5, (pier, h, 1), color, material)
            P('Lintel', 0, y0+dh+(h-dh)/2, front-0.5, (dw, h-dh, 1), color, material)
            openings['front'].append((0, dw+0.8))
            if spec.get('bay'): openings['front'].append((-(dw/2+pier/2), 6.4))
            door(P, front, spec)
        else:
            P('Wall', 0, y0+h/2, front-0.5, (w, h, 1), color, material)
            if jetty:
                P('Jetty', 0, y0-0.25, d/2+jetty/2, (w, 0.5, jetty), BEAM, 'Wood')
                for u in (-w/2+1, -w/4, w/4, w/2-1): P('Corbel', u, y0-0.9, d/2+jetty/2, (0.5, 0.8, jetty), BEAM, 'Wood', **TRIM)
        for face, u, ww, wh in spec['windows'][level]:
            window(P, w, front, back, face, u, y0 + h*0.55, ww, wh, level, spec, openings)
        if not stone: frame(P, w, front, back, y0, h, openings)
        y0 += h
    roof(P, w, d/2 + jetty, -d/2, y0, spec)
    for feature in spec.get('features', ()): feature(P, spec)
    return m

def bay_window(P, spec):
    """Oakhart's display bay: glazed box on the left pier with a rack of wands."""
    w, d, dw = spec['w'], spec['d'], spec['door'][0]
    u, z = -(dw/2 + (w-dw)/4), spec['d']/2
    P('Bay base', u, 1.2, z+0.85, (5.6, 1.0, 1.7), PLINTH, 'Granite')
    P('Display back', u, 3.6, z+0.06, (5.2, 3.8, 0.1), (44,36,48), 'Wood', **TRIM)
    P('Display rack', u, 2.0, z+0.9, (4.8, 0.3, 0.6), BEAM, 'Wood', **TRIM)
    for i, color in enumerate(((150,112,72),(60,48,44),(214,206,190),(118,70,52),(96,80,64))):
        P('Display wand', u-2+i, 2.95+0.15*(i % 2), z+0.9, (0.14, 1.6, 0.14), color, 'Wood', **TRIM)
    P('Bay glass', u, 3.6, z+1.62, (5.2, 3.8, 0.1), (214,232,236), 'Glass', transparent=0.45, **TRIM)
    for k in (-1, 1):
        P('Bay glass', u+k*2.62, 3.6, z+0.85, (0.1, 3.8, 1.5), (214,232,236), 'Glass', transparent=0.45, **TRIM)
        P('Bay post', u+k*2.65, 3.6, z+1.6, (0.3, 3.8, 0.3), BEAM, 'Wood', **TRIM)
    P('Bay roof', u, 5.7, z+0.95, (6.2, 0.4, 2.0), spec['roof'], 'Slate', **TRIM)

def columns(P, spec):
    """Marble columns flanking the bank door."""
    d, (dw, dh) = spec['d'], spec['door']
    for side in (-1, 1):
        x, z = side*(dw/2+1.1), d/2+1.3
        P('Column base', x, 0.175, z, (1.6, 0.35, 1.6), (196,192,182), 'Marble')
        P('Column', x, 0.35+(dh+0.5)/2, z, (dh+0.5, 1.1, 1.1), (214,210,200), 'Marble', shape=2, roll=math.pi/2)
        P('Column capital', x, dh+1.025, z, (1.6, 0.35, 1.6), (196,192,182), 'Marble')

def herb_planters(P, spec):
    d, dw = spec['d'], spec['door'][0]
    for side in (-1, 1):
        x = side*(dw/2+2.6)
        P('Planter', x, 0.25, d/2+0.9, (3.2, 0.5, 1.0), BEAM, 'WoodPlanks', **TRIM)
        for k in (-1, 0, 1): P('Herbs', x+k*0.95, 0.75, d/2+0.9, (0.8, 0.8, 0.8), (88,132+20*k,78), 'Grass', shape=0, **TRIM)

def awnings(P, spec):
    """Striped awnings over the tailor's display windows, and a bench of fabric bolts."""
    w, d, (dw, _) = spec['w'], spec['d'], spec['door']
    tilt, reach, strips = 0.35, 2.2, 6
    for side in (-1, 1):
        u, span = side*(dw/2 + (w-dw)/4), 7.6
        for i in range(strips):
            P('Awning', u - span/2 + span/strips*(i+0.5), 8.0 - reach/2*math.sin(tilt), d/2 + 0.15 + reach/2*math.cos(tilt),
              (span/strips, 0.12, reach), (182,62,72) if i % 2 == 0 else (236,226,206), pitch=tilt, **TRIM)
    x = -(dw/2 + 3.2)
    P('Display bench', x, 0.45, d/2+1.0, (3.6, 0.9, 1.2), BEAM, 'WoodPlanks')
    for i, color in enumerate(((126,72,140),(70,110,160),(196,150,70))):
        P('Fabric bolt', x, 1.25, d/2+0.65+0.35*i, (2.8, 0.6, 0.6), color, 'SmoothPlastic', shape=2, **TRIM)

SHOP = {'w': 28, 'd': 26, 'heights': (9, 6.5), 'door': (9, 7.2), 'pitch': 9}
UPPER = [('front',-9,3,3),('front',0,3,3),('front',9,3,3),('left',-5,3,3),('left',5,3,3),
         ('right',-5,3,3),('right',5,3,3),('back',-7,3,3),('back',7,3,3)]
GROUND = [('left',0,3,3),('right',0,3,3),('back',-6,3,3),('back',6,3,3)]
# Same centers and 28×26 footprints as before, so every door stays where its NPC prompt is.
SHOPS = [
    ('Oakharts Wandery', 49, 105, dict(SHOP, plaster=(233,221,192), roof=(64,74,92), shutter=(110,62,54), jetty=1.5,
        sign="OAKHART'S WANDS", bay=True, windows=([('front',9.25,4,3.4)]+GROUND, UPPER), features=(bay_window,))),
    ('Vaultkeep Bank', 128, 104, dict(SHOP, plaster=(226,222,210), roof=(52,62,70), ground='stone', sign='VAULTKEEP BANK',
        iron_bands=True, door_color=(70,52,40), windows=([('front',-9.25,3,3.4),('front',9.25,3,3.4)]+GROUND, UPPER), features=(columns,))),
    ('Apothecary', 48, 159, dict(SHOP, plaster=(226,232,206), roof=(58,80,70), shutter=(70,120,80), jetty=1.0,
        sign='HOLLOWMERE APOTHECARY', sill='bottles', windows=([('front',-9.25,4,3.4),('front',9.25,4,3.4)]+GROUND, UPPER), features=(herb_planters,))),
    ('Tailor display', 135, 173, dict(SHOP, plaster=(236,214,214), roof=(74,60,80), shutter=(120,80,130), jetty=1.0,
        sign='THREADS & THIMBLES', windows=([('front',-9.25,6.6,3.4),('front',9.25,6.6,3.4)]+GROUND, UPPER), features=(awnings,))),
]
# Villager cottages (14×12). Each door faces the lane or road its garden path joins.
HOMES = [(22,128,'+X'), (24,186,'+X'), (52,72,'+X'), (122,72,'-X'), (55,203,'-Z'), (125,203,'-Z')]

def cottage_spec():
    r = VILLAGE_RNG
    return {'w': 14, 'd': 12, 'heights': (7,), 'door': (4, 6.2), 'pitch': 6.5,
            'plaster': r.choice(((236,224,196),(229,214,188),(240,232,214),(224,206,180))),
            'roof': r.choice(((64,74,92),(86,64,58),(58,70,64),(78,72,86))),
            'shutter': r.choice(((92,120,84),(110,62,54),(64,96,128),(132,100,60))),
            'windows': ([('front',-4.6,2.4,2.4),('front',4.6,2.4,2.4),('left',0,2.2,2.2),('right',0,2.2,2.2),('back',0,2.4,2.2)],)}

# ---- Roads -------------------------------------------------------------------------------
def frange(a, b, step):
    return [a + step*i for i in range(int((b - a)//step) + 1)]

def road_trim(parent, axis, center, width, a, b, top, gaps=((), ())):
    """Slate curbs, dirt verges and paving bands over an existing bed running along `axis` from a to b.
    gaps lists (start, end) openings in the left/right curb where lanes and paths join."""
    for side, side_gaps in zip((-1, 1), gaps):
        edge, cur, runs = center + side*(width/2 - 0.4), a, []
        for g0, g1 in sorted(side_gaps):
            if g0 > cur: runs.append((cur, g0))
            cur = max(cur, g1)
        if cur < b: runs.append((cur, b))
        for r0, r1 in runs:  # Curbs collide for players but stay out of raycasts and monster steering.
            mid, length = (r0 + r1)/2, r1 - r0
            part(parent, 'Curb', (edge, top+0.15, mid) if axis == 'z' else (mid, top+0.15, edge),
                 (0.8, 0.3, length) if axis == 'z' else (length, 0.3, 0.8), (104,108,112), 'Slate', query=False)
        verge = center + side*(width/2 + 0.6)
        part(parent, 'Verge', (verge, 0.03, (a+b)/2) if axis == 'z' else ((a+b)/2, 0.03, verge),
             (1.2, 0.06, b-a) if axis == 'z' else (b-a, 0.06, 1.2), (104,98,70), 'Sand', **TRIM)
    for t in frange(a+4, b-2, 8):
        part(parent, 'Paving band', (center, top+0.01, t) if axis == 'z' else (t, top+0.01, center),
             (width-1.6, 0.02, 0.7) if axis == 'z' else (0.7, 0.02, width-1.6), (118,110,96), 'Cobblestone', **TRIM)

def lamp(parent, x, z, side):
    """Iron lamp post whose curved arm hangs a lantern over the road (side +1 = east, -1 = west)."""
    part(parent,'Lamp base',(x,0.4,z),(1.2,0.8,1.2),(96,98,102),'Granite')
    part(parent,'Lantern',(x,3.7,z),(0.35,7.4,0.35),(64,66,65),'Metal')
    part(parent,'Lamp arm',(x+side*0.9,7.2,z),(1.8,0.18,0.18),IRON,'Metal',**TRIM)
    part(parent,'Lamp brace',(x+side*0.45,6.75,z),(1.27,0.12,0.12),IRON,'Metal',roll=side*math.pi/4,**TRIM)
    part(parent,'Lamp cap',(x+side*1.6,6.85,z),(0.9,0.25,0.9),(40,42,46),'Metal',**TRIM)
    part(parent,'Lantern glass',(x+side*1.6,6.2,z),(0.6,0.9,0.6),(246,191,109),'Neon',**TRIM)

def plaza(parent, cx, cz, w, d, top):
    """Checker paving and a granite border laid flush over the village square."""
    tw, td = w/8, d/8
    for i in range(8):
        for j in range(8):
            if (i + j) % 2:
                part(parent,'Plaza tile',(cx-w/2+tw*(i+0.5),top+0.01,cz-d/2+td*(j+0.5)),(tw-0.3,0.02,td-0.3),(128,120,106),'Cobblestone',**TRIM)
    for side in (-1, 1):
        part(parent,'Plaza border',(cx+side*(w/2-0.6),top+0.015,cz),(1.2,0.03,d),(96,98,102),'Granite',**TRIM)
        part(parent,'Plaza border',(cx,top+0.015,cz+side*(d/2-0.6)),(w-2.4,0.03,1.2),(96,98,102),'Granite',**TRIM)

def bench(parent, x, z, top=0.45):
    part(parent,'Bench seat',(x,top+0.9,z),(4,0.3,1.2),(120,86,58),'WoodPlanks')
    part(parent,'Bench back',(x,top+1.45,z+0.55),(4,0.8,0.2),(120,86,58),'WoodPlanks')
    for side in (-1, 1): part(parent,'Bench leg',(x+side*1.6,top+0.375,z),(0.3,0.75,1.0),IRON,'Metal')

def planter(parent, x, z, top=0.45):
    part(parent,'Planter',(x,top+0.45,z),(2.4,0.9,2.4),(140,82,66),'Brick')
    part(parent,'Shrub',(x,top+1.6,z),(2,2,2),(70,112,72),'Grass',shape=0,**TRIM)
    part(parent,'Flowers',(x+0.5,top+2.2,z-0.4),(0.7,0.7,0.7),VILLAGE_RNG.choice(FLOWERS),shape=0,**TRIM)

# Cobble lanes from the square to each shop door, and gravel paths from each cottage door.
LANES = [((49,121.9),(10,4.2)), ((127.5,120.9),(11,4.2)), ((48.5,175.9),(11,4.2)),
         ((116.8,183.65),(7.6,8.3)), ((126.5,189.65),(27,3.7))]
GARDEN_PATHS = [((41.9,128),(24.2,3)), ((58.9,186),(54.2,3)), ((66.9,72),(14.2,3)),
                ((105.1,72),(18.2,3)), ((55,191.35),(3,7.7)), ((125,193.35),(3,3.7))]

def tree(parent,x,z,scale=1):
    m=model(parent,'Whisperwood tree')
    part(m,'Trunk',(x,8*scale,z),(2.2*scale,16*scale,2.2*scale),(78,70,59),'Wood')
    for h,s in ((15,13),(22,11),(28,7)):
        part(m,'Canopy',(x,h*scale,z),(s*scale,9*scale,s*scale),(46+RNG.randrange(8),74+RNG.randrange(15),65+RNG.randrange(12)),shape=0,collide=False,query=False)
    return m

def make_world(workspace):
    world=item(workspace,'Model','Map')
    ground=model(world,'Land')
    part(ground,'Meadow',(0,-2,0),(660,4,570),(108,130,102),'Grass')
    part(ground,'Forest floor',(-160,0,-35),(270,0.15,410),(66,83,70),'Grass')
    part(ground,'Academy approach',(85,0.2,10),(22,0.35,300),(146,139,121),'Cobblestone')
    part(ground,'Forest path',(-30,0.23,18),(200,0.4,15),(126,119,98),'Cobblestone')
    part(ground,'Village square',(88,0.25,147),(68,0.4,65),(150,140,121),'Cobblestone')
    part(ground,'Forest path link',(72,0.23,18),(4,0.4,15),(126,119,98),'Cobblestone')
    roads=item(world,'Folder','Roads')
    # Academy approach: visible from the courtyard (z -47) to the square; curb openings for the forest path and two garden paths.
    road_trim(roads,'z',85,22,-47,114.5,0.375,gaps=([(10.5,25.5),(70.5,73.5)],[(70.5,73.5)]))
    # Forest path: cobbled across the meadow, worn to dirt where it enters Whisperwood.
    road_trim(roads,'x',18,15,-25,74,0.43)
    part(roads,'Worn path',(-77.5,0.45,18),(105,0.04,14.6),(122,100,72),'Sand',**TRIM)
    for _ in range(7):
        part(roads,'Cobble remnant',(round(VILLAGE_RNG.uniform(-124,-31),2),0.48,round(VILLAGE_RNG.uniform(12.5,23.5),2)),
             (round(VILLAGE_RNG.uniform(1.5,3.5),2),0.03,round(VILLAGE_RNG.uniform(1.5,3),2)),(120,114,96),'Cobblestone',**TRIM)
    lamps=item(world,'Folder','Lamps')
    for z in range(-45,155,24):
        for x,side in ((70,1),(100,-1)): lamp(lamps,x,z,side)
    # Invisible limits are deliberately far outside the authored play space.
    for pos,size in [((-331,35,0),(2,70,570)),((331,35,0),(2,70,570)),((0,35,-286),(660,70,2)),((0,35,286),(660,70,2))]:
        part(ground,'World boundary',pos,size,(0,0,0),transparent=1)
    village=model(world,'Hollowmere')
    for name,x,z,spec in SHOPS: timber_house(village,name,x,z,'+Z',spec)
    for i,(x,z,facing) in enumerate(HOMES,1): timber_house(village,f'Cottage {i}',x,z,facing,cottage_spec())
    plaza(village,88,147,68,65,0.45)
    for x in (76,104): bench(village,x,168)
    for x,z in ((66.5,121),(109.5,121),(57.5,176),(118.5,176)): planter(village,x,z)
    for (x,z),(w,d) in LANES: part(village,'Shop lane',(x,0.25,z),(w,0.4,d),(150,140,121),'Cobblestone')
    for (x,z),(w,d) in GARDEN_PATHS: part(village,'Garden path',(x,0.05,z),(w,0.1,d),(176,164,138),'Sand')
    part(village,'Ferry dock',(90,0.5,206),(26,1,30),(107,84,63),'WoodPlanks')
    ferry=model(village,'Sky ferry')
    part(ferry,'Hull',(90,4,213),(20,5,29),(77,89,105),'Wood')
    part(ferry,'Deck',(90,7,213),(18,1,27),(145,116,81),'WoodPlanks')
    part(ferry,'Sail mast',(90,16,213),(0.5,18,0.5),GOLD,'Metal')
    part(ferry,'Sail',(95,17,213),(9,12,0.2),(218,209,184))
    # Mirrorlake uses stylized layered geometry; custom terrain is an art milestone.
    lake=model(world,'Mirrorlake')
    part(lake,'Shore',(218,-0.1,123),(103,1,111),(161,155,124),shape=0)
    part(lake,'Water',(218,0.1,123),(93,0.45,100),(74,140,155),'Glass',shape=0,transparent=0.25,collide=False,query=False)
    part(lake,'Small island',(239,0.4,105),(20,1,18),(110,125,104),shape=0)
    tree(lake,239,105,0.75)
    build_academy(world,part,model,label,POINTS)
    # The original hall consumed 84 draws for floating candles. Keep the forest seed stable.
    for _ in range(84): RNG.random()
    # Forest clearings and low-poly vegetation.
    forest=model(world,'Whisperwood')
    clearings=[(-75,15,29),(-147,68,32),(-216,45,32),(-210,-76,34),(-122,-87,28),(-160,-183,50)]
    for x,z,r in clearings: part(forest,'Clearing',(x,0.2,z),(r*2,0.2,r*2),(86,95,76),shape=0)
    for _ in range(120):
        x=RNG.uniform(-290,-40); z=RNG.uniform(-240,150)
        if any((x-a)**2+(z-b)**2<(r+9)**2 for a,b,r in clearings): continue
        if abs(z-18)<15 or (-150<x<-120 and -180<z<65): continue
        tree(forest,x,z,RNG.uniform(0.65,1.15))
    for _ in range(30):
        x=RNG.uniform(-290,-45); z=RNG.uniform(-245,150)
        if any((x-a)**2+(z-b)**2<(r+4)**2 for a,b,r in clearings): continue
        part(forest,'Stone',(x,2,z),(RNG.uniform(3,8),RNG.uniform(3,7),RNG.uniform(3,8)),(83,94,94),'Rock',shape=0)
    for side in (-1,1):
        part(forest,'Forest gate',(-38,7,18+side*12),(4,14,4),(83,94,90),'Rock')
        part(forest,'Gate rune',(-35.8,8,18+side*12),(0.3,4,2),(126,211,184),'Neon',query=False,collide=False)
    part(forest,'Moonwell',(-216,0.7,44),(15,1,15),(114,199,191),'Neon',shape=0,query=False,collide=False)
    for i in range(9):
        a=i*math.tau/9; x=-160+math.cos(a)*47; z=-183+math.sin(a)*43
        part(forest,'Grotto standing stone',(x,8,z),(6,16,7),(68,73,88),'Rock',yaw=a)
        part(forest,'Hollow rune',(x,15,z),(1.2,3,1.2),(195,116,188),'Neon',collide=False,query=False)
    # Rune chests are individual models used by the Resero spell handler.
    for i,(x,z) in enumerate([(118,63),(-103,66),(-180,-128)],1):
        chest=model(world,'RuneChest'+str(i)); p=part(chest,'Chest',(x,1.8,z),(5,3,3),(107,79,55),'Wood')
        part(chest,'Brass band',(x,1.9,z-1.55),(0.6,3,0.15),GOLD,'Metal')
        label(p,'SEALED CHEST','Aim and cast Resero',3,55)
    grounds=model(world,'Castle Grounds')
    part(grounds,'Training platform',(166,0.5,-2),(50,1,36),(124,131,129),'Cobblestone')
    arena=model(world,'Dueling Club')
    part(arena,'Arena',(240,0.4,-145),(76,0.8,86),(116,125,135),'Marble')
    for x in (203,277): part(arena,'Edge',(x,0.95,-145),(1,0.3,86),GOLD,'Metal')
    for z in (-188,-102): part(arena,'Edge',(240,0.95,z),(76,0.3,1),GOLD,'Metal')
    part(arena,'Center line',(240,0.95,-145),(72,0.2,0.4),GOLD,'Metal')
    people=model(world,'Academy staff')
    names={'Oakhart':('Odric Oakhart','Wandmaker',(117,92,67)),'Tobb':('Tobb Brambleworth','Groundskeeper',(101,119,74)),
           'Duelmaster':('Kestrel Vey','Duelmaster · Excido at level 6',(102,81,120))}
    teacher_titles={'Hex':('Professor Rook','Hexcraft'),'Ward':('Professor Holloway','Warding'),'Charm':('Professor Quill','Charms'),
                    'Restoration':('Healer Fenn','Restoration'),'Alteration':('Professor Ashgrove','Alteration')}
    for school,(name,title) in teacher_titles.items(): names['Teacher_'+school]=(name,title,(76,101,120))
    for anchor,(name,title,color) in names.items():
        # NPCs stand behind prompts, leaving room to interact without getting stuck.
        x,y,z=POINTS[anchor]; n=npc(people,name,(x,y,z-2.8),color)
        head=next(o for o in n.findall('Item') if o.find("Properties/string[@name='Name']").text=='Head')
        label(head,name,title,3,90)
    mirror=model(world,'Mirror of Choosing')
    part(mirror,'Frame',(85,6,-129),(9,12,1),GOLD,'Metal')
    p=part(mirror,'Mirror',(85,6,-128.3),(7,10,0.3),(152,189,215),'Glass',transparent=0.2)
    label(p,'THE MIRROR OF CHOOSING','Courage · Loyalty · Wisdom · Ambition',8,90)
    for key in ('Hollowmere','Castle','Whisperwood'):
        x,y,z=POINTS['Waystone_'+key]
        m=model(world,key+' Waystone'); p=part(m,'Stone',(x,3.5,z),(3,7,3),(79,111,123),'Slate')
        part(m,'Rune',(x,6.8,z),(2,2,2),(130,228,226),'Neon',shape=0,query=False,collide=False)
        label(p,key.upper()+' WAYSTONE','Attune & fast travel',6,90)
    markers=item(workspace,'Folder','Markers')
    signs={'Bank':('VAULTKEEP BANK','Deposit & withdraw'), 'Apothecary':('APOTHECARY','Potions & brewing'),
           'Library':('THE RESTRICTED SHELF','Tractum at level 14'), 'Training':('TRAINING YARD','Practice your Spark Bolt'),
           'ForestGate':('WHISPERWOOD','Levels 5–20 · PvE')}
    for key,pos in POINTS.items():
        marker=part(markers,key,pos,(1,1,1),(255,255,255),collide=False,transparent=1,query=False)
        if key in signs: label(marker,*signs[key],offset=5,distance=95)
    spawns=item(workspace,'Folder','Spawns')
    spawn=part(spawns,'Hollowmere arrival',(90,0.5,184),(8,1,8),(144,151,143),'Cobblestone',cls='SpawnLocation')
    prop(spawn,'bool','Neutral',True); prop(spawn,'float','Duration',0)
    return world,markers,spawns

def scripts(parent,path):
    for f in sorted(path.iterdir()):
        if f.is_dir(): scripts(item(parent,'Folder',f.name),f)
        elif f.suffix=='.lua':
            if f.name.endswith('.server.lua'): cls='Script'; name=f.name[:-11]
            elif f.name.endswith('.client.lua'): cls='LocalScript'; name=f.name[:-11]
            else: cls='ModuleScript'; name=f.stem
            obj=item(parent,cls,name); prop(obj,'ProtectedString','Source',f.read_text(encoding='utf-8'))

# Explicit UTF-8 and LF so Windows builds match other platforms byte for byte.
def save_text(path,text): path.write_text(text,encoding='utf-8',newline='\n')

def save_xml(node,path):
    with open(path,'wb') as f: ET.ElementTree(node).write(f,encoding='utf-8',xml_declaration=True)

def main():
    """Writes the place and world/ models. --world-only skips the place, so a Studio-saved
    place is untouched; copy the new map into it with tools/sync_scripts.py --map."""
    global counter
    counter=0
    world_only='--world-only' in sys.argv
    points='return {\n'+''.join(f'    ["{k}"] = {{{v[0]}, {v[1]}, {v[2]}}},\n' for k,v in POINTS.items())+'}\n'
    save_text(ROOT/'src/shared/WorldPoints.lua',points)
    doc=ET.Element('roblox',{'version':'4'}); ET.SubElement(doc,'External').text='null'; ET.SubElement(doc,'External').text='nil'
    workspace=item(doc,'Workspace','Workspace'); prop(workspace,'bool','StreamingEnabled',True)
    prop(workspace,'float','StreamingMinRadius',96); prop(workspace,'float','StreamingTargetRadius',300)
    prop(workspace,'float','FallenPartsDestroyHeight',-100)
    world,markers,spawns=make_world(workspace)
    rep=item(doc,'ReplicatedStorage','ReplicatedStorage'); scripts(item(rep,'Folder','Shared'),ROOT/'src/shared')
    scripts(item(doc,'ServerScriptService','ServerScriptService'),ROOT/'src/server')
    scripts(item(doc,'ServerStorage','ServerStorage'),ROOT/'src/serverstorage')
    starter=item(doc,'StarterPlayer','StarterPlayer'); prop(starter,'float','CameraMinZoomDistance',5); prop(starter,'float','CameraMaxZoomDistance',14)
    scripts(item(starter,'StarterPlayerScripts','StarterPlayerScripts'),ROOT/'src/client')
    light=item(doc,'Lighting','Lighting'); prop(light,'float','ClockTime',9); prop(light,'float','Brightness',2.5)
    prop(light,'Color3','Ambient',(114,117,132)); prop(light,'Color3','OutdoorAmbient',(143,152,157)); prop(light,'bool','GlobalShadows',True)
    atmosphere=item(light,'Atmosphere','Atmosphere'); prop(atmosphere,'float','Density',0.25); prop(atmosphere,'float','Haze',1)
    prop(atmosphere,'Color3','Color',(198,213,217)); prop(atmosphere,'Color3','Decay',(115,128,145))
    bloom=item(light,'BloomEffect','LanternBloom'); prop(bloom,'float','Intensity',0.16); prop(bloom,'float','Size',24); prop(bloom,'float','Threshold',1.2)
    chat=item(doc,'TextChatService','TextChatService'); prop(chat,'bool','CreateDefaultTextChannels',True); prop(chat,'bool','CreateDefaultCommands',True)
    output=ROOT/'Wandbound-Ravenmoor-Academy.rbxlx'
    ET.indent(doc,space='  ')
    if not world_only: save_xml(doc,output)
    assets=ROOT/'world'; assets.mkdir(exist_ok=True)
    for name,node in [('Map',world),('Markers',markers),('Spawns',spawns)]:
        r=ET.Element('roblox',{'version':'4'}); r.append(copy.deepcopy(node)); save_xml(r,assets/(name+'.rbxmx'))
    project={'name':'Wandbound','tree':{'$className':'DataModel',
        'Workspace':{'$properties':{'StreamingEnabled':True},'Map':{'$path':'world/Map.rbxmx'},'Markers':{'$path':'world/Markers.rbxmx'},'Spawns':{'$path':'world/Spawns.rbxmx'}},
        'ReplicatedStorage':{'Shared':{'$path':'src/shared'}},'ServerScriptService':{'$path':'src/server'},'ServerStorage':{'$path':'src/serverstorage'},
        'StarterPlayer':{'StarterPlayerScripts':{'$path':'src/client'}}}}
    save_text(ROOT/'default.project.json',json.dumps(project,indent=2)+'\n')
    instances=len(doc.findall('.//Item')); parts=sum(1 for x in doc.findall('.//Item') if x.get('class') in ('Part','SpawnLocation','WedgePart'))
    map_parts=sum(1 for x in world.iter('Item') if x.get('class') in ('Part','WedgePart'))
    print(json.dumps({'place':None if world_only else str(output),'instances':instances,'parts':parts,'map_parts':map_parts,
        'scripts':len(list((ROOT/'src').rglob('*.lua'))),'bytes':None if world_only else output.stat().st_size}))

if __name__=='__main__': main()
