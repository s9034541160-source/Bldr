# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: find_duplicates
# Основной источник: C:\Bldr\core\norms_scan.py
# Дубликаты (для справки):
#   - C:\Bldr\analyze_duplicates.py
#   - C:\Bldr\find_duplicates.py
#================================================================================
    def find_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Find duplicate documents by hash
        
        Args:
            df: DataFrame with document information
            
        Returns:
            DataFrame with duplicate documents
        """
        # Group by hash and find duplicates
        dup_groups = df.groupby('hash')
        duplicates = []
        
        for h, group in dup_groups:
            if len(group) > 1:
                # Sort by issue date to identify newest
                group_sorted = group.copy()
                group_sorted['sort_date'] = pd.to_datetime(group_sorted['issue_date'], errors='coerce').fillna(pd.Timestamp('1900-01-01'))
                group_sorted = group_sorted.sort_values('sort_date', ascending=False)
                
                # Keep the newest, mark others as duplicates
                newest = group_sorted.iloc[0]
                for _, row in group_sorted.iloc[1:].iterrows():
                    duplicates.append({
                        'hash': h,
                        'kept_path': newest['path'],
                        'deleted_path': row['path'],
                        'kept_name': newest['name'],
                        'deleted_name': row['name'],
                        'kept_date': newest['issue_date'],
                        'deleted_date': row['issue_date']
                    })
        
        return pd.DataFrame(duplicates)