#!/usr/bin/env python3
"""Static place integrity + Lua-subset compilation + focused mocked logic checks.

Requires a Lua 5.4 shared library for the latter checks. In Roblox Studio,
run docs/PLAYTEST.md for the engine behaviors this runner cannot validate.
"""
from pathlib import Path
import ctypes
import ctypes.util
import xml.etree.ElementTree as ET
import re
import json
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(Path(__file__).resolve().parent))
from sync_scripts import map_item, signature  # noqa: E402

def box(node):
    """Axis-aligned bounds (center, half extents) of a part, including its rotation."""
    props=node.find('Properties')
    cf=props.find("CoordinateFrame[@name='CFrame']"); size=props.find("Vector3[@name='size']")
    if cf is None or size is None: return None
    center=tuple(float(cf.find(k).text) for k in ('X','Y','Z'))
    r=[[float(cf.find(f'R{i}{j}').text) for j in range(3)] for i in range(3)]
    half=[float(size.find(k).text)/2 for k in ('X','Y','Z')]
    return center,tuple(sum(abs(r[i][j])*half[j] for j in range(3)) for i in range(3))

def name_of(node): return node.find("Properties/string[@name='Name']").text

def main():
    place=ROOT/'Wandbound-Ravenmoor-Academy.rbxlx'
    tree=ET.parse(place)
    items=tree.findall('.//Item')
    refs=[i.get('referent') for i in items]
    assert len(refs)==len(set(refs)), 'Duplicate instance references'
    scripts=[i for i in items if i.get('class') in ('Script','LocalScript','ModuleScript')]
    sources=list((ROOT/'src').rglob('*.lua'))
    assert len(scripts)==len(sources), f'{len(scripts)} scripts in the place, {len(sources)} in src (run tools/sync_scripts.py)'
    disk={p.read_text(encoding='utf-8') for p in sources}
    assert {i.find("Properties/ProtectedString[@name='Source']").text or '' for i in scripts}==disk, 'Place is stale (run tools/sync_scripts.py)'
    markers=next(i for i in items if i.find("Properties/string[@name='Name']") is not None and i.find("Properties/string[@name='Name']").text=='Markers')
    names={p.find("Properties/string[@name='Name']").text for p in markers.findall('Item')}
    required=set()
    for p in sources:
        t=p.read_text(encoding='utf-8')
        required.update(re.findall(r'Anchor\s*=\s*"([A-Za-z_]+)"',t))
        required.update(re.findall(r'self:Prompt\("([A-Za-z_]+)"\s*,',t))
        assert not re.search(r'\brequire\s*\(\s*\d',t), 'External numeric require'
        assert not re.search(r'\b(?:loadstring|getfenv)\s*\(',t), 'Dynamic executable source'
    assert required<=names, f'Missing interaction markers: {required-names}'
    assert len(required)>15
    # Ensure each class has an unobstructed sphere target row at its authored coordinates.
    geometry=[]
    for node in items:
        if node.get('class') not in ('Part','SpawnLocation','WedgePart'): continue
        if node.find("Properties/bool[@name='CanCollide']").text!='true': continue
        bounds=box(node)
        if bounds: geometry.append((name_of(node),)+bounds)
    def solid(point,margin=0): return [n for n,c,h in geometry if all(abs(a-b)<e+margin for a,b,e in zip(point,c,h))]
    spots={name_of(m):box(m)[0] for m in markers.findall('Item')}
    for name,(x,y,z) in spots.items():
        if not name.startswith('Teacher_'): continue
        for n in range(1,6):
            intersections=solid((x+(n-3)*5,y+5,z+15),1.25)
            assert not intersections, f'{name}: target intersects {intersections}'
    # Shop prompts: a clear standing spot, shop walls on both sides of the doorway behind it, and an open doorway.
    # A moved or rotated map fails here, because the prompts are fixed in Workspace.Markers.
    for name in ('Oakhart','Bank','Apothecary'):
        x,y,z=spots[name]; behind=(1.5,2,2.5,3,3.5)
        assert not any(solid((x+dx,y,z+dz)) for dx,dz in ((0,0),(1.5,0),(-1.5,0),(0,1.5),(0,-1.5))), f'{name}: prompt spot is blocked'
        for dx in (-6.5,6.5):
            assert any(solid((x+dx,4,z-k)) for k in behind), f'{name}: no shop wall beside the prompt (was the map moved or rotated?)'
        assert not any(solid((x,7.5,z-k)) for k in behind), f'{name}: shop doorway is blocked'
    # Village layout: house plinths stay off roads, lanes, paths, plaza furniture, the dock, Waystone and spawn pad,
    # and off each other. The shops deliberately sit over the edges of the square's base slab, so it is not checked.
    world=next(i for i in items if i.get('class')=='Model' and name_of(i)=='Map')
    ground=[]
    for group in world.findall('Item'):
        for node in group.iter('Item'):
            n=name_of(node)
            if node.get('class')=='Part' and (n in ('Academy approach','Forest path','Forest path link','Shop lane','Garden path','Ferry dock','Planter','Bench seat')
                                              or (n=='Stone' and name_of(group).endswith('Waystone'))): ground.append((n,box(node)))
    ground+=[(name_of(s),box(s)) for s in items if s.get('class')=='SpawnLocation']
    houses={}
    for group in world.iter('Item'):
        for node in group.findall('Item'):
            if name_of(node)=='Plinth' and node.get('class')=='Part': houses[name_of(group)]=box(node)
    def overlap(a,b): return all(abs(a[0][i]-b[0][i])<a[1][i]+b[1][i]-0.05 for i in (0,2))
    names=sorted(houses)
    for i,a in enumerate(names):
        for b in names[i+1:]: assert not overlap(houses[a],houses[b]), f'{a} overlaps {b}'
        hits=[n for n,g in ground if overlap(houses[a],g)]
        assert not hits, f'{a} sits on {hits}'
    map_parts=sum(1 for i in world.iter('Item') if i.get('class') in ('Part','WedgePart'))
    assert map_parts<=1800, f'Map has {map_parts} parts; the budget is 1800'
    print(f'PASS: place XML, {len(items)} instances, {len(sources)} embedded sources, {len(required)} interaction anchors, classroom clearance,')
    print(f'      shop doors at their prompts, {len(houses)} houses clear of roads and each other, {map_parts} map parts.')
    if signature(world)!=signature(ET.fromstring(map_item())):
        print('NOTE: the place map differs from world/Map.rbxmx. Fine if you edited it in Studio on purpose;'
              ' otherwise run python tools/sync_scripts.py --map.')
    libname=ctypes.util.find_library('lua5.4')
    if not libname:
        print('SKIPPED: Lua checks; install Lua 5.4 or run tests/headless.lua with ROOT set.')
        return 2
    lib=ctypes.CDLL(libname)
    lib.luaL_newstate.restype=ctypes.c_void_p
    lib.luaL_openlibs.argtypes=[ctypes.c_void_p]
    lib.luaL_loadfilex.argtypes=[ctypes.c_void_p,ctypes.c_char_p,ctypes.c_char_p]
    lib.luaL_loadfilex.restype=ctypes.c_int
    lib.luaL_loadstring.argtypes=[ctypes.c_void_p,ctypes.c_char_p]
    lib.luaL_loadstring.restype=ctypes.c_int
    lib.lua_pcallk.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_longlong,ctypes.c_void_p]
    lib.lua_pcallk.restype=ctypes.c_int
    lib.lua_tolstring.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_void_p]
    lib.lua_tolstring.restype=ctypes.c_char_p
    lib.lua_close.argtypes=[ctypes.c_void_p]
    def err(state): return lib.lua_tolstring(state,-1,None).decode()
    for path in sources:
        state=lib.luaL_newstate()
        assert lib.luaL_loadfilex(state,str(path).encode(),None)==0, err(state)
        lib.lua_close(state)
    print(f'PASS: all {len(sources)} source files compile with the Lua 5.4 parser (Luau-compatible subset).')
    state=lib.luaL_newstate(); lib.luaL_openlibs(state)
    code=f'ROOT={json.dumps(str(ROOT))}; dofile(ROOT.."/tests/headless.lua")'
    assert lib.luaL_loadstring(state,code.encode())==0, err(state)
    status=lib.lua_pcallk(state,0,-1,0,0,None)
    if status: raise AssertionError(err(state))
    lib.lua_close(state)
    return 0

if __name__=='__main__': sys.exit(main())
