"""Ravenmoor's modular academy. Coordinates deliberately preserve existing quest anchors.

Rooms, doors and furniture keep their positions, so lessons, sorting and the library work as
before. The exterior follows the build kit: two-tone stone with limestone dressings, stepped
buttresses, lancet windows set through the walls, steep slate roofs with stone gables, round
towers with octagonal spires and a square clock tower. Everything is plain parts and wedges.
"""
import math
import random
import xml.etree.ElementTree as ET

# xmin, xmax, north Z, south Z, purpose, accent
ROOMS = [
    (43,127,-145,-73,'Great Hall',(183,145,79)),
    (9,42,-108,-73,'Infirmary',(99,161,150)),
    (9,42,-145,-109,'Potions Laboratory',(156,116,183)),
    (128,179,-119,-73,'Library & Archive',(86,132,174)),
    (128,179,-145,-120,'Staff & Headmaster',(173,127,92)),
]
SCHOOLS=['Hex','Ward','Charm','Restoration','Alteration']
for i,school in enumerate(SCHOOLS):
    x=29+i*29
    ROOMS.append((x-14,x+14,-199,-153,school+' Classroom',(99,143,163)))
HOUSES=[('Emberclaw',(168,58,55)),('Stoneroot',(192,145,53)),('Skyquill',(63,114,180)),('Nightfang',(55,133,98))]
for i,(house,color) in enumerate(HOUSES):
    x=10+i*42
    ROOMS.append((x,x+40,-273,-217,house+' House',color))

# Build kit palette: wall stone, weathered stone, limestone dressings, plinth, slate, weathered copper.
STONE=(118,114,104); WEATHERED=(96,94,88); DRESSED=(176,166,142); PLINTH=(92,90,84)
SLATE=(54,60,68); RIDGE=(40,44,50); COPPER=(86,124,112); TIMBER=(88,60,40); IRON=(52,54,58); GOLD=(202,160,83)
DARK_GLASS=(58,68,80); WARM_GLASS=(236,178,104)
PITCH=math.tan(math.radians(52))   # roof rise per stud of run
TRIM={'collide':False,'query':False}
# Covered walks between the ranges. A wall that faces a room or one of these is an inside wall.
COVERED=[(8,180,-152.5,-145.5),(8,180,-216,-200),(160,180,-200,-152)]
# name, centre x, z, radius, drum top, spire height, spire colour and material, windows as (bearing°, y).
# Bearings: 0 = east, 90 = south. Windows face away from the rooms each tower is built against.
TOWERS=[
    ('Rookery Tower',185,-68,9,120,30,COPPER,'CorrodedMetal',[(90,20),(30,44),(150,68),(60,92),(120,110)]),
    ('West Tower',3,-68,8,74,26,SLATE,'Slate',[(90,22),(160,40),(200,58),(120,66)]),
    ('Gate Turret',68,-70,4.5,56,15,SLATE,'Slate',[(90,24),(130,40),(50,48)]),
    ('Gate Turret',102,-70,4.5,56,15,SLATE,'Slate',[(90,24),(50,40),(130,48)]),
    ('North-west Tower',7,-276,5,64,17,SLATE,'Slate',[(200,20),(250,40),(160,52)]),
    ('Starwatch Tower',179,-276,5,92,17,COPPER,'CorrodedMetal',[(290,24),(340,48),(20,72)]),
]
CLOCK=(42.5,-66.5,6,84,22)   # centre x, z, half width, wall top, spire height; back face on the front wall
GREAT_WINDOW=(74,96)         # x span kept clear on the hall front for the great window
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


def _open_runs(axis,fixed,out,a,b):
    """Spans of a wall segment whose outer side is open ground, sampled every half stud."""
    rects=[r[:4] for r in ROOMS]+COVERED
    runs=[]; t=a+0.25
    while t<b:
        x,z=(t,fixed+out*2.5) if axis=='x' else (fixed+out*2.5,t)
        if not any(x0<x<x1 and n<z<s for x0,x1,n,s in rects):
            if runs and abs(runs[-1][1]-(t-0.25))<1e-6: runs[-1][1]=t+0.25
            else: runs.append([t-0.25,t+0.25])
        t+=0.5
    return [(s,min(e,b)) for s,e in runs if e-s>=4]


def _free_spans(axis,fixed,a,b):
    """Parts of a facade run not covered by a tower or the great window."""
    blocked=[]
    for _,x,z,r,*_rest in TOWERS:
        near,u=(z,x) if axis=='x' else (x,z)
        if abs(near-fixed)<r+4: blocked.append((u-r-1.5,u+r+1.5))
    cx,cz,half=CLOCK[:3]
    near,u=(cz,cx) if axis=='x' else (cx,cz)
    if abs(near-fixed)<half+6: blocked.append((u-half-1.5,u+half+1.5))
    if axis=='x' and fixed==-73: blocked.append(GREAT_WINDOW)
    spans=[(a,b)]
    for lo,hi in blocked:
        spans=[piece for s,e in spans for piece in ((s,min(e,lo)),(max(s,hi),e)) if piece[1]-piece[0]>0.01]
    return spans


def build_academy(parent, part, model, label, points):
    rng=random.Random(5207)   # the academy's own stream, so it never moves forest trees or village props
    windows=[0]; lights=[0]

    def tri(group,name,a,b,c,color,material,thick,**kw):
        for center,height,length,right,up,back in wedge_frames(a,b,c):
            w=part(group,name,center,(thick,round(height,4),round(length,4)),color,material,cls='WedgePart',**kw)
            _set_frame(w,center,right,up,back)

    def spire(group,x,z,base,radius,height,color,material,sides=8):
        apex=(x,base+height,z)
        ring=[(x+radius*math.cos(math.tau*(i+0.5)/sides),base,z+radius*math.sin(math.tau*(i+0.5)/sides)) for i in range(sides)]
        for i in range(sides): tri(group,'Spire',ring[i],ring[(i+1)%sides],apex,color,material,0.4,**TRIM)

    def lamp(node,brightness,reach):
        lights[0]+=1
        light=ET.SubElement(node,'Item',{'class':'PointLight','referent':f'TEMP_LIGHT_{lights[0]}'})
        props=ET.SubElement(light,'Properties')
        ET.SubElement(props,'string',{'name':'Name'}).text='Warm room light'
        ET.SubElement(props,'float',{'name':'Brightness'}).text=str(brightness)
        ET.SubElement(props,'float',{'name':'Range'}).text=str(reach)
        ET.SubElement(props,'bool',{'name':'Shadows'}).text='false'

    def glazing():
        """One window in three is lit; WorldService switches 'Lit window' parts to Neon at night."""
        windows[0]+=1
        return ('Lit window',WARM_GLASS) if windows[0]%3==1 else ('Window glass',DARK_GLASS)

    def frame_for(axis,fixed):
        def at(u,off,y): return (u,y,fixed+off) if axis=='x' else (fixed+off,y,u)
        def dims(along,tall,deep): return (along,tall,deep) if axis=='x' else (deep,tall,along)
        return at,dims

    def lancet(group,axis,fixed,u,y0,w,h):
        """Pointed window through the wall: limestone surround, glass and a pointed glass head."""
        at,dims=frame_for(axis,fixed); name,color=glazing()
        part(group,'Window surround',at(u,0,y0+h/2+0.2),dims(w+1.2,h+0.8,1.3),DRESSED,'Limestone',**TRIM)
        part(group,name,at(u,0,y0+h/2),dims(w,h,1.5),color,'Glass',**TRIM)
        tri(group,name,at(u-w/2,0,y0+h),at(u+w/2,0,y0+h),at(u,0,y0+h+w*0.8),color,'Glass',1.5,**TRIM)

    def buttress(group,axis,fixed,out,u,top):
        at,dims=frame_for(axis,fixed); low=top*0.45
        o=(0,0,out) if axis=='x' else (out,0,0)
        yaw=math.atan2(o[0],o[2]) if WEDGE_FLIP else math.atan2(-o[0],-o[2])   # tall side against the wall
        part(group,'Buttress',at(u,out*2,low/2),dims(2.6,low,3),STONE,'Slate')
        part(group,'Buttress',at(u,out*1.5,(top-3)/2),dims(2,top-3,2),STONE,'Slate')
        part(group,'Buttress weathering',at(u,out*3,low+0.9),(2.6,1.8,1),DRESSED,'Limestone',yaw=yaw,cls='WedgePart',**TRIM)
        part(group,'Buttress weathering',at(u,out*1.5,top-1.75),(2,2.5,2),DRESSED,'Limestone',yaw=yaw,cls='WedgePart',**TRIM)

    def facade(group,axis,fixed,out,a,b,height,win=(3,10)):
        """Outside face of a wall run: plinth, string course, cornice, weathering, buttresses and windows."""
        at,dims=frame_for(axis,fixed); top=height+0.4; mid=(a+b)/2; run=b-a
        part(group,'Plinth course',at(mid,out*0.9,1.9),dims(run,3,0.8),PLINTH,'Cobblestone',**TRIM)
        part(group,'String course',at(mid,out*0.7,6.4),dims(run,0.5,0.4),DRESSED,'Limestone',**TRIM)
        part(group,'Cornice',at(mid,out*0.85,top-0.4),dims(run,0.8,0.7),DRESSED,'Limestone',**TRIM)
        for _ in range(int(run//10)):   # about one weathered block in four, set just proud of the face
            w,h=rng.uniform(3,7),rng.uniform(2,4.5)
            u=rng.uniform(a+w/2,b-w/2) if run>w else mid
            part(group,'Weathered stone',at(u,out*0.56,rng.uniform(4.5+h/2,top-1.5-h/2)),dims(w,h,0.12),WEATHERED,'Slate',**TRIM)
        for s,e in _free_spans(axis,fixed,a,b):
            bays=max(1,math.ceil((e-s)/16)); width=(e-s)/bays
            if width<6: continue
            for k in range(1,bays): buttress(group,axis,fixed,out,s+k*width,top)
            for k in range(bays): lancet(group,axis,fixed,s+(k+0.5)*width,7,*win)

    def plaque(group,title,x,z,y=11):
        p=part(group,'Room sign',(x,y,z),(7,1,0.3),GOLD,'Metal',collide=False,query=False)
        label(p,title,'',offset=2,distance=48)

    def wall(group,axis,fixed,lo,hi,doors,height,out,win):
        cursor=lo
        def segment(a,b):
            if b<=a: return
            pos=((a+b)/2,height/2+0.4,fixed) if axis=='x' else (fixed,height/2+0.4,(a+b)/2)
            size=(b-a,height,1) if axis=='x' else (1,height,b-a)
            part(group,'Stone wall',pos,size,STONE,'Slate')
            for s,e in _open_runs(axis,fixed,out,a,b): facade(group,axis,fixed,out,s,e,height,win)
        for center in sorted(doors):
            segment(cursor,center-5)
            pos=(center,(height+14)/2+0.4,fixed) if axis=='x' else (fixed,(height+14)/2+0.4,center)
            size=(10,height-14,1) if axis=='x' else (1,height-14,10)
            part(group,'Door arch lintel',pos,size,STONE,'Slate')
            cursor=center+5
        segment(cursor,hi)

    def roof(group,xmin,xmax,north,south,top):
        """Steep slate roof along Z. The slabs' underside meets the wall top on the inner face and the
        eaves drop past it; stone gables close both ends."""
        cx=(xmin+xmax)/2; cz=(north+south)/2; half_in=(xmax-xmin)/2; half=half_in+1.5
        slope=math.atan(PITCH); sit=0.5/math.cos(slope); depth=south-north+3; apex=top+half_in*PITCH
        for side in (-1,1):
            part(group,'Slate roof',(cx+side*half/2,top+sit+(half_in-half/2)*PITCH,cz),
                 (round(math.hypot(half,half*PITCH),4),1,depth),SLATE,'Slate',roll=-side*slope)
        part(group,'Roof ridge',(cx,apex+2*sit,cz),(1.2,0.8,depth+0.2),RIDGE,'Slate',**TRIM)
        for z in (north,south): tri(group,'Gable',(xmin,top,z),(xmax,top,z),(cx,apex,z),STONE,'Slate',1)
        return apex

    def table(group,x,z,w=8,d=5):
        part(group,'Table',(x,2.6,z),(w,0.5,d),TIMBER,'Wood')
        for dx in (-w/2+0.7,w/2-0.7): part(group,'Table support',(x+dx,1.4,z),(0.7,2.4,d-1),TIMBER,'Wood')

    def bed(group,x,z,color):
        part(group,'Bed frame',(x,0.9,z),(6,1,10),TIMBER,'Wood')
        part(group,'Mattress',(x,1.6,z),(5.5,0.6,9),(222,216,193))
        part(group,'House blanket',(x,1.95,z+1),(5.5,0.15,6),color,collide=False,query=False)
        part(group,'Pillow',(x,2,z-3),(4,0.4,2),(239,229,205),collide=False,query=False)

    def round_tower(group,name,x,z,r,top,spire_h,spire_color,spire_material,openings):
        m=model(group,name); d=2*r; up=math.pi/2
        part(m,'Tower drum',(x,top/2,z),(top,d,d),STONE,'Slate',shape=2,roll=up)
        part(m,'Plinth course',(x,1.9,z),(3,d+1.6,d+1.6),PLINTH,'Cobblestone',shape=2,roll=up,**TRIM)
        for y in (round(top*0.35,1),round(top*0.7,1)):
            part(m,'String course',(x,y,z),(0.6,d+0.8,d+0.8),DRESSED,'Limestone',shape=2,roll=up,**TRIM)
        for bearing,y in openings:
            a=math.radians(bearing); glass,color=glazing()
            part(m,glass,(x+(r-0.15)*math.cos(a),y,z+(r-0.15)*math.sin(a)),(1.4,4,1),color,'Glass',
                 yaw=math.atan2(math.cos(a),math.sin(a)),**TRIM)
        base=top
        if name=='Starwatch Tower':   # glazed observatory lantern under the spire
            part(m,'Lit window',(x,top+3,z),(6,d-1.6,d-1.6),WARM_GLASS,'Glass',shape=2,roll=up,**TRIM)
            base+=6
        part(m,'Corbel table',(x,base+1,z),(2,d+1.6,d+1.6),DRESSED,'Limestone',shape=2,roll=up,**TRIM)
        spire(m,x,z,base+2,(r+0.9)/math.cos(math.pi/8),spire_h,spire_color,spire_material)
        part(m,'Finial',(x,base+2+spire_h+1.2,z),(0.35,2.6,0.35),IRON,'Metal',**TRIM)

    def clock_tower(group):
        x,z,half,top,spire_h=CLOCK; m=model(group,'Clock Tower'); s=half*2; face=z+half
        part(m,'Tower wall',(x,top/2,z),(s,top,s),STONE,'Slate')
        part(m,'Plinth course',(x,1.9,z),(s+1.6,3,s+1.6),PLINTH,'Cobblestone',**TRIM)
        for y in (24,52): part(m,'String course',(x,y,z),(s+0.8,0.6,s+0.8),DRESSED,'Limestone',**TRIM)
        for dx in (-1,1):
            for dz in (-1,1): part(m,'Quoin',(x+dx*(half-0.1),top/2,z+dz*(half-0.1)),(1,top,1),DRESSED,'Limestone',**TRIM)
        for y0 in (30,44): lancet(m,'x',face,x,y0,3,8)
        for dx in (-2,2):   # louvred belfry openings on the three free faces
            part(m,'Belfry louvre',(x+dx,top-8,face+0.1),(2.4,9,0.4),(30,34,40),'Slate',**TRIM)
        for side in (-1,1):
            for dz in (-2,2):
                part(m,'Belfry louvre',(x+side*(half+0.1),top-8,z+dz),(0.4,9,2.4),(30,34,40),'Slate',**TRIM)
        dial_y=top-22
        part(m,'Clock bezel',(x,dial_y,face+0.15),(0.4,8,8),GOLD,'Metal',shape=2,yaw=math.pi/2,**TRIM)
        part(m,'Clock dial',(x,dial_y,face+0.3),(0.6,7,7),(232,222,196),'SmoothPlastic',shape=2,yaw=math.pi/2,**TRIM)
        for length,turn in ((2.4,math.radians(60)),(3.2,math.radians(-60))):   # ten past ten
            dx,dy=-math.sin(turn)*length/2,math.cos(turn)*length/2
            part(m,'Clock hand',(x+dx,dial_y+dy,face+0.75),(0.4,length,0.3),IRON,'Metal',roll=turn,**TRIM)
        for side in (-1,1):
            part(m,'Clock bezel',(x+side*(half+0.15),dial_y,z),(0.4,8,8),GOLD,'Metal',shape=2,**TRIM)
            part(m,'Clock dial',(x+side*(half+0.3),dial_y,z),(0.6,7,7),(232,222,196),'SmoothPlastic',shape=2,**TRIM)
        part(m,'Cornice',(x,top+0.6,z),(s+1.6,1.2,s+1.6),DRESSED,'Limestone',**TRIM)
        for dx in (-1,1):
            for dz in (-1,1): part(m,'Pinnacle',(x+dx*(half-0.2),top+3.7,z+dz*(half-0.2)),(1.2,5,1.2),DRESSED,'Limestone',**TRIM)
        k=half-0.5; base=top+1.2; apex=(x,base+spire_h,z)
        corners=[(x-k,base,z-k),(x+k,base,z-k),(x+k,base,z+k),(x-k,base,z+k)]
        for i in range(4): tri(m,'Spire',corners[i],corners[(i+1)%4],apex,SLATE,'Slate',0.4,**TRIM)
        part(m,'Finial',(x,base+spire_h+1.2,z),(0.35,2.6,0.35),IRON,'Metal',**TRIM)

    def great_hall_front(g,top,apex):
        """Gate, great window and rose window on the hall's south gable."""
        z=-73
        for x in (79.6,90.4): part(g,'Gate jamb',(x,7.4,z),(0.8,14,1.6),DRESSED,'Limestone',**TRIM)
        tri(g,'Gate hood',(78.8,14.4,z),(91.2,14.4,z),(85,17.6,z),DRESSED,'Limestone',1.6,**TRIM)
        for x in (80.6,89.4): part(g,'Gate door',(x,7.2,-76),(0.5,13.6,5),TIMBER,'WoodPlanks',**TRIM)
        part(g,'Window surround',(85,33,z),(20,30,1.3),DRESSED,'Limestone',**TRIM)
        part(g,'Lit window',(85,33,z),(17,28,1.5),WARM_GLASS,'Glass',**TRIM)
        tri(g,'Window surround',(75,48,z),(95,48,z),(85,64,z),DRESSED,'Limestone',1.3,**TRIM)
        tri(g,'Lit window',(76.5,47,z),(93.5,47,z),(85,60.6,z),WARM_GLASS,'Glass',1.5,**TRIM)
        for x in (80.75,89.25): part(g,'Mullion',(x,33,z),(0.5,28,1.7),DRESSED,'Limestone',**TRIM)
        part(g,'Mullion',(85,39.5,z),(0.5,41,1.7),DRESSED,'Limestone',**TRIM)
        part(g,'Transom',(85,33,z),(17,0.6,1.7),DRESSED,'Limestone',**TRIM)
        rose=min(70,apex-14)
        part(g,'Rose window surround',(85,rose,z),(1.3,12,12),DRESSED,'Limestone',shape=2,yaw=math.pi/2,**TRIM)
        part(g,'Lit window',(85,rose,z),(1.5,10,10),WARM_GLASS,'Glass',shape=2,yaw=math.pi/2,**TRIM)
        for turn in (0,math.pi/4,math.pi/2,3*math.pi/4):
            part(g,'Tracery',(85,rose,z),(10,0.45,1.7),DRESSED,'Limestone',roll=turn,**TRIM)

    def great_hall_roof(g,top,apex):
        """Open timber roof: king-post trusses, two iron chandeliers and a clerestory over the wings."""
        slope=math.atan(PITCH); run=42; rafter=math.hypot(run,run*PITCH)
        for z in (-87,-101,-115,-129):
            part(g,'Tie beam',(85,top-0.6,z),(84,1.2,1.2),TIMBER,'Wood',**TRIM)
            for side in (-1,1):
                part(g,'Principal rafter',(85+side*run/2,(top+apex)/2-1.1,z),(round(rafter,4),1.2,1.2),TIMBER,'Wood',roll=-side*slope,**TRIM)
            part(g,'King post',(85,(top+apex)/2-0.6,z),(1.2,round(apex-top,4),1.2),TIMBER,'Wood',**TRIM)
        for x in (64,106):
            part(g,'Chandelier chain',(x,28,-101),(0.2,6.4,0.2),IRON,'Metal',**TRIM)
            ring=part(g,'Chandelier',(x,24.6,-101),(0.5,8,8),IRON,'Metal',shape=2,roll=math.pi/2,**TRIM)
            lamp(ring,1.1,40)
            for i in range(6):
                a=math.tau*i/6
                part(g,'Candle',(x+3.6*math.cos(a),25.2,-101+3.6*math.sin(a)),(0.3,0.7,0.3),(255,214,150),'Neon',**TRIM)
        for x in (43,127):
            for z in (-81,-95,-109,-123,-137): lancet(g,'z',x,z,24,3,5.5)

    campus=model(parent,'Ravenmoor Academy')
    part(campus,'Campus foundation',(94,0,-165),(172,0.4,218),(126,135,138),'Cobblestone')
    part(campus,'Entrance court',(85,0.2,-64),(150,0.4,21),(145,148,145),'Cobblestone')
    for xmin,xmax,north,south,name,color in ROOMS:
        g=model(campus,name); cx=(xmin+xmax)/2; cz=(north+south)/2
        doors={'n':[],'s':[],'w':[],'e':[]}
        hall=name=='Great Hall'; height=32 if hall else 22; top=height+0.4
        win=(4,16) if hall else (3,10)
        if hall: doors={'n':[85],'s':[85],'w':[-91,-132],'e':[-91,-132]}
        elif name in ('Infirmary','Potions Laboratory'): doors['e']=[-91 if name=='Infirmary' else -132]
        elif name in ('Library & Archive','Staff & Headmaster'): doors['w']=[-91 if name=='Library & Archive' else -132]
        else: doors['s']=[cx]
        if name.endswith('Classroom'): doors['n']=[cx]
        part(g,'Floor',(cx,0.3,cz),(xmax-xmin,0.2,south-north),(137,142,148),'Marble')
        wall(g,'x',north,xmin,xmax,doors['n'],height,-1,win); wall(g,'x',south,xmin,xmax,doors['s'],height,1,win)
        wall(g,'z',xmin,north,south,doors['w'],height,-1,win); wall(g,'z',xmax,north,south,doors['e'],height,1,win)
        apex=roof(g,xmin,xmax,north,south,top)
        if doors['s']: plaque(g,name,cx,south+0.7)
        else: plaque(g,name,xmin+2 if doors['w'] else xmax-2,doors['w'][0] if doors['w'] else doors['e'][0])
        if hall:
            great_hall_front(g,top,apex); great_hall_roof(g,top,apex)
            for x in (59,111):
                table(g,x,-102,10,28)
                for dx in (-8,8): part(g,'Dining bench',(x+dx,1.1,-102),(2,1,28),TIMBER,'Wood')
            for i,(house,accent) in enumerate(HOUSES):
                part(g,house+' banner',(54+i*21,23,-144),(8,12,0.3),accent,collide=False,query=False)
            plaque(g,'MIRROR OF CHOOSING',85,-139,17)
            continue
        # One low local light per room, to suit the day/night cycle.
        lamp(part(g,'Pendant',(cx,height-3,cz),(2,1,2),GOLD,'Neon',collide=False,query=False),1.3,38)
        if name.endswith('Classroom'):
            school=name.split()[0]; x,_,z=points['Teacher_'+school]
            part(g,'Blackboard',(x,8,z-7),(17,9,0.8),(33,57,55),'Slate')
            table(g,x,-194,12,3)
            part(g,'Spell lane inlay',(x,0.43,-165),(22,0.03,8),color,collide=False,query=False)
        elif name=='Library & Archive':
            for z in (-111,-101,-81):
                part(g,'Archive shelf',(175,5,z),(3,10,7),TIMBER,'Wood')
                for row in range(3): part(g,'Book spines',(172.9,2+row*3,z),(1,2,6),color,collide=False,query=False)
            table(g,160,-88,10,8)
            for x in (153,167): part(g,'Reading bench',(x,1.1,-88),(2,1,8),TIMBER,'Wood')
            plaque(g,'RESTRICTED SHELF',146,-112,12)
        elif name=='Infirmary':
            for z in (-99,-82): bed(g,16,z,(99,161,150))
            table(g,31,-103,8,3)
        elif name=='Potions Laboratory':
            for z in (-137,-116):
                table(g,21,z,14,5)
                part(g,'Brewing basin',(21,3.6,z),(4,1.5,4),IRON,'Metal',shape=0)
                part(g,'Potion',(21,4.4,z),(3,0.1,3),color,'Neon',shape=0,collide=False,query=False)
        elif name=='Staff & Headmaster':
            table(g,166,-137,12,6)
            part(g,'Headmaster chair',(166,2,-142),(4,4,2),TIMBER,'Wood')
            table(g,142,-140,8,4)
        else:
            for x in (xmin+7,xmax-7):
                for z in (-264,-248): bed(g,x,z,color)
            table(g,cx,-230,10,6)
            for x in (cx-8,cx+8): part(g,'Common room bench',(x,1.1,-230),(2,1,8),TIMBER,'Wood')
            plaque(g,'COMMON ROOM / DORMITORY',cx,-240,12)
    corridors=model(campus,'Cloister corridors')
    for z,depth,title in ((-149,7,'SOUTH CLOISTER — CLASSROOMS'),(-208,16,'NORTH CLOISTER — HOUSE DORMITORIES')):
        part(corridors,'Cloister roof',(94,24,z),(172,1,depth),SLATE,'Slate')
        plaque(corridors,title,85,z,18)
    # Classroom row joins the north and south cloisters; the east passage provides a second route.
    part(corridors,'East passage roof',(170,24,-176),(20,1,48),SLATE,'Slate')
    part(corridors,'East boundary wall',(180,11.4,-176),(1,22,66),STONE,'Slate')
    facade(corridors,'z',180,1,-209,-143,22)
    towers=model(campus,'Towers')
    for name,x,z,r,top,spire_h,spire_color,spire_material,openings in TOWERS:
        round_tower(towers,name,x,z,r,top,spire_h,spire_color,spire_material,openings)
    clock_tower(towers)
    plaque(campus,'RAVENMOOR ACADEMY',85,-72,16)
    return campus
