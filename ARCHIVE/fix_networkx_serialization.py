import json
import copy
import networkx as nx

def fix_qdrant_save_error():
    """
    Fixes the NetworkX DiGraph serialization issue in bldr_rag_trainer.py
    by creating a serialization helper function
    """
    # Define the fix to add to the file
    serialization_helper = """
    def _prepare_rubern_for_qdrant(self, rubern_data):
        """
        Prepares Rubern data for serialization by handling NetworkX DiGraph
        """
        # Create a deep copy to avoid modifying the original
        prepared_data = copy.deepcopy(rubern_data)
        
        # Check if 'doc_structure' has a NetworkX graph
        if 'doc_structure' in prepared_data and 'networkx_graph' in prepared_data['doc_structure']:
            # Convert the graph to a dictionary representation
            G = prepared_data['doc_structure']['networkx_graph']
            prepared_data['doc_structure']['graph_nodes'] = list(G.nodes())
            prepared_data['doc_structure']['graph_edges'] = list(G.edges())
            # Remove the actual NetworkX graph object
            del prepared_data['doc_structure']['networkx_graph']
        
        return prepared_data
    """
    
    # Function to fix the save_to_qdrant method
    fixed_save_to_qdrant = """
    def _stage14_save_to_qdrant(self, chunks: List[Dict], embeddings: np.ndarray, 
                           doc_type_res: Dict[str, Any], rubern_data: Dict[str, Any], 
                           quality_score: float, file_hash: str, file_path: str) -> int:
        """
        Stage 14: Save chunks to Qdrant vector database with category tagging
        """
        points = []
        success_count = 0
        
        # Determine category from document type
        doc_type = doc_type_res.get('doc_type', 'unknown')
        doc_subtype = doc_type_res.get('doc_subtype', 'unknown')
        
        # Map document types to categories for Qdrant tagging
        category_mapping = {
            'norms': 'construction',
            'ppr': 'construction',
            'smeta': 'finance',
            'rd': 'construction',
            'educational': 'education',
            'finance': 'finance',
            'safety': 'safety',
            'ecology': 'ecology',
            'accounting': 'finance',
            'hr': 'hr',
            'logistics': 'logistics',
            'procurement': 'procurement',
            'insurance': 'insurance'
        }
        
        # Get primary category
        primary_category = category_mapping.get(doc_type, 'other')
        
        # Get secondary categories based on content analysis
        secondary_categories = self._extract_secondary_categories(chunks, doc_type)
        
        # Combine categories
        all_categories = [primary_category]
        all_categories.extend(secondary_categories)
        # Remove duplicates while preserving order
        all_categories = list(dict.fromkeys(all_categories))
        
        # Prepare Rubern data for serialization (remove NetworkX objects)
        serializable_rubern = self._prepare_rubern_for_qdrant(rubern_data)
        
        for i, (chunk, emb) in enumerate(zip(chunks, embeddings)):
            try:
                point = PointStruct(
                    id=str(uuid.uuid4()),
                    vector=emb.tolist(),
                    payload={
                        'chunk': chunk['chunk'],
                        'meta': chunk['meta'],
                        'hash': hashlib.md5(chunk['chunk'].encode('utf-8')).hexdigest(),
                        'file_hash': file_hash,  # ДОБАВЛЕНО: хеш файла для проверки дубликатов
                        'source_file': file_path,  # ДОБАВЛЕНО: путь к файлу
                        'type': doc_type,
                        'subtype': doc_subtype,
                        'rubern': serializable_rubern,  # Use serializable version
                        'quality': quality_score,
                        'conf': 0.99,
                        'viol': len(chunk['meta'].get('violations', [])) if 'violations' in chunk['meta'] else 0,
                        # Add category tagging for auto-sorting
                        'category': primary_category,
                        'categories': all_categories,
                        'tags': all_categories  # Alternative field name for compatibility
                    }
                )
                points.append(point)
                success_count += 1
            except Exception as e:
                print(f'Error creating point {i}: {e}')
        
        # Batch upsert to Qdrant
        try:
            if points and self.qdrant_client is not None:
                self.qdrant_client.upsert(
                    collection_name='universal_docs',
                    points=points
                )
                
                # Add to FAISS index
                if len(embeddings) > 0 and self.index is not None:
                    self.index.add(embeddings.astype('float32'))
                    faiss.write_index(self.index, self.faiss_path)
        except Exception as e:
            print(f'Qdrant/FAISS save error: {e}')
            success_count = 0
        
        log = f'Upserted {success_count}/{len(chunks)} chunks to Qdrant + FAISS (hybrid) with categories: {all_categories}'
        print(f'✅ [Stage 14/14] Save to Qdrant/FAISS: {log}')
        
        return success_count
    """
    
    # Read the original file
    with open("C:\\Bldr\\scripts\\bldr_rag_trainer.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    # Insert the helper function after the class definition
    insert_pos = content.find("class BldrRAGTrainer:")
    insert_pos = content.find("\n", insert_pos + 20)  # Find the next newline after class def
    
    modified_content = content[:insert_pos] + serialization_helper + content[insert_pos:]
    
    # Replace the _stage14_save_to_qdrant method
    start_marker = "    def _stage14_save_to_qdrant"
    end_marker = "    def _extract_secondary_categories"
    
    start_pos = modified_content.find(start_marker)
    end_pos = modified_content.find(end_marker)
    
    if start_pos != -1 and end_pos != -1:
        method_content = modified_content[start_pos:end_pos]
        modified_content = modified_content.replace(method_content, fixed_save_to_qdrant)
    
    # Write the modified content to a new file
    with open("C:\\Bldr\\scripts\\bldr_rag_trainer_fixed.py", "w", encoding="utf-8") as f:
        f.write(modified_content)
    
    print("✅ Fixed NetworkX serialization issue in BldrRAGTrainer")
    print("✅ Created C:\\Bldr\\scripts\\bldr_rag_trainer_fixed.py")

if __name__ == "__main__":
    fix_qdrant_save_error()