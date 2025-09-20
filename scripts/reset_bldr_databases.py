import shutil
import os
from pathlib import Path
from qdrant_client import QdrantClient

dirs_to_clean = ['data/qdrant_db', 'data/faiss_index.index', 'data/reports', 'data/norms_db']
for d in dirs_to_clean:
    if os.path.exists(d):
        shutil.rmtree(d, ignore_errors=True)
qdrant_client = QdrantClient(path='data/qdrant_db')
qdrant_client.delete_collection('universal_docs')  # If exists
print('🚀 Reset complete: Clean DBs for new train!')