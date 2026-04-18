with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

with open('patch_data_agent.py', 'r', encoding='utf-8') as f:
    patch = f.read()

# Replace lines 2261 to 2649 (0-indexed: 2260 to 2649)
new_lines = lines[:2260] + [patch] + ['\n'] + lines[2649:]

with open('app.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
print('Done padding final app.py')
