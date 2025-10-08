import warnings
warnings.filterwarnings('ignore')
from sentence_transformers import SentenceTransformer
m = SentenceTransformer('ai-forever/sbert_large_nlu_ru', device='cpu')
print('SBERT_OK', hasattr(m, 'encode'))
emb = m.encode(['тест'])
print('EMB_DIM', len(emb[0]))
