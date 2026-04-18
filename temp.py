import re
with open('app.py', 'r', encoding='utf-8') as f:
    text = f.read()
matches = list(re.finditer('if st.session_state.mode == "DataAgent":', text))
print(f"File size: {len(text)}")
print("Matches:")
for m in matches:
    print(m.start())
