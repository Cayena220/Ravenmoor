#!/usr/bin/env python3
"""Render the academy campus from the exported map's real geometry (optional Pillow dependency).

Writes docs/academy-exterior.png (seen from the south-east) and docs/academy-site-plan.png (straight down,
north up). Parts, wedges and cylinders are drawn as flat-shaded solids in painter's order, so overlapping
shapes can occasionally draw in the wrong order. These are geometry renders, not Studio screenshots.
"""
from pathlib import Path
import math
import xml.etree.ElementTree as ET
from PIL import Image, ImageDraw
from academy import WEDGE_FLIP

ROOT=Path(__file__).resolve().parents[1]
AREA=(-260,340,-40,650)   # east and north limits of what is drawn, in studs
LIGHT=(-0.339,-0.551,0.763)
PAPER=(242,232,207)


def solids(path):
    """(points as (east, north, up), faces, colour) for every visible part in the drawn area."""
    for node in ET.parse(path).getroot().iter('Item'):
        if node.get('class') not in ('Part','WedgePart'): continue
        pr=node.find('Properties'); cf=pr.find("CoordinateFrame[@name='CFrame']"); size=pr.find("Vector3[@name='size']")
        if float(pr.findtext("float[@name='Transparency']") or 0)>0.9: continue
        center=[float(cf.find(k).text) for k in 'XYZ']
        rot=[[float(cf.find(f'R{i}{j}').text) for j in range(3)] for i in range(3)]
        half=[float(size.find(k).text)/2 for k in 'XYZ']
        value=int(pr.findtext("Color3uint8[@name='Color3uint8']") or 0)
        color=((value>>16)&255,(value>>8)&255,value&255)
        if node.get('class')=='WedgePart':   # the tall face is at local +Z unless WEDGE_FLIP
            back=-1 if WEDGE_FLIP else 1
            local=[(-1,-1,-1),(1,-1,-1),(1,-1,1),(-1,-1,1),(-1,1,back),(1,1,back)]
            faces=[(0,1,2,3),(3,2,5,4) if back>0 else (0,1,5,4),(0,4,5,1) if back>0 else (3,4,5,2),(0,3,4),(1,5,2)]
        elif pr.findtext("token[@name='shape']")=='2':   # cylinder along local X, as an octagonal prism
            local=[(end,math.cos(a),math.sin(a)) for end in (-1,1) for a in (math.tau*(k+0.5)/8 for k in range(8))]
            faces=[tuple(range(8)),tuple(range(8,16))]+[(k,(k+1)%8,8+(k+1)%8,8+k) for k in range(8)]
        else:
            local=[(-1,-1,-1),(1,-1,-1),(1,-1,1),(-1,-1,1),(-1,1,-1),(1,1,-1),(1,1,1),(-1,1,1)]
            faces=[(0,1,2,3),(4,7,6,5),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)]
        points=[]
        for l in local:
            q=[l[i]*half[i] for i in range(3)]
            w=[center[i]+sum(rot[i][j]*q[j] for j in range(3)) for i in range(3)]
            points.append((w[0],-w[2],w[1]))
        if any(AREA[0]<p[0]<AREA[1] and AREA[2]<p[1]<AREA[3] for p in points): yield points,faces,color


def render(parts,out,yaw,pitch,width=1900):
    c,s=math.cos(math.radians(yaw)),math.sin(math.radians(yaw)); cp,sp=math.cos(math.radians(pitch)),math.sin(math.radians(pitch))
    view=(cp*s,cp*c,-sp)
    def project(p):
        xr=p[0]*c-p[1]*s; yr=p[0]*s+p[1]*c
        return xr,-(yr*sp+p[2]*cp),yr*cp-p[2]*sp
    polys=[]
    for points,faces,color in parts:
        mean=[sum(p[i] for p in points)/len(points) for i in range(3)]
        flat=max(p[2] for p in points)<=0.6   # ground slabs and paths always sit underneath
        for face in faces:
            fp=[points[i] for i in face]; n=[0,0,0]
            for i in range(len(fp)):
                a,b=fp[i],fp[(i+1)%len(fp)]
                n[0]+=(a[1]-b[1])*(a[2]+b[2]); n[1]+=(a[2]-b[2])*(a[0]+b[0]); n[2]+=(a[0]-b[0])*(a[1]+b[1])
            length=math.sqrt(sum(v*v for v in n)) or 1; n=[v/length for v in n]
            centre=[sum(p[i] for p in fp)/len(fp) for i in range(3)]
            if sum(n[i]*(centre[i]-mean[i]) for i in range(3))<0: n=[-v for v in n]
            if sum(n[i]*view[i] for i in range(3))>-1e-6: continue
            lit=0.6+0.4*max(0,sum(n[i]*LIGHT[i] for i in range(3)))
            pp=[project(p) for p in fp]
            polys.append(((0 if flat else 1,-sum(p[2] for p in pp)/len(pp)),[(p[0],p[1]) for p in pp],tuple(min(255,int(v*lit)) for v in color)))
    polys.sort(key=lambda t:t[0])
    xs=[x for _,pp,_ in polys for x,_ in pp]; ys=[y for _,pp,_ in polys for _,y in pp]
    k=(width-40)/(max(xs)-min(xs)); x0,y0=min(xs)-20/k,min(ys)-20/k
    image=Image.new('RGB',(width,int((max(ys)-y0)*k)+20),PAPER); draw=ImageDraw.Draw(image)
    for _,pp,color in polys: draw.polygon([((x-x0)*k,(y-y0)*k) for x,y in pp],fill=color,outline=color)
    image.save(out)
    print(f'{len(polys)} faces -> {out.relative_to(ROOT)}')


def main():
    parts=list(solids(ROOT/'world/Map.rbxmx'))
    render(parts,ROOT/'docs/academy-exterior.png',-35,34)
    render(parts,ROOT/'docs/academy-site-plan.png',0,90,1400)


if __name__=='__main__': main()
