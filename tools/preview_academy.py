#!/usr/bin/env python3
"""Render a floor plan and an exterior from the exported academy's real geometry."""
from pathlib import Path
import xml.etree.ElementTree as ET
import os
os.environ.setdefault("MPLCONFIGDIR","/tmp/ravenmoor-matplotlib")
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from academy import ROOMS
from validate import box, name_of
ROOT=Path(__file__).resolve().parents[1]


def main():
    paper='#f3efe5'; ink='#253546'; gold='#b18b4d'
    fig,ax=plt.subplots(figsize=(11,14),facecolor=paper); ax.set_facecolor(paper)
    ax.add_patch(Rectangle((8,54),172,220,facecolor='#dcd7c9',edgecolor=ink,lw=2))
    for xmin,xmax,north,south,name,color in ROOMS:
        c=tuple(v/255 for v in color)
        ax.add_patch(Rectangle((xmin,-south),xmax-xmin,south-north,facecolor=c,alpha=.28,edgecolor=ink,lw=1.5))
        short=name.replace(' Classroom','\nClassroom').replace(' House','\nCommon room\n& dormitory').replace(' & ','\n& ').replace('Potions Laboratory','Potions\nLaboratory')
        ax.text((xmin+xmax)/2,-(north+south)/2,short,ha='center',va='center',fontsize=9,color=ink,fontweight='semibold')
    # Openings are 10 studs wide, matching the traversable arches in the model.
    for xmin,xmax,north,south,name,_ in ROOMS:
        cx=(xmin+xmax)/2
        portals=[]
        if name=='Great Hall': portals=[('x',85,north),('x',85,south)]+[( 'z',edge,z) for edge in (xmin,xmax) for z in (-91,-132)]
        elif name in ('Infirmary','Potions Laboratory'): portals=[('z',xmax,-91 if name=='Infirmary' else -132)]
        elif name in ('Library & Archive','Staff & Headmaster'): portals=[('z',xmin,-91 if name=='Library & Archive' else -132)]
        else:
            portals=[('x',cx,south)]
            if name.endswith('Classroom'): portals.append(('x',cx,north))
        for axis,x,z in portals:
            if axis=='x': ax.plot([x-5,x+5],[-z,-z],color='#dcd7c9',lw=4,solid_capstyle='butt')
            else: ax.plot([x,x],[-z-5,-z+5],color='#dcd7c9',lw=4,solid_capstyle='butt')
    # Draw furnishings from the actual export, so the plan stays tied to the model.
    tree=ET.parse(ROOT/'world/RavenmoorAcademy.rbxmx')
    for node in tree.findall('.//Item'):
        if node.get('class')!='Part' or name_of(node) not in ('Bed frame','Table','Archive shelf','Blackboard','Dining bench'): continue
        c,h=box(node)
        ax.add_patch(Rectangle((c[0]-h[0],-c[2]-h[2]),h[0]*2,h[2]*2,facecolor='#756654',alpha=.32,edgecolor=ink,lw=.5))
    for y,label in ((149,'SOUTH CLOISTER'),(208,'NORTH CLOISTER')):
        ax.text(93,y,label,ha='center',va='center',fontsize=8,color=ink)
    ax.text(170,176,'EAST\nPASSAGE',ha='center',va='center',fontsize=7,color=ink)
    for a,b in (((85,56),(85,70)),((85,137),(85,146)),((87,154),(87,158)),((87,195),(87,203))):
        ax.annotate('',xy=b,xytext=a,arrowprops=dict(arrowstyle='->',color=gold,lw=2))
    ax.text(85,61,'ENTRANCE COURT',ha='center',fontsize=8,color=ink)
    ax.text(85,125,'◇ Mirror',ha='center',fontsize=8,color=gold)
    ax.text(146,104,'◆ Archive',ha='center',fontsize=8,color=gold)
    ax.set_xlim(-4,194);ax.set_ylim(45,284);ax.set_aspect('equal')
    ax.set_xlabel('World X · studs',color=ink);ax.set_ylabel('North (−world Z) · studs',color=ink)
    ax.tick_params(colors=ink,labelsize=8);ax.spines[['top','right']].set_visible(False)
    fig.suptitle('RAVENMOOR ACADEMY',fontsize=25,fontweight='bold',color=ink,y=.96)
    ax.set_title('14 rooms  •  4 house suites  •  16 student beds\nGround-floor layout · roofs omitted for clarity',fontsize=11,color=ink,pad=18)
    fig.text(.5,.035,'Open archways connect the hall, teaching cloisters and residential wing.\nExisting Mirror, professor and library quest locations are preserved.',ha='center',fontsize=10,color=ink)
    fig.subplots_adjust(top=.88,bottom=.09)
    fig.savefig(ROOT/'docs/academy-floor-plan.png',dpi=170,facecolor=paper);plt.close(fig)
    fig=plt.figure(figsize=(14,10),facecolor=paper);ax=fig.add_subplot(111,projection='3d');ax.set_facecolor(paper)
    faces=[];colors=[]
    for node in tree.findall('.//Item'):
        if node.get('class')!='Part':continue
        cf=node.find("Properties/CoordinateFrame[@name='CFrame']")
        size=node.find("Properties/Vector3[@name='size']")
        center=[float(cf.find(k).text) for k in ('X','Y','Z')]
        half=[float(size.find(k).text)/2 for k in ('X','Y','Z')]
        rot=[[float(cf.find(f'R{i}{j}').text) for j in range(3)] for i in range(3)]
        value=int(node.findtext("Properties/Color3uint8[@name='Color3uint8']"))
        color=((value>>16&255)/255,(value>>8&255)/255,(value&255)/255)
        verts=[]
        for dx,dy,dz in [(-1,-1,1),(1,-1,1),(1,-1,-1),(-1,-1,-1),(-1,1,1),(1,1,1),(1,1,-1),(-1,1,-1)]:
            local=[dx*half[0],dy*half[1],dz*half[2]]
            v=[center[i]+sum(rot[i][j]*local[j] for j in range(3)) for i in range(3)]
            verts.append((v[0],-v[2],v[1]))
        for indexes,shade in [((0,1,5,4),.8),((1,2,6,5),.7),((2,3,7,6),.85),((3,0,4,7),.9),((4,5,6,7),1.0)]:
            faces.append([verts[i] for i in indexes]);colors.append(tuple(v*shade for v in color))
    ax.add_collection3d(Poly3DCollection(faces,facecolors=colors,edgecolors=(.1,.15,.2,.12),linewidths=.2))
    ax.set_xlim(0,190);ax.set_ylim(45,280);ax.set_zlim(0,65);ax.set_box_aspect((190,235,90));ax.view_init(elev=36,azim=-62);ax.set_axis_off()
    fig.suptitle('RAVENMOOR  /  EXPANDED ACADEMY',fontsize=23,color=ink,y=.92)
    fig.text(.5,.10,'Geometry preview of the exported Roblox model\nLantern gate · Great Hall · teaching cloisters · residential wing',ha='center',fontsize=12,color=ink)
    fig.savefig(ROOT/'docs/academy-exterior.png',dpi=160,facecolor=paper,bbox_inches='tight');plt.close(fig)

if __name__=='__main__':main()
