# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: _stage9_quality_control
# Основной источник: C:\Bldr\enterprise_rag_trainer_full.py
# Дубликаты (для справки):
#   - C:\Bldr\scripts\bldr_rag_trainer.py
#   - C:\Bldr\scripts\optimized_bldr_rag_trainer.py
#================================================================================
    def _stage9_quality_control(self, content: str, doc_type_info: Dict, 
                               structural_data: Dict, sbert_data: Dict, 
                               metadata: DocumentMetadata) -> Dict[str, Any]:
        """STAGE 9: Quality Control"""
        
        logger.info(f"[Stage 9/14] QUALITY CONTROL")
        start_time = time.time()
        
        issues = []
        recommendations = []
        quality_score = 100.0
        
        if doc_type_info['confidence'] < 0.7:
            issues.append(f"Low document type confidence: {doc_type_info['confidence']:.2f}")
            quality_score -= 15
        
        sections_count = len(structural_data.get('sections', []))
        if sections_count < 2:
            issues.append(f"Too few sections found: {sections_count}")
            quality_score -= 20
            recommendations.append("Consider manual section markup")
        
        works_count = len(sbert_data.get('works', []))
        if works_count < 3:
            issues.append(f"Too few works extracted: {works_count}")
            quality_score -= 10
            recommendations.append("Review seed extraction patterns")
        
        if metadata.quality_score < 0.3:
            issues.append(f"Low metadata quality: {metadata.quality_score:.2f}")
            quality_score -= 15
        
        deps_count = len(sbert_data.get('dependencies', []))
        if deps_count == 0 and works_count > 1:
            issues.append("No work dependencies found")
            quality_score -= 5
            recommendations.append("Check dependency extraction logic")
        
        quality_score = max(quality_score, 0.0)
        
        result = {
            'quality_score': quality_score,
            'issues': issues,
            'recommendations': recommendations,
            'stats': {
                'doc_type_confidence': doc_type_info['confidence'],
                'sections_count': sections_count,
                'works_count': works_count,
                'dependencies_count': deps_count,
                'metadata_quality': metadata.quality_score
            }
        }
        
        elapsed = time.time() - start_time
        logger.info(f"[Stage 9/14] COMPLETE - Quality Score: {quality_score:.1f}, "
                   f"Issues: {len(issues)} ({elapsed:.2f}s)")
        
        return result