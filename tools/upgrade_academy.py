#!/usr/bin/env python3
"""Rebuild the academy campus and the map groups it touches; keep every other map group from the place.

Land (the meadow runs north to the house quarters), Lamps (the campus avenues have posts too), Academy
staff (teachers stand on the raised classroom floors), Mirror of Choosing and Ravenmoor Academy are
generated fresh. Groups from earlier academy versions are dropped. All other map groups, Studio edits included, are copied from the current place. Also writes
world/Markers.rbxmx and src/shared/WorldPoints.lua for the moved anchors.
Run sync_scripts.py --map afterwards to apply the map and markers to the place.
"""
import copy
import xml.etree.ElementTree as ET
import build

REPLACED=('Land','Lamps','Academy staff','Mirror of Choosing','Ravenmoor Academy')
RETIRED=('Classrooms','Library')


def name_of(node): return node.findtext("Properties/string[@name='Name']")


def main():
    root=build.ROOT
    place=ET.parse(root/'Wandbound-Ravenmoor-Academy.rbxlx')
    workspace=place.find("Item[@class='Workspace']")
    world=copy.deepcopy(next(i for i in workspace.findall('Item') if name_of(i)=='Map'))
    fresh,markers,_=build.make_world(build.item(ET.Element('roblox'),'Workspace','Workspace'))
    groups={name_of(n):n for n in fresh.findall('Item') if name_of(n) in REPLACED}
    for node in list(world):
        if node.tag!='Item': continue
        name=name_of(node)
        if name in RETIRED: world.remove(node)
        elif name in groups: world.insert(list(world).index(node),groups.pop(name)); world.remove(node)
    for node in groups.values(): world.append(node)
    # A distinct deterministic namespace for every regenerated instance, including lights and GUIs.
    count=0
    for node in world.findall('Item'):
        if name_of(node) in REPLACED:
            for item in node.iter('Item'): item.set('referent',f'RBXCAMPUS{count:023X}'); count+=1
    academy=next(n for n in world.findall('Item') if name_of(n)=='Ravenmoor Academy')
    for path,node in [('Map.rbxmx',world),('RavenmoorAcademy.rbxmx',academy),('Markers.rbxmx',markers)]:
        doc=ET.Element('roblox',{'version':'4'}); doc.append(copy.deepcopy(node)); ET.indent(doc,space='  ')
        build.save_xml(doc,root/'world'/path)
    build.save_text(root/'src/shared/WorldPoints.lua',build.points_lua())
    parts=sum(1 for i in academy.iter('Item') if i.get('class') in ('Part','WedgePart'))
    print(f'Exported the academy campus ({parts} parts), world/Map.rbxmx and world/Markers.rbxmx; other map groups preserved.')


if __name__=='__main__': main()
