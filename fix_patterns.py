# Script to fix the PATTERNS section in bldr_rag_trainer.py
with open('scripts/bldr_rag_trainer.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Fix the line break in the regex pattern
lines[126] = "            'rd': {'type_keywords': [r'рабочая документация', r'проект'], 'seeds': r'раздел (\d+\.\d+)'},\n"
lines[127] = "            'smeta': {'type_keywords': [r'смета', r'расчет'], 'seeds': r'позиция (\d+)'},\n"

# Write the file back
with open('scripts/bldr_rag_trainer.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print('Fixed line break in regex pattern in bldr_rag_trainer.py')