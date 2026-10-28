#!/usr/bin/env python3
"""Run Blender scripts from blender/ in the background; they write FBX files to blender/exports/.

    python tools/blender.py                                       show which Blender is used
    python tools/blender.py blender/models/cauldron.py            build one script
    python tools/blender.py "blender/*/*.py" --preview            build every script and render PNG previews

Blender is found from WANDBOUND_BLENDER (the full path to blender.exe), then PATH, then the usual install
folders; the newest version wins. Scripts can `import rbx` (blender/rbx.py) and `from palette import *`.
See blender/README.md for setup and for importing the results into Studio.
"""
import glob
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INSTALLS = [r'%ProgramFiles%\Blender Foundation\Blender*\blender.exe', r'%LOCALAPPDATA%\Programs\Blender Foundation\Blender*\blender.exe',
            r'%ProgramFiles(x86)%\Steam\steamapps\common\Blender\blender.exe', '/Applications/Blender.app/Contents/MacOS/Blender']


def find_blender():
    if os.environ.get('WANDBOUND_BLENDER'): return os.environ['WANDBOUND_BLENDER']
    found = [p for pattern in INSTALLS for p in glob.glob(os.path.expandvars(pattern))]
    version = lambda p: tuple(int(n) for n in re.findall(r'\d+', Path(p).parent.name))
    return shutil.which('blender') or max(found, key=version, default=None)


def main():
    flags = [a for a in sys.argv[1:] if a.startswith('--')]
    scripts = [Path(p) for a in sys.argv[1:] if not a.startswith('--') for p in (sorted(glob.glob(a)) or [a])]
    blender = find_blender()
    if not blender:
        sys.exit('Blender not found. Install Blender 4.2 or newer (blender/README.md), or set WANDBOUND_BLENDER '
                 'to the full path of blender.exe.')
    if not scripts:
        version = subprocess.run([blender, '--version'], capture_output=True, text=True, errors='replace').stdout
        print(f'{blender}\n{version.strip().splitlines()[0] if version.strip() else "(no version reported)"}')
        return
    setup = f'import sys; sys.path[:0] = [{str(ROOT / "blender")!r}, {str(ROOT / "tools")!r}]'
    failed = []
    for script in scripts:
        run = subprocess.run([blender, '--background', '--factory-startup', '--python-exit-code', '1',
                              '--python-expr', setup, '--python', str(script), '--', *flags],
                             capture_output=True, text=True, encoding='utf-8', errors='replace')
        print(f'{script.as_posix()}:')
        if run.returncode:
            # Show Blender's own output, which ends with the Python traceback.
            print('\n'.join((run.stdout + run.stderr).strip().splitlines()[-40:])); failed.append(script)
        else:
            for line in run.stdout.splitlines():
                if line.startswith('[rbx] '): print('  blender/' + line[6:])
    if failed: sys.exit(f'{len(failed)} of {len(scripts)} scripts failed.')


if __name__ == '__main__': main()
