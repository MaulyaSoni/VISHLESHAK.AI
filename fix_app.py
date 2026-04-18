with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = lines[:1160] + lines[1509:]

with open('app.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
