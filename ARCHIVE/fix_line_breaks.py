# Script to fix line breaks in the PATTERNS section
with open('scripts/bldr_rag_trainer.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Fix the line break in the 'rd' line
lines[126] = lines[126].rstrip() + ' ' + lines[127].strip() + '\n'
# Remove the next line
del lines[127]

# Fix the line break in the 'smeta' line
lines[127] = lines[127].rstrip() + ' ' + lines[128].strip() + '\n'
# Remove the next line
del lines[128]

# Write the file back
with open('scripts/bldr_rag_trainer.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print('Fixed line breaks in PATTERNS section')