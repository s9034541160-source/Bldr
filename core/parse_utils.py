"""Parse utilities for Bldr Empire v2 using ai-forever/sbert_large_nlu_ru"""

import json
import logging
from typing import Dict, Any, List, Optional
from sentence_transformers import SentenceTransformer, util

logger = logging.getLogger(__name__)

# Load SBERT model once for efficiency
try:
    model = SentenceTransformer('ai-forever/sbert_large_nlu_ru')
    logger.info("✅ SBERT model loaded successfully")
except Exception as e:
    logger.error(f"❌ Failed to load SBERT model: {e}")
    model = None

def parse_intent_and_entities(text: str, task: str = 'intent', labels: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Parse intent and entities from text using SBERT NLU.
    
    Args:
        text: Input text to parse
        task: Task type ('intent', 'entities', or 'similarity')
        labels: Labels for zero-shot classification (for intent task)
        
    Returns:
        Dictionary with parsed results
    """
    if model is None:
        return {'error': 'SBERT model not available'}
    
    try:
        # Embed text
        text_embed = model.encode(text)
        
        if task == 'intent':
            # Default labels for Bldr2 flows
            if labels is None:
                labels = [
                    'norm_check', 'budget_calc', 'letter_gen', 'vl_analysis', 
                    'project_timeline', 'safety_inspection', 'compliance_audit', 
                    'tender_response', 'quality_control', 'risk_assessment'
                ]
            
            # Embed labels and calculate similarities
            label_embeds = model.encode(labels)
            similarities = util.cos_sim(text_embed, label_embeds)[0]
            top_idx = similarities.argmax()
            confidence = similarities[top_idx].item()
            
            # Low confidence fallback
            if confidence < 0.7:
                return {
                    'intent': 'unknown', 
                    'confidence': confidence, 
                    'error': 'Low confidence, fallback to regex'
                }
            
            # Extract entities using similarity to dictionary
            entities = {}
            norm_dict = {
                'СП': 'norm', 'ГЭСН': 'rate', 'ФЗ-44': 'law', 'SanPiN': 'safety',
                'ГОСТ': 'norm', 'СНиП': 'norm', 'ФЗ': 'law', 'Постановление': 'law',
                'Методика': 'method', 'РД': 'doc', 'ВСН': 'norm', 'МГСН': 'norm'
            }
            
            # Check for entities in text
            text_words = text.split()
            for word in text_words:
                # Check if word matches any norm pattern
                for norm_key, norm_type in norm_dict.items():
                    if norm_key in word:
                        # Verify with embedding similarity
                        try:
                            ent_embed = model.encode(word)
                            sims = util.cos_sim(ent_embed, model.encode(list(norm_dict.keys())))[0]
                            max_sim = sims.max().item()
                            if max_sim > 0.8:
                                entities[word] = norm_dict[list(norm_dict.keys())[sims.argmax()]]
                        except Exception:
                            # Fallback to exact match
                            entities[word] = norm_type
            
            return {
                'intent': labels[top_idx], 
                'confidence': confidence, 
                'entities': entities
            }
            
        elif task == 'entities':
            # Pure entity extraction
            entities = {}
            norm_dict = {
                'СП': 'norm', 'ГЭСН': 'rate', 'ФЗ-44': 'law', 'SanPiN': 'safety',
                'ГОСТ': 'norm', 'СНиП': 'norm', 'ФЗ': 'law', 'Постановление': 'law',
                'Методика': 'method', 'РД': 'doc', 'ВСН': 'norm', 'МГСН': 'norm'
            }
            
            # Check for entities in text
            text_words = text.split()
            for word in text_words:
                # Check if word matches any norm pattern
                for norm_key, norm_type in norm_dict.items():
                    if norm_key in word:
                        # Verify with embedding similarity
                        try:
                            ent_embed = model.encode(word)
                            sims = util.cos_sim(ent_embed, model.encode(list(norm_dict.keys())))[0]
                            max_sim = sims.max().item()
                            if max_sim > 0.8:
                                entities[word] = norm_dict[list(norm_dict.keys())[sims.argmax()]]
                        except Exception:
                            # Fallback to exact match
                            entities[word] = norm_type
            
            return {
                'entities': entities,
                'confidence': 0.9 if entities else 0.1
            }
            
        elif task == 'similarity':
            # Calculate similarity between text and labels
            if labels is None:
                return {'error': 'Labels required for similarity task'}
            
            label_embeds = model.encode(labels)
            similarities = util.cos_sim(text_embed, label_embeds)[0]
            
            # Return similarities for all labels
            similarity_dict = {}
            for i, label in enumerate(labels):
                similarity_dict[label] = similarities[i].item()
            
            # Get best match index
            best_match_idx = int(similarities.argmax().item())
            
            return {
                'similarities': similarity_dict,
                'max_similarity': similarities.max().item(),
                'best_match': labels[best_match_idx]
            }
            
        else:
            return {'error': 'Invalid task type'}
            
    except Exception as e:
        logger.error(f"Error in parse_intent_and_entities: {e}")
        return {'error': str(e)}

def parse_request_with_sbert(query: str) -> Dict[str, Any]:
    """
    Parse user request using SBERT for intent and entity extraction.
    
    Args:
        query: User query to parse
        
    Returns:
        Dictionary with parsed intent, entities, and confidence
    """
    if model is None:
        return {'error': 'SBERT model not available'}
    
    try:
        # Parse intent
        intent_result = parse_intent_and_entities(query, task='intent')
        
        # Parse entities
        entities_result = parse_intent_and_entities(query, task='entities')
        
        # Combine results
        result = {
            'query': query,
            'intent': intent_result.get('intent', 'unknown'),
            'confidence': intent_result.get('confidence', 0.0),
            'entities': entities_result.get('entities', {}),
            'parser': 'sbert_large_nlu_ru'
        }
        
        logger.info(f"SBERT parse result: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error parsing request with SBERT: {e}")
        return {'error': str(e)}

# Test function
def test_sbert_parse():
    """Test SBERT parsing with sample queries"""
    test_queries = [
        "Проверь СП31 на фото",
        "Смета ГЭСН Москва",
        "Нарушение СанПиН в тендере FZ-44",
        "Анализ фото сайта на СП31",
        "Бюджет ГЭСН для фундамента",
        "График работ по проекту",
        "Проверка соответствия ГОСТ",
        "Расчет стоимости материалов по ФЗ-44"
    ]
    
    print("Testing SBERT parsing...")
    for query in test_queries:
        result = parse_request_with_sbert(query)
        print(f"Query: {query}")
        print(f"Result: {result}")
        print("-" * 50)

if __name__ == "__main__":
    test_sbert_parse()