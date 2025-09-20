# Script to fix indentation in bldr_rag_trainer.py
with open('scripts/bldr_rag_trainer.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Fix the indentation issue on line 127
if len(lines) > 126:
    lines[126] = lines[126].strip() + '\n'

# Write the file back
with open('scripts/bldr_rag_trainer.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print('Fixed indentation in bldr_rag_trainer.py')