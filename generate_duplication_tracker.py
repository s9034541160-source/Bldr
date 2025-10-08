import re
import csv
from pathlib import Path

def parse_duplicate_report(report_path):
    with open(report_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Регулярное выражение для поиска блоков функций
    pattern = r"🔸 Function: (.*?)\n\s+Defined in (\d+) files:(.*?)(?=\n🔸 Function:|\Z)"
    matches = re.findall(pattern, content, re.DOTALL)
    
    tracker_data = []
    for func_name, count, file_block in matches:
        func_name = func_name.strip()
        count = int(count.strip())
        # Извлекаем пути файлов
        file_paths = [line.strip().lstrip("- ").strip() for line in file_block.strip().split('\n') if line.strip().startswith('-')]
        tracker_data.append({
            'FunctionName': func_name,
            'FileCount': count,
            'FileList': ';'.join(file_paths),  # Храним как строку, разделенную ";"
            'ChosenPrimaryFile': '',  # Пока пусто
            'Status': 'Pending',
            'Notes': ''
        })
    return tracker_data

def save_to_csv(data, output_path):
    fieldnames = ['FunctionName', 'FileCount', 'FileList', 'ChosenPrimaryFile', 'Status', 'Notes']
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in data:
            writer.writerow(row)

if __name__ == "__main__":
    # Find the most recent duplicate report file
    import os
    import glob
    
    # Find the most recent duplicate report file
    duplicate_reports = glob.glob("duplicate_report_duplicates_*.txt")
    if duplicate_reports:
        # Sort by modification time and get the most recent
        report_file = max(duplicate_reports, key=os.path.getmtime)
        print(f"Using report file: {report_file}")
    else:
        report_file = "duplicate_report_duplicates_20250922_145054.txt"  # Default fallback
    
    output_csv = "duplication_master_list.csv"
    data = parse_duplicate_report(report_file)
    save_to_csv(data, output_csv)
    print(f"✅ Трекер дубликатов создан: {output_csv}")
    print(f"📊 Найдено {len(data)} дублирующихся функций.")