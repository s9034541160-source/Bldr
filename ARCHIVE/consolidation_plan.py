#!/usr/bin/env python3
"""
Consolidation plan for duplicate tools in Bldr Empire v2
"""

def create_consolidation_plan():
    """Create detailed consolidation plan"""
    
    consolidation_plan = {
        # HIGH PRIORITY: Exact duplicates (similarity 1.0)
        "exact_duplicates": [
            {
                "group": "template_management",
                "action": "merge",
                "primary": "get_available_templates",
                "duplicates": ["get_letter_templates"],
                "reason": "100% identical functionality - get available letter templates",
                "implementation": "Keep get_available_templates in letter_service, remove get_letter_templates from official_letters"
            }
        ],
        
        # HIGH PRIORITY: Parse estimate functions (0.7+ similarity)
        "parse_estimate_consolidation": [
            {
                "group": "estimate_parsing",
                "action": "create_unified_parser",
                "primary": "parse_estimate_unified",
                "consolidate": [
                    "parse_gesn_estimate",
                    "parse_excel_estimate", 
                    "parse_csv_estimate",
                    "parse_text_estimate",
                    "parse_batch_estimates"
                ],
                "reason": "All parse different formats of the same data (estimates)",
                "implementation": "Create unified parser with format auto-detection"
            }
        ],
        
        # MEDIUM PRIORITY: Letter generation (0.6+ similarity)
        "letter_generation_consolidation": [
            {
                "group": "letter_generation",
                "action": "merge_with_delegation",
                "primary": "generate_letter",
                "consolidate": ["generate_official_letter"],
                "reason": "Both generate letters, but different engines (LM Studio vs Jinja2)",
                "implementation": "Keep both, but make generate_letter delegate to generate_official_letter for templates"
            }
        ],
        
        # MEDIUM PRIORITY: Schedule/Timeline tools
        "schedule_consolidation": [
            {
                "group": "scheduling",
                "action": "create_unified_scheduler",
                "primary": "generate_construction_schedule",
                "consolidate": [
                    "create_construction_schedule",
                    "generate_timeline",
                    "generate_gantt_tasks",
                    "generate_task_links"
                ],
                "reason": "All create different aspects of project scheduling",
                "implementation": "Create unified scheduler that generates all schedule components"
            }
        ],
        
        # MEDIUM PRIORITY: Resource extraction
        "resource_extraction_consolidation": [
            {
                "group": "resource_extraction", 
                "action": "merge",
                "primary": "extract_resources",
                "consolidate": ["extract_gpp_resources"],
                "reason": "Both extract resources, just for different purposes",
                "implementation": "Merge into single extract_resources with type parameter"
            }
        ],
        
        # LOW PRIORITY: Export functions
        "export_consolidation": [
            {
                "group": "export_functions",
                "action": "create_unified_exporter",
                "primary": "export_document",
                "consolidate": [
                    "export_budget_to_excel",
                    "export_letter_to_docx",
                    "autocad_export"
                ],
                "reason": "All export different data to different formats",
                "implementation": "Create unified exporter with format and data type parameters"
            }
        ],
        
        # LOW PRIORITY: Data extraction
        "data_extraction_consolidation": [
            {
                "group": "data_extraction",
                "action": "create_unified_extractor", 
                "primary": "extract_data_unified",
                "consolidate": [
                    "extract_works_nlp",
                    "extract_construction_data",
                    "extract_financial_data",
                    "extract_gesn_rates_from_text",
                    "extract_document_structure"
                ],
                "reason": "All extract different types of data from documents",
                "implementation": "Create unified extractor with data type parameter"
            }
        ]
    }
    
    return consolidation_plan

def print_consolidation_plan():
    """Print detailed consolidation plan"""
    plan = create_consolidation_plan()
    
    print("🔧 TOOLS CONSOLIDATION PLAN")
    print("=" * 50)
    
    total_tools_to_consolidate = 0
    
    for category, consolidations in plan.items():
        print(f"\n📂 {category.upper().replace('_', ' ')}")
        print("-" * 40)
        
        for consolidation in consolidations:
            group = consolidation["group"]
            action = consolidation["action"]
            primary = consolidation["primary"]
            consolidate = consolidation.get("consolidate", consolidation.get("duplicates", []))
            reason = consolidation["reason"]
            implementation = consolidation["implementation"]
            
            print(f"\n🎯 Group: {group}")
            print(f"   Action: {action}")
            print(f"   Primary: {primary}")
            print(f"   Consolidate: {consolidate}")
            print(f"   Count: {len(consolidate)} tools")
            print(f"   Reason: {reason}")
            print(f"   Implementation: {implementation}")
            
            total_tools_to_consolidate += len(consolidate)
    
    print(f"\n📊 CONSOLIDATION SUMMARY:")
    print(f"   Total tools to consolidate: {total_tools_to_consolidate}")
    print(f"   Estimated reduction: {total_tools_to_consolidate} → ~{len(plan)} unified tools")
    print(f"   Net reduction: ~{total_tools_to_consolidate - len(plan)} tools")
    
    print(f"\n🚀 IMPLEMENTATION PRIORITY:")
    print("1. HIGH: Exact duplicates (immediate merge)")
    print("2. HIGH: Parse estimate consolidation (unified parser)")
    print("3. MEDIUM: Letter generation (delegation pattern)")
    print("4. MEDIUM: Schedule consolidation (unified scheduler)")
    print("5. LOW: Export/extraction consolidation (when needed)")
    
    return plan

if __name__ == "__main__":
    print_consolidation_plan()