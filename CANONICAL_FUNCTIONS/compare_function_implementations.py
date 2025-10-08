# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: compare_function_implementations
# Основной источник: C:\Bldr\full_automatic_duplicate_eliminator.py
# Дубликаты (для справки):
#   - C:\Bldr\semi_automated_duplicate_eliminator.py
#================================================================================
def compare_function_implementations(func_name, primary_file, duplicate_files):
    """Compare implementations and determine if they're similar enough for automatic merging."""
    primary_code, _, _ = extract_function_code(primary_file, func_name)
    
    # Filter out primary file from duplicates
    actual_duplicates = [f for f in duplicate_files if f != primary_file and os.path.exists(f)]
    
    if not actual_duplicates:
        return True, "No duplicates to compare"
    
    # Compare each duplicate with primary
    similar_count = 0
    total_count = len(actual_duplicates)
    
    for dup_file in actual_duplicates:
        dup_code, _, _ = extract_function_code(dup_file, func_name)
        
        # Simple similarity check
        similarity = difflib.SequenceMatcher(None, primary_code, dup_code).ratio()
        
        # If similarity is very high (95%+), consider them similar enough
        if similarity > 0.95:
            similar_count += 1
    
    # If most duplicates are very similar, automatic merge is safe
    similarity_ratio = similar_count / total_count if total_count > 0 else 1
    
    return similarity_ratio > 0.8, f"Similarity ratio: {similarity_ratio:.2f}"