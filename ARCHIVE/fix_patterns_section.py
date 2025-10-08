# Script to fix the PATTERNS section in bldr_rag_trainer.py
with open('scripts/bldr_rag_trainer.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Rewrite the PATTERNS section with proper formatting
lines[125] = '        self.PATTERNS = {\n'
lines[126] = "            'norms': {'type_keywords': [r'СП \\d+\\.\\d+', r'п\\. \\d+\\.\\d+', r'ФЗ-\\d+', r'cl\\.\\d+\\.\\d+'], 'seeds': r'п\\. (\\d+\\.\\d+)', 'materials': r'бетон|цемент|сталь \\d+', 'finances': r'стоимость = (\\d+)', 'entities': {'ORG': r'(СП|ФЗ|CL|BIM|OVOS|LSR)', 'MONEY': r'(\\d+млн|руб)', 'DATE': r'\\d{4}-\\d{2}-\\d{2}'}}},\n"
lines[127] = "            'rd': {'type_keywords': [r'рабочая документация', r'проект'], 'seeds': r'раздел (\\d+\\.\\d+)'},\n"
lines[128] = "            'smeta': {'type_keywords': [r'смета', r'расчет'], 'seeds': r'позиция (\\d+)'},\n"
lines[129] = '            # Add more types...\n'
lines[130] = '        }\n'

# Write the file back
with open('scripts/bldr_rag_trainer.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print('Fixed PATTERNS section in bldr_rag_trainer.py')