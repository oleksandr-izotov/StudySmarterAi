import os
import sys
from pathlib import Path
import polib

def compile_messages():
    """
    Compiles .po files to .mo files using polib.
    """
    base_dir = Path(__file__).resolve().parent.parent
    locale_dir = base_dir / 'locale'
    
    print(f"Scanning for .po files in {locale_dir}...")
    
    if not locale_dir.exists():
        print(f"Locale directory {locale_dir} does not exist.")
        return

    # Walk through locale directory
    for polang_dir in locale_dir.iterdir():
        if not polang_dir.is_dir():
            continue
            
        lc_messages = polang_dir / 'LC_MESSAGES'
        if not lc_messages.exists():
            continue
            
        for po_file in lc_messages.glob('*.po'):
            mo_file = po_file.with_suffix('.mo')
            print(f"Compiling {po_file.name} -> {mo_file.name}")
            
            try:
                po = polib.pofile(str(po_file))
                po.save_as_mofile(str(mo_file))
                print(f"Success: {mo_file}")
            except Exception as e:
                print(f"Error compiling {po_file}: {e}")

if __name__ == "__main__":
    compile_messages()
