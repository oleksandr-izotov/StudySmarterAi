import os

root = 'locale'
languages = ['en', 'de', 'fr', 'es', 'ru']

for lang in languages:
    path = os.path.join(root, lang, 'LC_MESSAGES', 'django.po')
    if not os.path.exists(path):
        print(f"Skipping {path} (not found)")
        continue
        
    print(f"Processing {path}...")
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    new_lines = []
    skip_next = False
    
    for line in lines:
        if skip_next:
            skip_next = False
            continue
            
        if line.strip().startswith('#~ msgid "Мы отправим'):
            # Found obsolete entry, removing it and the next line
            skip_next = True 
            continue
            
        new_lines.append(line)
        
    with open(path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)

print("Done.")
