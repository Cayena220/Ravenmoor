"""Ravenmoor Academy campus, remodelled from the exterior concept canvas
(https://claude.ai/artifact/9WsYqy3tTPN4NaBVxsGduk) and fitted to this map.

Three levels climb north from the approach road: the arrival plaza and Main Gate on the meadow, two
classroom wings 20 studs up either side of the Grand Stair, and the upper terrace 40 studs up with the
Entrance Keep, Great Hall, Rookery Tower, Library and Starwatch Tower. Every classroom is a hall of its own,
and each house has a separate walled quarter north of the upper terrace with its own common room, dorm
tower, gate and stair. Stairs use a 1-stud rise and a 2-stud run. Everything is plain parts and wedges.
Coordinates: X runs east, Z runs south (north is -Z), Y is up.
"""
import math
import random
from palette import (CASTLE_STONE, LIMESTONE, COURSE, ARCH_SHADOW, SLATE, RIDGE, COPPER, IRON, BEAM, PLAZA,
                     ROAD, FLOOR, HEDGE, WATER, LAMPLIGHT)

MID=20; TOP=40            # classroom-wing and upper-terrace levels
CX=85                     # centre line of the approach road and the Grand Stair
# Footprints as (xmin, xmax, north Z, south Z).
ARRIVAL=(45,125,-110,-50)
LANDING=(45,125,-180,-150)
WINGS={'West':(-18,38,-215,-60),'East':(136,192,-215,-60)}
UPPER=(-10,180,-340,-220)
BOUNDS=(-240,320,-630,-20)   # the area the walking check covers
SCHOOLS=['Hex','Ward','Charm','Restoration','Alteration']
HOUSES=[('Emberclaw',(168,58,55)),('Stoneroot',(192,145,53)),('Skyquill',(63,114,180)),('Nightfang',(55,133,98))]
# House quarters: centre x, z and terrace height. The front, with the gate and stair, faces the campus.
QUARTERS=[(-190,-430,12),(-190,-580,24),(270,-430,12),(270,-580,24)]
# Village lamp posts along the plaza, the two avenues, the garden walk and the east walk: x, z, and the
# side (+1 or -1) along the axis ('x' or 'z') that the arm reaches toward. build.py places them in Lamps.
LAMPS=([(47,z,1,'x') for z in (-75,-100)]+[(123,z,-1,'x') for z in (-75,-100)]
       +[(x,-418,-1,'z') for x in (-100,-60,-20,20,60,160)]+[(x,-590,1,'z') for x in (-75,-35,5,45,85,150)]
       +[(106,z,1,'x') for z in (-455,-505,-555)]+[(203,z,-1,'x') for z in (-50,-230,-280,-330,-380)])

# xmin, xmax, north Z, south Z, name, accent. Teacher anchors stand 9 studs inside a classroom's north wall,
# so the lesson targets 15 studs south of them stay inside the hall.
ROOMS=[
    (-14,34,-210,-174,'Hex Classroom',(99,143,163)),
    (-14,34,-160,-124,'Ward Classroom',(99,143,163)),
    (-14,34,-110,-74,'Charm Classroom',(99,143,163)),
    (140,188,-210,-174,'Restoration Classroom',(99,143,163)),
    (140,188,-160,-124,'Alteration Classroom',(99,143,163)),
    (35,135,-305,-250,'Great Hall',(183,145,79)),
    (-8,22,-315,-232,'Library & Archive',(86,132,174)),
]
FLOORS={name:(MID if name.endswith('Classroom') else TOP)+0.4 for *_,name,_ in ROOMS}
COURTS={}   # house name -> (x, z, floor) of its private court, filled in below


def quarter(cx,cz,h):
    """A house quarter's layout. mx is +1 when the front faces east, -1 when it faces west."""
    mx=1 if cx<CX else -1
    hall=tuple(sorted((cx-mx*40,cx-mx*8)))+(cz-30,cz+14)
    return mx,hall,(cx-mx*24,cz+28)


for (house,color),(cx,cz,h) in zip(HOUSES,QUARTERS):
    mx,(x0,x1,n,s),_=quarter(cx,cz,h)
    ROOMS.append((x0,x1,n,s,house+' House',color)); FLOORS[house+' House']=h+0.4
    COURTS[house]=(cx+mx*20,cz,h)

PITCH=math.tan(math.radians(52))   # roof rise per stud of run
TRIM={'collide':False,'query':False}
# Keep equal to build.ROOF_FLIP. False: a WedgePart's tall face is its back (+Z), sloping down to the front.
WEDGE_FLIP=False


def _sub(a,b): return tuple(x-y for x,y in zip(a,b))
def _add(a,b): return tuple(x+y for x,y in zip(a,b))
def _mul(a,k): return tuple(x*k for x in a)
def _dot(a,b): return sum(x*y for x,y in zip(a,b))
def _cross(a,b): return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def _unit(a): return _mul(a,1/math.sqrt(_dot(a,a)))


def wedge_frames(a,b,c):
    """A triangle as two right-angled WedgeParts: [(centre, height, length, right, up, back)].
    The triangle lies in each wedge's local YZ plane, with the right angle on the longest edge."""
    p,q,r=max(((a,b,c),(b,c,a),(c,a,b)),key=lambda e:_dot(_sub(e[1],e[0]),_sub(e[1],e[0])))
    base=_sub(q,p); foot=_add(p,_mul(base,_dot(_sub(r,p),base)/_dot(base,base)))
    frames=[]
    for end in (p,q):
        leg,rise=_sub(end,foot),_sub(r,foot)
        length,height=math.sqrt(_dot(leg,leg)),math.sqrt(_dot(rise,rise))
        if length<0.01 or height<0.01: continue
        up=_unit(rise); along=_unit(leg)
        back=along if WEDGE_FLIP else _mul(along,-1)
        frames.append((_add(foot,_add(_mul(up,height/2),_mul(along,length/2))),height,length,_cross(up,back),up,back))
    return frames


def _set_frame(node,center,right,up,back):
    cf=node.find("Properties/CoordinateFrame[@name='CFrame']")
    values=(*center,right[0],up[0],back[0],right[1],up[1],back[1],right[2],up[2],back[2])
    for k,v in zip(('X','Y','Z','R00','R01','R02','R10','R11','R12','R20','R21','R22'),values):
        cf.find(k).text=str(round(v,9)+0.0)


def _toward(dx,dz):
    """Yaw that turns a WedgePart's tall face toward (dx, dz)."""
    return math.atan2(dx,dz) if not WEDGE_FLIP else math.atan2(-dx,-dz)


def build_academy(parent, kit, points):
    """kit carries the shared world builders from tools/build.py: part, model, sign, light, glazing and tree."""
    part,model=kit.part,kit.model
    rng=random.Random(5207)   # the academy's own stream, so it never moves forest trees or village props
    def glazing(): return kit.glazing(1,3)   # one academy window in three lights up at night

    def tri(group,name,a,b,c,color,material,thick,**kw):
        for center,height,length,right,up,back in wedge_frames(a,b,c):
            w=part(group,name,center,(thick,round(height,4),round(length,4)),color,material,cls='WedgePart',**kw)
            _set_frame(w,center,right,up,back)

    def spire(group,x,z,base,radius,height,color,material,sides=8):
        apex=(x,base+height,z)
        ring=[(x+radius*math.cos(math.tau*(i+0.5)/sides),base,z+radius*math.sin(math.tau*(i+0.5)/sides)) for i in range(sides)]
        for i in range(sides): tri(group,'Spire',ring[i],ring[(i+1)%sides],apex,color,material,0.4,**TRIM)

    def lantern(group,pos,size,reach,**kw):
        """A night light: glass by day, glowing with a warm light after dark (WorldService)."""
        kit.light(part(group,'Lantern',pos,size,LAMPLIGHT,'Glass',**kw,**TRIM),1.2,reach)

    def box(group,name,x0,x1,z0,z1,y0,y1,color,material='Slate',**kw):
        return part(group,name,((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),(x1-x0,y1-y0,z1-z0),color,material,**kw)

    def frame_for(axis,fixed):
        def at(u,off,y): return (u,y,fixed+off) if axis=='x' else (fixed+off,y,u)
        def dims(along,tall,deep): return (along,tall,deep) if axis=='x' else (deep,tall,along)
        return at,dims

    def lancet(group,axis,fixed,u,y0,w,h):
        """Pointed window through the wall: limestone surround, glass and a pointed glass head."""
        at,dims=frame_for(axis,fixed); name,color=glazing()
        part(group,'Window surround',at(u,0,y0+h/2+0.2),dims(w+1.2,h+0.8,1.3),LIMESTONE,'Limestone',**TRIM)
        part(group,name,at(u,0,y0+h/2),dims(w,h,1.5),color,'Glass',**TRIM)
        tri(group,name,at(u-w/2,0,y0+h),at(u+w/2,0,y0+h),at(u,0,y0+h+w*0.8),color,'Glass',1.5,**TRIM)

    def plaque(group,title,x,y,z,facing):
        """A wall sign in the village style: lettering on a timber board, facing 'n', 's', 'e' or 'w'."""
        yaw={'n':0,'s':math.pi,'e':-math.pi/2,'w':math.pi/2}[facing]   # turns the board's lettered -Z face outward
        kit.sign(part(group,'Sign',(x,y,z),(max(7,0.8*len(title)),1.6,0.2),BEAM,'Wood',yaw=yaw,**TRIM),title)

    def walls(group,x0,x1,z0,z1,base,height,doors,win=(3,9),spacing=13,buttresses=False,skip=()):
        """1-stud walls standing on `base`, with 10-stud door arches 14 high, lancets, string course and cornice.
        doors maps a side ('n', 's', 'w', 'e') to door centres along it."""
        top=base+height+0.4
        for key,(axis,fixed,a,b,out) in {'n':('x',z0,x0,x1,-1),'s':('x',z1,x0,x1,1),'w':('z',x0,z0,z1,-1),'e':('z',x1,z0,z1,1)}.items():
            if key in skip: continue
            at,dims=frame_for(axis,fixed); cursor=a; spans=[]
            for d in sorted(doors.get(key,[])):
                spans.append((cursor,d-5)); cursor=d+5
                part(group,'Door arch lintel',at(d,0,(base+14+top)/2),dims(10,top-base-14,1),CASTLE_STONE,'Slate')
            spans.append((cursor,b))
            for s,e in spans:
                if e-s<=0.01: continue
                part(group,'Stone wall',at((s+e)/2,0,(base+top)/2),dims(e-s,top-base,1),CASTLE_STONE,'Slate')
                part(group,'String course',at((s+e)/2,out*0.7,base+6.4),dims(e-s,0.5,0.4),LIMESTONE,'Limestone',**TRIM)
                count=int((e-s)//spacing)
                for k in range(count): lancet(group,axis,fixed,s+(k+0.5)*(e-s)/count,base+7,*win)
                if buttresses and count>1:
                    for k in range(1,count):
                        part(group,'Buttress',at(s+k*(e-s)/count,out*1.5,base+height*0.4),dims(2.2,height*0.8,2),CASTLE_STONE,'Slate')
            part(group,'Cornice',at((a+b)/2,out*0.85,top-0.4),dims(b-a,0.8,0.7),LIMESTONE,'Limestone',**TRIM)
        return top

    def gable_roof(group,x0,x1,z0,z1,top,color,axis,gables=CASTLE_STONE,material='Slate'):
        """Steep roof with its ridge along `axis`; the slabs' underside meets the wall top on the inner face and
        the eaves drop past it. Stone gables close both ends."""
        slope=math.atan(PITCH); cx=(x0+x1)/2; cz=(z0+z1)/2
        span,length=(x1-x0,z1-z0) if axis=='z' else (z1-z0,x1-x0)
        half_in=span/2; half=half_in+1.5; sit=0.5/math.cos(slope); depth=length+3
        apex=top+half_in*PITCH; y=top+sit+(half_in-half/2)*PITCH; hyp=round(math.hypot(half,half*PITCH),4)
        for side in (-1,1):
            if axis=='z': part(group,'Slate roof',(cx+side*half/2,y,cz),(hyp,1,depth),color,material,roll=-side*slope)
            else: part(group,'Slate roof',(cx,y,cz+side*half/2),(depth,1,hyp),color,material,pitch=side*slope)
        if axis=='z':
            part(group,'Roof ridge',(cx,apex+2*sit,cz),(1.2,0.8,depth+0.2),RIDGE,'Slate',**TRIM)
            for z in (z0,z1): tri(group,'Gable',(x0,top,z),(x1,top,z),(cx,apex,z),gables,material,1)
        else:
            part(group,'Roof ridge',(cx,apex+2*sit,cz),(depth+0.2,0.8,1.2),RIDGE,'Slate',**TRIM)
            for x in (x0,x1): tri(group,'Gable',(x,top,z0),(x,top,z1),(x,apex,cz),gables,material,1)
        return apex

    def hall(group,name,rect,base,height,doors,roof=SLATE,axis=None,**kw):
        """A free-standing hall: floor, walls, roof and one warm light."""
        x0,x1,z0,z1=rect; g=model(group,name)
        box(g,'Floor',x0,x1,z0,z1,base+0.2,base+0.4,(137,142,148),'Marble')
        top=walls(g,x0,x1,z0,z1,base,height,doors,**kw)
        axis=axis or ('x' if x1-x0>=z1-z0 else 'z')
        apex=gable_roof(g,x0,x1,z0,z1,top,roof,axis)
        lantern(g,((x0+x1)/2,top-3,(z0+z1)/2),(2,1,2),40)
        return g,top,apex

    def terrace(group,name,x0,x1,z0,z1,top,arches='',pointed=''):
        """A solid stone terrace with a cornice, a cobbled base course, paving and a blind arcade on its faces.
        Arches on the faces listed in `pointed` get pointed heads."""
        box(group,name,x0,x1,z0,z1,0,top,CASTLE_STONE,'Slate')
        box(group,'Terrace paving',x0+0.5,x1-0.5,z0+0.5,z1-0.5,top,top+0.1,PLAZA,'Cobblestone',**TRIM)
        box(group,'Terrace cornice',x0-0.6,x1+0.6,z0-0.6,z1+0.6,top-1.2,top-0.2,LIMESTONE,'Limestone',**TRIM)
        box(group,'Base course',x0-0.6,x1+0.6,z0-0.6,z1+0.6,0,3,COURSE,'Cobblestone',**TRIM)
        h=min(top-6,16)
        for key in arches:
            axis,fixed,a,b,out={'n':('x',z0,x0,x1,-1),'s':('x',z1,x0,x1,1),'w':('z',x0,z0,z1,-1),'e':('z',x1,z0,z1,1)}[key]
            at,dims=frame_for(axis,fixed); count=max(1,int((b-a)//18))
            for k in range(count):
                u=a+(k+0.5)*(b-a)/count
                part(group,'Blind arch',at(u,out*0.1,3+h/2),dims(8,h,0.3),ARCH_SHADOW,'Slate',**TRIM)
                if key in pointed:
                    tri(group,'Blind arch',at(u-4,out*0.1,3+h),at(u+4,out*0.1,3+h),at(u,out*0.1,3+h+5),ARCH_SHADOW,'Slate',0.3,**TRIM)

    def flight(group,name,axis,lo,hi,start,climb,base,steps,cheek=1.5):
        """`steps` steps of 1-stud rise and 2-stud run across lo..hi. The bottom step's outer edge is at `start`
        and the flight climbs toward `climb` (+1 or -1 along `axis`). Steps are solid down to `base`; a sloped
        string wall and a limestone coping run up each side."""
        m=model(group,name)
        for i in range(steps):
            a,b=sorted((start+climb*2*i,start+climb*2*(i+1)))
            if axis=='z': box(m,'Step',lo,hi,a,b,base,base+i+1,LIMESTONE,'Limestone')
            else: box(m,'Step',a,b,lo,hi,base,base+i+1,LIMESTONE,'Limestone')
        mid=start+climb*steps; slope=math.atan(0.5); run=math.hypot(2*steps,steps)-0.8   # coping stops short of both ends
        for edge in (lo-cheek/2,hi+cheek/2):
            pos=(edge,base+steps/2,mid) if axis=='z' else (mid,base+steps/2,edge)
            yaw=_toward(0,climb) if axis=='z' else _toward(climb,0)
            part(m,'String wall',pos,(cheek,steps,2*steps),CASTLE_STONE,'Slate',cls='WedgePart',yaw=yaw)
            top=(pos[0],base+steps/2+0.8,pos[2])
            if axis=='z': part(m,'Coping',top,(cheek+0.4,0.8,round(run,4)),LIMESTONE,'Limestone',pitch=-climb*slope)
            else: part(m,'Coping',top,(round(run,4),0.8,cheek+0.4),LIMESTONE,'Limestone',roll=climb*slope)
        return m

    def pylon(group,x,z,base,h):
        """A stone pylon with a limestone cap and a lantern that lights after dark."""
        box(group,'Pylon',x-2.5,x+2.5,z-2.5,z+2.5,base,base+h,CASTLE_STONE,'Slate')
        box(group,'Pylon cap',x-3,x+3,z-3,z+3,base+h,base+h+1,LIMESTONE,'Limestone')
        lantern(group,(x,base+h+2.2,z),(2.4,2.4,2.4),18,shape=0)

    def drum(group,name,x,z,r,base,top,spire_h,color=SLATE,material='Slate',sides=8,slits=3,lantern=False):
        """A round tower: drum, string course, slit windows, corbel table, spire and finial. A lantern adds a
        glazed observatory ring under the spire."""
        m=model(group,name); d=2*r; up=math.pi/2
        part(m,'Tower drum',(x,(base+top)/2,z),(top-base,d,d),CASTLE_STONE,'Slate',shape=2,roll=up)
        part(m,'String course',(x,base+(top-base)*0.55,z),(0.6,d+0.8,d+0.8),LIMESTONE,'Limestone',shape=2,roll=up,**TRIM)
        for i in range(slits):
            a=math.tau*(i/slits+0.25); y=base+(top-base)*(0.3+0.55*i/max(1,slits-1)); glass,tint=glazing()
            part(m,glass,(x+(r-0.15)*math.cos(a),y,z+(r-0.15)*math.sin(a)),(1.4,4,1),tint,'Glass',
                 yaw=math.atan2(math.cos(a),math.sin(a)),**TRIM)
        if lantern:
            part(m,'Lit window',(x,top+3,z),(6,d-1.6,d-1.6),LAMPLIGHT,'Glass',shape=2,roll=up,**TRIM)
            top+=6
        part(m,'Corbel table',(x,top+1,z),(2,d+1.6,d+1.6),LIMESTONE,'Limestone',shape=2,roll=up,**TRIM)
        spire(m,x,z,top+2,(r+0.9)/math.cos(math.pi/sides),spire_h,color,material,sides)
        part(m,'Finial',(x,top+2+spire_h+1.2,z),(0.35,2.6,0.35),IRON,'Metal',**TRIM)
        return m

    def square_tower(group,name,x,z,half,base,top,spire_h,color,material):
        """A square tower with quoins, belfry lancets, pinnacles and a four-sided spire."""
        m=model(group,name); s=2*half
        box(m,'Tower wall',x-half,x+half,z-half,z+half,base,top,CASTLE_STONE,'Slate')
        box(m,'Plinth course',x-half-0.8,x+half+0.8,z-half-0.8,z+half+0.8,base,base+3,COURSE,'Cobblestone',**TRIM)
        for y in (base+(top-base)*0.4,base+(top-base)*0.75):
            box(m,'String course',x-half-0.4,x+half+0.4,z-half-0.4,z+half+0.4,y-0.3,y+0.3,LIMESTONE,'Limestone',**TRIM)
        for dx in (-1,1):
            for dz in (-1,1): part(m,'Quoin',(x+dx*(half-0.1),(base+top)/2,z+dz*(half-0.1)),(1,top-base,1),LIMESTONE,'Limestone',**TRIM)
        for axis,fixed in (('x',z-half),('x',z+half),('z',x-half),('z',x+half)):
            lancet(m,axis,fixed,x if axis=='x' else z,top-26,4,14)
        box(m,'Cornice',x-half-0.8,x+half+0.8,z-half-0.8,z+half+0.8,top,top+1.2,LIMESTONE,'Limestone',**TRIM)
        for dx in (-1,1):
            for dz in (-1,1): part(m,'Pinnacle',(x+dx*(half-0.2),top+3.7,z+dz*(half-0.2)),(1.4,5,1.4),LIMESTONE,'Limestone',**TRIM)
        k=half-0.5; b=top+1.2; apex=(x,b+spire_h,z)
        corners=[(x-k,b,z-k),(x+k,b,z-k),(x+k,b,z+k),(x-k,b,z+k)]
        for i in range(4): tri(m,'Spire',corners[i],corners[(i+1)%4],apex,color,material,0.4,**TRIM)
        part(m,'Finial',(x,b+spire_h+1.2,z),(0.35,2.6,0.35),IRON,'Metal',**TRIM)
        return m

    campus=model(parent,'Ravenmoor Academy')

    # Arrival: plaza and Main Gate where the approach road ends.
    arrival=model(campus,'Arrival')
    x0,x1,n,s=ARRIVAL
    box(arrival,'Arrival plaza',x0,x1,n,s,0,0.4,PLAZA,'Cobblestone')
    for x in (55,115): drum(arrival,'Gate tower',x,-53,6,0,40,20,sides=6)
    gate=box(arrival,'Gate arch',61,109,-58,-48,30,38,CASTLE_STONE,'Slate')
    box(arrival,'Gate cornice',60,110,-58.6,-47.4,38,39,LIMESTONE,'Limestone',**TRIM)
    plaque(arrival,'RAVENMOOR ACADEMY',CX,33,-47.4,'s')
    for x in (41,129): pylon(arrival,x,-113,0,9)

    # Grand Stair: two flights, a landing at 20 studs and bridges out to both classroom wings.
    stair=model(campus,'Grand Stair')
    flight(stair,'Flight one','z',45,125,-110,-1,0,MID)
    x0,x1,n,s=LANDING
    box(stair,'Landing',x0,x1,n,s,0,MID,CASTLE_STONE,'Slate')
    box(stair,'Landing paving',x0+0.5,x1-0.5,n+0.5,s-0.5,MID,MID+0.1,PLAZA,'Cobblestone',**TRIM)
    flight(stair,'Flight two','z',55,115,-180,-1,MID,TOP-MID)
    for x in (49,121):
        pylon(stair,x,-154,MID,10)
        pylon(stair,x,-224,TOP,10)
    for a,b in ((38,45),(125,136)):
        box(stair,'Bridge deck',a,b,-172,-162,MID-3,MID,CASTLE_STONE,'Slate')
        for z0,z1 in ((-172,-171),(-163,-162)): box(stair,'Bridge parapet',a,b,z0,z1,MID,MID+3,LIMESTONE,'Limestone')

    # Classroom wings: five free-standing halls and a fountain court, each with open ground on every side.
    rooms={r[4]:r for r in ROOMS}; wings={}
    for side,(x0,x1,n,s) in WINGS.items():
        wings[side]=wing=model(campus,side+' classroom wing')
        terrace(wing,'Wing terrace',x0,x1,n,s,MID,'sw' if side=='West' else 'se')
        lo=0 if side=='West' else 154
        flight(wing,'Wing stair','z',lo,lo+20,-20,-1,0,MID)
    for school in SCHOOLS:
        xmin,xmax,north,south,name,color=rooms[school+' Classroom']
        g,top,_=hall(wings['West' if xmin<CX else 'East'],name,(xmin,xmax,north,south),MID,22,{'s':[(xmin+xmax)/2]},win=(3,9),spacing=13)
        x,y,z=points['Teacher_'+school]
        part(g,'Blackboard',(x,y+5,z-7),(17,9,0.8),(33,57,55),'Slate')
        part(g,'Spell lane inlay',(x,y-2.57,z+15),(22,0.03,8),color,**TRIM)
        plaque(g,name.upper(),(xmin+xmax)/2,MID+16,south+0.7,'s')
    court=model(wings['East'],'Fountain court')
    part(court,'Fountain basin',(164,MID+0.75,-92),(1.5,16,16),LIMESTONE,'Limestone',shape=2,roll=math.pi/2)
    part(court,'Fountain water',(164,MID+1.55,-92),(0.1,14,14),WATER,'Glass',shape=2,roll=math.pi/2,transparent=0.2,**TRIM)
    box(court,'Fountain column',162.5,165.5,-93.5,-90.5,MID+1.5,MID+8,CASTLE_STONE,'Slate')
    lantern(court,(164,MID+9.2,-92),(2.4,2.4,2.4),18,shape=0)

    # Upper terrace, 40 studs up.
    upper=model(campus,'Upper terrace')
    x0,x1,n,s=UPPER
    terrace(upper,'Upper terrace',x0,x1,n,s,TOP,'swen',pointed='s')
    for a,b in ((x0,55),(115,x1)): box(upper,'Terrace parapet',a,b,s-1.2,s,TOP,TOP+3,LIMESTONE,'Limestone')
    keep,_,_=hall(upper,'Entrance Keep',(65,105,-250,-226),TOP,34,{'s':[CX]},win=(3,9),spacing=12,skip='n')
    plaque(keep,'GREAT HALL',CX,TOP+17,-225.3,'s')
    xmin,xmax,north,south,_,_=rooms['Great Hall']
    great,top,apex=hall(upper,'Great Hall',(xmin,xmax,north,south),TOP,40,{'s':[CX],'w':[-278],'e':[-278]},
                        win=(4,16),spacing=14,buttresses=True)
    part(great,'Rose window surround',(CX,apex-16,south),(1.3,13,13),LIMESTONE,'Limestone',shape=2,yaw=math.pi/2,**TRIM)
    part(great,'Lit window',(CX,apex-16,south),(1.5,11,11),LAMPLIGHT,'Glass',shape=2,yaw=math.pi/2,**TRIM)
    for x in (xmin,xmax): drum(upper,'Hall turret',x,south,6,TOP,112,18,sides=6)
    square_tower(upper,'Rookery Tower',CX,-318,12,TOP,160,44,COPPER,'CorrodedMetal')
    xmin,xmax,north,south,_,_=rooms['Library & Archive']
    library,_,_=hall(upper,'Library & Archive',(xmin,xmax,north,south),TOP,30,{'e':[-268]},win=(3,11),spacing=13,buttresses=True)
    x,y,z=points['Library']
    box(library,'Archive shelf',xmin+0.5,xmin+3.5,z-3.5,z+3.5,TOP+0.4,TOP+10.4,(88,60,40),'Wood')
    plaque(library,'RESTRICTED SHELF',xmin+2,TOP+13,z,'e')
    drum(upper,'Starwatch Tower',158,-282,15,TOP,116,26,COPPER,'CorrodedMetal',slits=4,lantern=True)
    flight(upper,'Back stair','z',105,125,-420,1,0,TOP)

    # House quarters: one walled terrace per house, far apart, each with its own hall, tower, gate and stair.
    houses=model(campus,'House quarters')
    for (house,color),(cx,cz,h) in zip(HOUSES,QUARTERS):
        q=model(houses,house+' quarter'); mx,rect,(tx,tz)=quarter(cx,cz,h)
        terrace(q,'House terrace',cx-45,cx+45,cz-42,cz+42,h,'e' if mx>0 else 'w')
        front=rect[1] if mx>0 else rect[0]
        g,_,_=hall(q,house+' House',rect,h,20,{'e' if mx>0 else 'w':[cz-8]},roof=color,axis='z',spacing=12)
        plaque(g,house.upper()+' COMMON ROOM',front+mx*0.7,h+16,cz-8,'e' if mx>0 else 'w')
        drum(q,house+' Tower',tx,tz,9,h,h+64,30,color,'Slate',slits=4)
        edge=cx+mx*45; inner=edge-mx*5
        for z0,z1 in ((cz-15,cz-10),(cz+10,cz+15)): box(q,'Gate post',min(edge,inner),max(edge,inner),z0,z1,h,h+16,CASTLE_STONE,'Slate')
        box(q,'Gate lintel',min(edge,inner),max(edge,inner),cz-15,cz+15,h+16,h+20,color,'Slate')
        part(q,'House emblem',(cx+mx*20,h+0.15,cz),(0.1,16,16),color,shape=2,roll=math.pi/2,**TRIM)
        flight(q,'House stair','x',cz-10,cz+10,edge+mx*2*h,-mx,0,h)

    # North gardens: two avenues, the garden walk, a glasshouse, hedges and trees.
    gardens=model(campus,'North gardens')
    for a,b,c,d in ((-121,201,-436,-420),(-97,177,-588,-572),(108,122,-572,-436),(193,201,-420,-20),(2,18,-20,10.5)):
        box(gardens,'Campus path',a,b,c,d,0,0.35,ROAD,'Cobblestone')
    box(gardens,'Glasshouse',40,100,-525,-485,0,18,(170,196,190),'Glass',transparent=0.35)
    gable_roof(gardens,40,100,-525,-485,18,(170,196,190),'x',gables=(170,196,190),material='Glass')
    for a,b,c,d in ((132,188,-470,-462),(132,188,-548,-540),(30,100,-470,-462),(30,100,-548,-540)):
        box(gardens,'Hedge',a,b,c,d,0,4,HEDGE,'Grass')
    for x,z in ((150,-505),(170,-505),(-40,-505),(-60,-480),(10,-560),(150,-610),(30,-610),(-30,-460),(230,-505),(-110,-505)):
        kit.tree(gardens,x,z,rng.uniform(0.55,0.8),rng,'Garden tree')
    return campus
