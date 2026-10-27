"""Ravenmoor's modular academy. Coordinates deliberately preserve existing quest anchors."""
import math

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


def build_academy(parent, part, model, label, points):
    stone=(91,101,119); trim=(52,65,83); roof=(42,72,88); gold=(202,160,83); wood=(108,80,57)
    campus=model(parent,'Ravenmoor Academy')
    part(campus,'Campus foundation',(94,0,-165),(172,0.4,218),(126,135,138),'Cobblestone')
    part(campus,'Entrance court',(85,0.2,-64),(150,0.4,21),(145,148,145),'Cobblestone')
    def plaque(group,title,x,z,y=11):
        p=part(group,'Room sign',(x,y,z),(7,1,0.3),gold,'Metal',collide=False,query=False)
        label(p,title,'',offset=2,distance=48)
    def wall(group,axis,fixed,lo,hi,doors,height):
        cursor=lo
        def segment(a,b):
            if b<=a: return
            pos=((a+b)/2,height/2+0.4,fixed) if axis=='x' else (fixed,height/2+0.4,(a+b)/2)
            size=(b-a,height,1) if axis=='x' else (1,height,b-a)
            part(group,'Stone wall',pos,size,stone,'Brick')
        for center in sorted(doors):
            segment(cursor,center-5)
            pos=(center,(height+14)/2+0.4,fixed) if axis=='x' else (fixed,(height+14)/2+0.4,center)
            size=(10,height-14,1) if axis=='x' else (1,height-14,10)
            part(group,'Door arch lintel',pos,size,stone,'Brick')
            cursor=center+5
        segment(cursor,hi)
    def table(group,x,z,w=8,d=5):
        part(group,'Table',(x,2.6,z),(w,0.5,d),wood,'Wood')
        for dx in (-w/2+0.7,w/2-0.7): part(group,'Table support',(x+dx,1.4,z),(0.7,2.4,d-1),wood,'Wood')
    def bed(group,x,z,color):
        part(group,'Bed frame',(x,0.9,z),(6,1,10),wood,'Wood')
        part(group,'Mattress',(x,1.6,z),(5.5,0.6,9),(222,216,193))
        part(group,'House blanket',(x,1.95,z+1),(5.5,0.15,6),color,collide=False,query=False)
        part(group,'Pillow',(x,2,z-3),(4,0.4,2),(239,229,205),collide=False,query=False)
    for xmin,xmax,north,south,name,color in ROOMS:
        g=model(campus,name); cx=(xmin+xmax)/2; cz=(north+south)/2
        doors={'n':[],'s':[],'w':[],'e':[]}
        height=32 if name=='Great Hall' else 22
        if name=='Great Hall': doors={'n':[85],'s':[85],'w':[-91,-132],'e':[-91,-132]}
        elif name in ('Infirmary','Potions Laboratory'): doors['e']=[-91 if name=='Infirmary' else -132]
        elif name in ('Library & Archive','Staff & Headmaster'): doors['w']=[-91 if name=='Library & Archive' else -132]
        else: doors['s']=[cx]
        if name.endswith('Classroom'): doors['n']=[cx]
        part(g,'Floor',(cx,0.3,cz),(xmax-xmin,0.2,south-north),(137,142,148),'Marble')
        wall(g,'x',north,xmin,xmax,doors['n'],height); wall(g,'x',south,xmin,xmax,doors['s'],height)
        wall(g,'z',xmin,north,south,doors['w'],height); wall(g,'z',xmax,north,south,doors['e'],height)
        half_width=(xmax-xmin+2)/2; rise=9 if name=='Great Hall' else 5
        slope=math.atan2(rise,half_width)
        for side in (-1,1):
            part(g,'Pitched slate roof',(cx+side*half_width/2,height+1+rise/2,cz),
                 (math.hypot(half_width,rise),1,south-north+2),roof,'Slate',roll=-side*slope)
        # Luminous clerestory panels and cornices do not obstruct spells or movement.
        for x in (xmin+1,xmax-1):
            part(g,'Clerestory',(x,height-4,cz),(0.2,5,min(18,south-north-12)),color,'Neon',collide=False,query=False)
        part(g,'Brass cornice',(cx,height+1.6,south),(xmax-xmin,0.4,0.5),gold,'Metal',collide=False,query=False)
        if doors['s']: plaque(g,name,cx,south+0.7)
        else: plaque(g,name,xmin+2 if doors['w'] else xmax-2,doors['w'][0] if doors['w'] else doors['e'][0])
        # Actual local lights: one per room, low brightness to suit the day/night cycle.
        light_part=part(g,'Pendant',(cx,height-3,cz),(2,1,2),gold,'Neon',collide=False,query=False)
        # Keep this builder usable with the XML helpers without requiring Roblox APIs.
        import xml.etree.ElementTree as ET
        light=ET.SubElement(light_part,'Item',{'class':'PointLight','referent':'TEMP_LIGHT_'+name})
        props=ET.SubElement(light,'Properties')
        ET.SubElement(props,'string',{'name':'Name'}).text='Warm room light'
        ET.SubElement(props,'float',{'name':'Brightness'}).text='1.3'
        ET.SubElement(props,'float',{'name':'Range'}).text='38'
        ET.SubElement(props,'bool',{'name':'Shadows'}).text='false'
        if name=='Great Hall':
            for x in (59,111):
                table(g,x,-102,10,28)
                for dx in (-8,8): part(g,'Dining bench',(x+dx,1.1,-102),(2,1,28),wood,'Wood')
            for i,(house,accent) in enumerate(HOUSES):
                part(g,house+' banner',(54+i*21,23,-144),(8,12,0.3),accent,collide=False,query=False)
            plaque(g,'MIRROR OF CHOOSING',85,-139,17)
        elif name.endswith('Classroom'):
            school=name.split()[0]; x,_,z=points['Teacher_'+school]
            part(g,'Blackboard',(x,8,z-7),(17,9,0.8),(33,57,55),'Slate')
            table(g,x,-194,12,3)
            part(g,'Spell lane inlay',(x,0.43,-165),(22,0.03,8),color,collide=False,query=False)
        elif name=='Library & Archive':
            for z in (-111,-101,-81):
                part(g,'Archive shelf',(175,5,z),(3,10,7),wood,'Wood')
                for row in range(3): part(g,'Book spines',(172.9,2+row*3,z),(1,2,6),color,collide=False,query=False)
            table(g,160,-88,10,8)
            for x in (153,167): part(g,'Reading bench',(x,1.1,-88),(2,1,8),wood,'Wood')
            plaque(g,'RESTRICTED SHELF',146,-112,12)
        elif name=='Infirmary':
            for z in (-99,-82): bed(g,16,z,(99,161,150))
            table(g,31,-103,8,3)
        elif name=='Potions Laboratory':
            for z in (-137,-116):
                table(g,21,z,14,5)
                part(g,'Brewing basin',(21,3.6,z),(4,1.5,4),trim,'Metal',shape=0)
                part(g,'Potion',(21,4.4,z),(3,0.1,3),color,'Neon',shape=0,collide=False,query=False)
        elif name=='Staff & Headmaster':
            table(g,166,-137,12,6)
            part(g,'Headmaster chair',(166,2,-142),(4,4,2),wood,'Wood')
            table(g,142,-140,8,4)
        else:
            for x in (xmin+7,xmax-7):
                for z in (-264,-248): bed(g,x,z,color)
            table(g,cx,-230,10,6)
            for x in (cx-8,cx+8): part(g,'Common room bench',(x,1.1,-230),(2,1,8),wood,'Wood')
            plaque(g,'COMMON ROOM / DORMITORY',cx,-240,12)
    corridors=model(campus,'Cloister corridors')
    for z,depth,title in ((-149,7,'SOUTH CLOISTER — CLASSROOMS'),(-208,16,'NORTH CLOISTER — HOUSE DORMITORIES')):
        part(corridors,'Cloister roof',(94,24,z),(172,1,depth),roof,'Slate')
        plaque(corridors,title,85,z,18)
    # Classroom row joins the north and south cloisters; the east passage provides a second route.
    part(corridors,'East passage roof',(170,24,-176),(20,1,48),roof,'Slate')
    part(corridors,'East boundary wall',(180,11.4,-176),(1,22,66),stone,'Brick')
    for x in (20,160):
        tower=model(campus,'Entrance lantern tower')
        for dx in (-6,6): part(tower,'Tower pier',(x+dx,20,-63),(3,40,12),stone,'Brick')
        part(tower,'Tower crown',(x,42,-63),(18,4,18),trim,'Slate')
        part(tower,'Lantern',(x,47,-63),(5,6,5),gold,'Neon',collide=False,query=False)
        for dx in (-7,7):
            for dz in (-7,7): part(tower,'Battlement',(x+dx,46,-63+dz),(3,5,3),stone,'Brick')
    for x in (47,65,105,123):
        part(campus,'Entrance buttress',(x,10,-71),(2,20,3),stone,'Brick')
        part(campus,'Stained glass',(x+4 if x<85 else x-4,23,-72.4),(3,9,0.3),gold,'Neon',collide=False,query=False)
    for x in (79.5,90.5): part(campus,'Gate arch trim',(x,7,-72.3),(0.6,14,0.5),gold,'Metal',collide=False,query=False)
    part(campus,'Gate lintel trim',(85,14.5,-72.3),(12,0.8,0.5),gold,'Metal',collide=False,query=False)
    plaque(campus,'RAVENMOOR ACADEMY',85,-72,21)
    return campus
