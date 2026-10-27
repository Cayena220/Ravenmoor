"""Check player-width walking routes through the academy campus's actual geometry, on every level.

Every collidable part's top is a floor a player may stand on. A player-sized envelope (2.5 studs wide,
5.5 tall) must be clear above it, and a step from one floor to the next may rise or drop at most 1.15
studs: the stairs use 1-stud steps. The walk starts on the arrival plaza.
"""
from collections import deque
from math import ceil, floor
from academy import BOUNDS, COURTS, FLOORS, PLAZA, ROOMS, SCHOOLS

STEP=1.15; BODY=5.5; REACH=1.25
# Places the campus must leave alone: the Whisperwood zone, the duel arena and the training platform.
KEEP_OUT={'Whisperwood':(-290,-20,-235,165),'Dueling Club':(202,278,-188,-102),'Training platform':(141,191,-20,16)}


def validate_academy(world, geometry, spots, box, name_of):
    campus=next(n for n in world.findall('Item') if name_of(n)=='Ravenmoor Academy')
    names={name_of(n) for n in campus.iter('Item')}
    assert all(room[4] in names for room in ROOMS), 'Missing academy room'
    parts=[n for n in campus.iter('Item') if n.get('class') in ('Part','WedgePart')]
    assert len(parts)<=1600, f'Academy has {len(parts)} parts; its allocation is 1600'
    for node in parts:
        (cx,_,cz),(hx,_,hz)=box(node)
        assert -330<cx-hx and cx+hx<330 and -650<cz-hz and cz+hz<285, f'{name_of(node)} is outside the world'
        for place,(x0,x1,z0,z1) in KEEP_OUT.items():
            assert not (cx+hx>x0+0.05 and cx-hx<x1-0.05 and cz+hz>z0+0.05 and cz-hz<z1-0.05), f'{name_of(node)} overlaps {place}'
    xmin,xmax,zmin,zmax=BOUNDS
    floors={}; blocks={}
    for _,(cx,cy,cz),(hx,hy,hz) in geometry:
        top,bottom=cy+hy,cy-hy
        if cx+hx<xmin or cx-hx>xmax or cz+hz<zmin or cz-hz>zmax or top<0.05: continue
        for x in range(max(xmin,ceil(cx-hx)),min(xmax,floor(cx+hx))+1):
            for z in range(max(zmin,ceil(cz-hz)),min(zmax,floor(cz+hz))+1): floors.setdefault((x,z),set()).add(round(top,2))
        if top<=STEP: continue
        for x in range(max(xmin,ceil(cx-hx-REACH)),min(xmax,floor(cx+hx+REACH))+1):
            for z in range(max(zmin,ceil(cz-hz-REACH)),min(zmax,floor(cz+hz+REACH))+1): blocks.setdefault((x,z),[]).append((bottom,top))
    def levels(cell): return floors.get(cell,set())|{0.0}   # the meadow is everywhere
    def clear(cell,h): return all(b>=h+BODY or t<=h+STEP for b,t in blocks.get(cell,()))
    start=(round((PLAZA[0]+PLAZA[1])/2),PLAZA[3]-10,0.4)
    assert clear(start[:2],start[2]), 'Arrival plaza blocked'
    seen={start}; queue=deque([start])
    while queue:
        x,z,h=queue.popleft()
        for cell in ((x-1,z),(x+1,z),(x,z-1),(x,z+1)):
            if not (xmin<=cell[0]<=xmax and zmin<=cell[1]<=zmax): continue
            for h2 in levels(cell):
                state=(*cell,h2)
                if abs(h2-h)<=STEP and state not in seen and clear(cell,h2):
                    seen.add(state); queue.append(state)
    def reached(x,z,h):
        cell=(round(x),round(z))
        return any((*cell,level) in seen for level in levels(cell) if abs(level-h)<=0.5)
    for x0,x1,north,south,name,_ in ROOMS:
        assert reached((x0+x1)/2,(north+south)/2,FLOORS[name]), f'No player-width path to {name}'
    for house,(x,z,h) in COURTS.items():
        assert reached(x,z,h), f'No player-width path to the {house} quarter'
    for name in ['Mirror','Library']+['Teacher_'+s for s in SCHOOLS]:
        x,y,z=spots[name]
        assert reached(x,z,y-2.6), f'Quest interaction {name} is unreachable'
    print(f'PASS: all {len(ROOMS)} academy halls, {len(COURTS)} house quarters and {2+len(SCHOOLS)} quest anchors reachable'
          f' up the stairs; {len(parts)} academy parts (budget 1600).')
