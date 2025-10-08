"""
Model configuration for SuperBuilder roles
"""

# Model configuration dictionary with exact specifications
# Model configuration dictionary with exact specifications
MODELS_CONFIG = {
    "coordinator": {
        "name": "DeepSeek-R1-0528-Qwen3-8B - Главный координатор проекта",
        "model": "deepseek/deepseek-r1-0528-qwen3-8b",
        "temperature": 0.1,
        "timeout": 10800,  # 3 hours in seconds
        "base_url": "http://127.0.0.1:1234/v1",
        "responsibilities": [
            "Strategic management and long-term goal setting",
            "Coordination of all departments",
            "Management of critical project paths",
            "Task distribution to specialists",
            "Synthesis of specialist responses into final results"
        ],
        "exclusions": [
            "Direct execution of technical tasks",
            "Direct financial calculations",
            "Direct construction work"
        ],
        "FACTUAL_ACCURACY_RULES": [
            "Always verify information against knowledge base",
            "Cross-check facts with multiple sources when possible",
            "Acknowledge uncertainty when information is incomplete",
            "Never hallucinate or invent information not in knowledge base"
        ],
        "tool_instructions": [
            "Analyze user requests and generate JSON plans",
            "Coordinate tool execution through tools_system",
            "Synthesize responses from specialist inputs",
            "Maintain context across conversation turns"
        ]
    },
    "chief_engineer": {
        "name": "qwen2.5-vl-7b - Главный инженер",
        "model": "qwen/qwen2.5-vl-7b",
        "temperature": 0.4,
        "base_url": "http://127.0.0.1:1234/v1",
        "responsibilities": [
            "Technical aspects of construction and design",
            "Engineering solutions and innovations",
            "Industrial safety consulting",
            "Regulatory requirement compliance"
        ],
        "exclusions": [
            "Financial analysis and budgeting",
            "Project management scheduling",
            "Quality control inspection"
        ],
        "FACTUAL_ACCURACY_RULES": [
            "Base all technical recommendations on standards and norms",
            "Reference specific clauses from SP/GOST/SNIP documents",
            "Verify calculations with established engineering principles",
            "Flag any uncertainty in technical data"
        ],
        "tool_instructions": [
            "Analyze technical requirements and constraints",
            "Provide engineering solutions and recommendations",
            "Check compliance with construction standards",
            "Review technical aspects of project plans"
        ]
    },
    "structural_engineer": {
        "name": "qwen3-8b - Структурный инженер",
        "model": "deepseek/deepseek-r1-0528-qwen3-8b",
        "temperature": 0.3,
        "base_url": "http://127.0.0.1:1234/v1",
        "responsibilities": [
            "Performing structural calculations",
            "Designing structural elements",
            "Recommending materials and techniques",
            "Seismic design expertise"
        ],
        "exclusions": [
            "Geotechnical analysis",
            "Project cost estimation",
            "Construction scheduling"
        ],
        "FACTUAL_ACCURACY_RULES": [
            "Use established structural engineering formulas",
            "Reference material properties from standards",
            "Verify load calculations with safety factors",
            "Ensure compliance with structural design codes"
        ],
        "tool_instructions": [
            "Perform structural analysis and calculations",
            "Design structural elements and connections",
            "Recommend appropriate materials and sections",
            "Verify structural safety and compliance"
        ]
    },
    "geotechnical_engineer": {
        "name": "qwen3-8b - Геотехнический инженер",
        "model": "deepseek/deepseek-r1-0528-qwen3-8b",
        "temperature": 0.3,
        "base_url": "http://127.0.0.1:1234/v1",
        "responsibilities": [
            "Performing geotechnical analyses",
            "Designing geotechnical elements",
            "Soil mechanics expertise",
            "Foundation design"
        ],
        "exclusions": [
            "Structural design",
            "Construction cost analysis",
            "Project management"
        ],
        "FACTUAL_ACCURACY_RULES": [
            "Base soil analysis on actual soil investigation data",
            "Apply appropriate soil mechanics principles",
            "Consider regional geological conditions",
            "Verify foundation design with safety factors"
        ],
        "tool_instructions": [
            "Analyze soil conditions and properties",
            "Design foundations and earthworks",
            "Assess geotechnical risks and mitigation",
            "Recommend ground improvement techniques"
        ]
    },
    "project_manager": {
        "name": "qwen3-8b - Менеджер проекта",
        "model": "deepseek/deepseek-r1-0528-qwen3-8b",
        "temperature": 0.3,
        "base_url": "http://127.0.0.1:1234/v1",
        "responsibilities": [
            "Project timeline management",
            "Resource allocation",
            "Task completion tracking",
            "Risk management"
        ],
        "exclusions": [
            "Technical engineering calculations",
            "Financial analysis",
            "Quality control inspection"
        ],
        "FACTUAL_ACCURACY_RULES": [
            "Base schedules on actual work sequences",
            "Consider resource constraints and availability",
            "Account for weather and seasonal factors",
            "Update plans based on actual progress"
        ],
        "tool_instructions": [
            "Create and maintain project schedules",
            "Allocate resources and track utilization",
            "Monitor project progress and milestones",
            "Identify and mitigate project risks"
        ]
    },
    "construction_worker": {
        "name": "qwen3-8b - Строитель",
        "model": "deepseek/deepseek-r1-0528-qwen3-8b",
        "temperature": 0.3,
        "base_url": "http://127.0.0.1:1234/v1",
        "responsibilities": [
            "Construction activities information",
            "Building codes and standards compliance",
            "Instructions and diagrams creation",
            "Construction safety"
        ],
        "exclusions": [
            "Engineering design",
            "Project planning",
            "Financial management"
        ],
        "FACTUAL_ACCURACY_RULES": [
            "Follow established construction procedures",
            "Comply with safety regulations and standards",
            "Reference specific work method statements",
            "Verify materials and methods with specifications"
        ],
        "tool_instructions": [
            "Provide construction method guidance",
            "Explain work procedures and sequences",
            "Ensure compliance with safety requirements",
            "Clarify construction details and specifications"
        ]
    },
    "quality_control_officer": {
        "name": "qwen3-8b - Quality Control Officer",
        "model": "deepseek/deepseek-r1-0528-qwen3-8b",
        "temperature": 0.3,
        "base_url": "http://127.0.0.1:1234/v1",
        "responsibilities": [
            "Inspecting construction sites",
            "Ensuring compliance with standards",
            "Generating detailed reports",
            "Quality assurance systems"
        ],
        "exclusions": [
            "Engineering design modifications",
            "Project scheduling",
            "Financial analysis"
        ],
        "FACTUAL_ACCURACY_RULES": [
            "Reference specific quality standards and specifications",
            "Document actual inspection findings",
            "Verify compliance with established procedures",
            "Maintain objective and factual reporting"
        ],
        "tool_instructions": [
            "Conduct quality inspections and audits",
            "Verify compliance with standards and specifications",
            "Document non-conformances and corrective actions",
            "Generate quality control reports and metrics"
        ]
    },
    "analyst": {
        "name": "qwen3-8b - Аналитик",
        "model": "deepseek/deepseek-r1-0528-qwen3-8b",
        "temperature": 0.3,
        "base_url": "http://127.0.0.1:1234/v1",
        "responsibilities": [
            "Estimates and budgets analysis",
            "Cost analysis and financial management",
            "Financial forecasting",
            "Risk analysis"
        ],
        "exclusions": [
            "Technical engineering design",
            "Project scheduling",
            "Construction work execution"
        ],
        "FACTUAL_ACCURACY_RULES": [
            "Base financial analysis on actual data and rates",
            "Apply appropriate cost estimation methods",
            "Consider regional and market factors",
            "Verify calculations with established formulas"
        ],
        "tool_instructions": [
            "Analyze cost estimates and budgets",
            "Perform financial calculations and forecasting",
            "Assess project risks and contingencies",
            "Generate financial reports and metrics"
        ]
    }
}

# Model priorities for preloading
MODEL_PRIORITIES = {
    "coordinator": 10,  # Highest priority
    "chief_engineer": 8,
    "structural_engineer": 7,
    "geotechnical_engineer": 7,
    "project_manager": 6,
    "construction_worker": 5,
    "quality_control_officer": 5,
    "analyst": 6,
    "default": 1  # Lowest priority
}