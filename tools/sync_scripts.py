#!/usr/bin/env python3
"""Copy src/ scripts (and optionally the world/ Map, Markers and Spawns models) into the .rbxlx
without rebuilding the place.

Works on places saved by build.py or by Roblox Studio. Only script Source text changes and
missing scripts are added to their folders; everything else stays byte for byte. With --map,
Workspace/Map, Workspace/Markers and Workspace/Spawns are also replaced by the ones from
`python tools/build.py --world-only` or `python tools/upgrade_academy.py`, when they differ.

    python tools/sync_scripts.py           update the place (writes a .bak copy first)
    python tools/sync_scripts.py --map     also replace Workspace/Map, Markers and Spawns
    python tools/sync_scripts.py --check   report differences only; exit 1 when out of date
"""
from collections import Counter
from pathlib import Path
import re
import shutil
import sys
import uuid
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
PLACE = ROOT / 'Wandbound-Ravenmoor-Academy.rbxlx'
MAP = ROOT / 'world' / 'Map.rbxmx'
MARKERS = ROOT / 'world' / 'Markers.rbxmx'
SPAWNS = ROOT / 'world' / 'Spawns.rbxmx'
# Same mapping as default.project.json.
FOLDERS = {'shared': 'ReplicatedStorage/Shared', 'server': 'ServerScriptService',
           'serverstorage': 'ServerStorage', 'client': 'StarterPlayer/StarterPlayerScripts'}
TOKEN = re.compile(r'<ProtectedString name="Source">(.*?)</ProtectedString>'
                   r'|<Item class="([^"]+)" referent="[^"]+">|</Item>|<string name="Name">([^<]*)</string>', re.S)


def escape(text):
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def encode(source, cdata):
    if cdata:  # A literal "]]>" must be split across two CDATA sections.
        return '<![CDATA[' + source.replace(']]>', ']]]]><![CDATA[>') + ']]>'
    return escape(source)


def scan(text):
    """Map instance path -> {cls, source span, opening- and closing-tag offsets}."""
    nodes, stack = {}, []
    for m in TOKEN.finditer(text):
        if m.group(2):
            stack.append({'cls': m.group(2), 'name': None, 'source': None, 'open': m.start()})
        elif m.group(0) == '</Item>':
            node = stack.pop()
            node['close'] = m.start()
            nodes['/'.join(n['name'] or '?' for n in stack + [node])] = node
        elif m.group(3) is not None:
            if stack and stack[-1]['name'] is None:
                stack[-1]['name'] = m.group(3)
        elif stack and stack[-1]['source'] is None:
            stack[-1]['source'] = (m.start(1), m.end(1))
    return nodes


def map_signature(item_xml):
    """Every part in a Map item: (class, name, position, size, colour, material), rounded."""
    return signature(ET.fromstring('<r xmlns:xmime="http://www.w3.org/2005/05/xmlmime">' + item_xml + '</r>'))


def signature(root):
    out = Counter()
    for it in root.iter('Item'):
        props = it.find('Properties')
        cf, size = props.find("CoordinateFrame[@name='CFrame']"), props.find("Vector3[@name='size']")
        if cf is None or size is None:
            continue
        out[(it.get('class'), props.find("string[@name='Name']").text,
             tuple(round(float(cf.find(k).text), 2) for k in 'XYZ'),
             tuple(round(float(size.find(k).text), 2) for k in 'XYZ'),
             props.findtext("Color3uint8[@name='Color3uint8']"), props.findtext("token[@name='Material']"))] += 1
    return out


def map_item(path=MAP):
    text = path.read_bytes().decode('utf-8')
    return text[text.index('<Item '):text.rindex('</Item>') + len('</Item>')]


def built_map(path=MAP):
    """A world/ model's item, with fresh referents so they cannot collide with the place's."""
    item = map_item(path)
    fresh = {ref: 'RBX' + uuid.uuid4().hex.upper() for ref in re.findall(r'referent="([^"]+)"', item)}
    item = re.sub(r'referent="([^"]+)"', lambda m: f'referent="{fresh[m.group(1)]}"', item)
    return re.sub(r'(<Ref name="[^"]*">)([^<]+)(</Ref>)', lambda m: m.group(1) + fresh.get(m.group(2), m.group(2)) + m.group(3), item)


def wanted():
    """Yield (instance path, class, source) for every script in src/."""
    for file in sorted((ROOT / 'src').rglob('*.lua')):
        rel = file.relative_to(ROOT / 'src')
        if file.name.endswith('.server.lua'):
            cls, name = 'Script', file.name[:-11]
        elif file.name.endswith('.client.lua'):
            cls, name = 'LocalScript', file.name[:-11]
        else:
            cls, name = 'ModuleScript', file.stem
        parts = [FOLDERS[rel.parts[0]], *rel.parts[1:-1], name]
        yield '/'.join(parts), cls, file.read_bytes().decode('utf-8')


def main():
    check = '--check' in sys.argv
    lock = PLACE.with_name(PLACE.name + '.lock')
    if not check and lock.exists() and '--force' not in sys.argv:
        print(f'Roblox Studio has {PLACE.name} open ({lock.name} exists).')
        print('Save any Studio edits, close the place in Studio, then run this again.')
        print('(If Studio is already closed, the lock is stale: delete it or pass --force.)')
        return 2
    text = PLACE.read_bytes().decode('utf-8')
    nodes = scan(text)
    cdata = '<![CDATA[' in text
    edits, updated, added = [], [], []
    for path, cls, source in wanted():
        node = nodes.get(path)
        if node and node['cls'] == cls and node['source']:
            start, end = node['source']
            current = text[start:end]
            is_cdata = current.startswith('<![CDATA[')
            new = encode(source, is_cdata)
            if current != new:
                edits.append((start, end, new)); updated.append(path)
            continue
        parent = nodes.get(path.rsplit('/', 1)[0])
        if node or not parent:
            raise SystemExit(f'Cannot place {path}: ' + ('found as a ' + node['cls'] if node else 'parent folder missing'))
        name = path.rsplit('/', 1)[1]
        item = (f'<Item class="{cls}" referent="RBX{uuid.uuid4().hex.upper()}"><Properties>'
                f'<string name="Name">{escape(name)}</string>'
                f'<ProtectedString name="Source">{encode(source, cdata)}</ProtectedString>'
                f'</Properties></Item>\n')
        edits.append((parent['close'], parent['close'], item)); added.append(path)
    known = {path for path, _, _ in wanted()}
    extra = [p for p, n in nodes.items() if n['cls'] in ('Script', 'LocalScript', 'ModuleScript') and p not in known]
    map_notes = []
    if '--map' in sys.argv:
        for where, source in (('Workspace/Map', MAP), ('Workspace/Markers', MARKERS), ('Workspace/Spawns', SPAWNS)):
            current = nodes.get(where)
            if not current:
                raise SystemExit(f'Cannot replace {where}: it is missing from the place.')
            start, end = current['open'], current['close'] + len('</Item>')
            old_refs = set(re.findall(r'referent="([^"]+)"', text[start:end]))
            outside = text[:start] + text[end:]
            pointing_in = [ref for ref in re.findall(r'<Ref name="[^"]*">([^<]+)</Ref>', outside) if ref in old_refs]
            inside_scripts = [p for p in extra if p.startswith(where + '/')]
            if pointing_in or inside_scripts:  # Replacing it would silently break or delete these.
                raise SystemExit(f'Not replacing {where}: ' + (f'{len(pointing_in)} references from outside point into it'
                                 if pointing_in else 'it contains scripts: ' + ', '.join(inside_scripts)))
            old, new = map_signature(text[start:end]), map_signature(map_item(source))
            if old != new:
                edits.append((start, end, built_map(source)))
                map_notes.append(f'{where} ({sum(old.values())} parts -> {sum(new.values())} from world/{source.name})')
    map_note = ', '.join(map_notes)
    for path in updated: print('update ', path)
    for path in added: print('add    ', path)
    for note in map_notes: print('replace', note)
    for path in extra: print('kept   ', path, '(only in the place, not in src/)')
    if not edits:
        print('Place already matches src/' + (' and world/Map.rbxmx.' if '--map' in sys.argv else '.'))
        return 0
    if check:
        print(f'{len(updated)} to update, {len(added)} to add' + (', map to replace.' if map_note else '.'))
        return 1
    for start, end, new in sorted(edits, key=lambda e: e[0], reverse=True):
        text = text[:start] + new + text[end:]
    backup = PLACE.with_name(PLACE.name + '.bak')
    shutil.copyfile(PLACE, backup)
    PLACE.write_bytes(text.encode('utf-8'))
    print(f'Updated {len(updated)} and added {len(added)} scripts' + (', and replaced the map,' if map_note else '')
          + f' in {PLACE.name}. Previous version: {backup.name}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
