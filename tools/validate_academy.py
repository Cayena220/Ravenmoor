"""Check a conservative player-width walking route through the academy's actual geometry."""
from collections import deque
from math import ceil, floor
from academy import ROOMS


def validate_academy(world, geometry, spots, box, name_of):
    campus=next(n for n in world.findall('Item') if name_of(n)=='Ravenmoor Academy')
    names={name_of(n) for n in campus.findall('Item')}
    assert all(room[4] in names for room in ROOMS), 'Missing academy room'
    parts=[n for n in campus.iter('Item') if n.get('class')=='Part']
    assert len(parts)<=450, 'Academy exceeds its 450-part allocation'
    # Avatar envelope: 2.5 studs wide, 5.5 studs tall above the 0.4-stud floor.
    # Rasterize solids with clearance, then flood the connected walkable surface.
    bounds=(8,180,-273,-54)
    blocked=set()
    for _,center,half in geometry:
        if center[1]+half[1]<=0.45 or center[1]-half[1]>=5.9: continue
        lo=max(bounds[0],ceil(center[0]-half[0]-1.25)); hi=min(bounds[1],floor(center[0]+half[0]+1.25))
        north=max(bounds[2],ceil(center[2]-half[2]-1.25)); south=min(bounds[3],floor(center[2]+half[2]+1.25))
        for x in range(lo,hi+1):
            for z in range(north,south+1): blocked.add((x,z))
    start=(85,-55); assert start not in blocked, 'Academy approach blocked'
    reached={start}; queue=deque([start])
    while queue:
        x,z=queue.popleft()
        for neighbor in ((x-1,z),(x+1,z),(x,z-1),(x,z+1)):
            a,b=neighbor
            if bounds[0]<=a<=bounds[1] and bounds[2]<=b<=bounds[3] and neighbor not in blocked and neighbor not in reached:
                reached.add(neighbor); queue.append(neighbor)
    for xmin,xmax,north,south,name,_ in ROOMS:
        point=(round((xmin+xmax)/2),round((north+south)/2))
        assert point in reached, f'No player-width path to {name}'
    for name in ['Mirror','Library']+['Teacher_'+s for s in ('Hex','Ward','Charm','Restoration','Alteration')]:
        x,_,z=spots[name]
        assert (round(x),round(z)) in reached, f'Quest interaction {name} is unreachable'
    for node in parts:
        center,half=box(node)
        assert center[0]-half[0]>-10 and center[0]+half[0]<200 and center[2]-half[2]>-285, 'Academy overlaps forest, arena or world boundary'
    print(f'PASS: all {len(ROOMS)} academy rooms and 7 quest anchors reachable; {len(parts)} academy parts (budget 450).')
