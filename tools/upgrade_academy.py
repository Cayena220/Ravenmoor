#!/usr/bin/env python3
"""Export the academy and update only academy groups in the current place's map.
Run sync_scripts.py --map afterwards to apply the generated map to the place.
Other map groups are copied from the current place, preserving Studio edits.
"""
import copy
import xml.etree.ElementTree as ET
import build
from academy import build_academy


def main():
    root=build.ROOT
    place=ET.parse(root/'Wandbound-Ravenmoor-Academy.rbxlx')
    workspace=place.find("Item[@class='Workspace']")
    world=next(i for i in workspace.findall('Item') if i.findtext("Properties/string[@name='Name']")=='Map')
    world=copy.deepcopy(world)
    removed={'Ravenmoor Academy','Classrooms','Library'}
    for node in list(world.findall('Item')):
        if node.findtext("Properties/string[@name='Name']") in removed: world.remove(node)
    academy=build_academy(world,build.part,build.model,build.label,build.POINTS)
    # Use a distinct deterministic namespace, including lights and GUI descendants.
    for i,node in enumerate(academy.iter('Item')): node.set('referent',f'RBXACADE000{i:024X}')
    for path,node in [('Map.rbxmx',world),('RavenmoorAcademy.rbxmx',academy)]:
        doc=ET.Element('roblox',{'version':'4'}); doc.append(copy.deepcopy(node)); ET.indent(doc,space='  ')
        build.save_xml(doc,root/'world'/path)
    print('Exported academy and updated world/Map.rbxmx; surrounding map groups preserved.')

if __name__=='__main__': main()
