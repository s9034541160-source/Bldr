"""
Letter service module - Unified interface for letter generation
"""

import os
from typing import Dict, Any, Optional
from core.letter_generator import LetterGenerator
from core.official_letters import generate_official_letter, get_letter_templates

# Configuration
USE_OFFICIAL_TEMPLATES = os.getenv("LETTER_BACKEND", "lm") == "official"
DEFAULT_LM_MODEL = os.getenv("DEFAULT_LM_MODEL", "llama3")
LM_STUDIO_URL = os.getenv("LM_STUDIO_URL", "http://localhost:1234")

# Initialize generators
_lm_generator = LetterGenerator(LM_STUDIO_URL)
_lm_generator.lm_studio_available = _lm_generator._check_lm_studio_connection()

def generate_letter(description: str, 
                   template_text: str, 
                   project_data: Optional[Dict[str, Any]] = None,
                   tone: float = 0.0,
                   dryness: float = 0.5,
                   humanity: float = 0.7,
                   length: str = "medium",
                   formality: str = "formal") -> str:
    """
    Generate a letter using either LM Studio or official templates
    
    Args:
        description: Description of the issue/problem
        template_text: Template text to use as base
        project_data: Optional project data to include
        tone: Tone parameter (-1 to +1: harsh to loyal)
        dryness: Dryness parameter (0-1: lively to dry)
        humanity: Humanity parameter (0-1: robotic to natural)
        length: Length parameter (short/medium/long)
        formality: Formality parameter (formal/informal)
        
    Returns:
        Generated letter text
    """
    if USE_OFFICIAL_TEMPLATES:
        # Use official templates with Jinja2
        try:
            # Adapt parameters for official letter generation
            data = {
                "content": description,
                "recipient": project_data.get("client", "") if project_data else "",
                "sender": "АО БЛДР",
                "subject": "Официальное письмо",
                "compliance_details": [],
                "violations": project_data.get("violations", []) if project_data else [],
                "budget_details": {},
            }
            # For official templates, we'll use the template_text as the template name
            filename = generate_official_letter("compliance_sp31", data)
            return f"Official letter generated successfully. File: {filename}"
        except Exception as e:
            # Fallback to LM Studio if official templates fail
            print(f"Official template generation failed, falling back to LM Studio: {e}")
            pass
    
    # Use LM Studio
    return _lm_generator.generate_letter_with_lm(
        description=description,
        template_text=template_text,
        project_data=project_data,
        tone=tone,
        dryness=dryness,
        humanity=humanity,
        length=length,
        formality=formality
    )

def improve_letter(draft: str,
                  description: str = "",
                  template_text: str = "",
                  project_data: Optional[Dict[str, Any]] = None,
                  tone: float = 0.0,
                  dryness: float = 0.5,
                  humanity: float = 0.7,
                  length: str = "medium",
                  formality: str = "formal") -> str:
    """
    Improve an existing letter draft
    
    Args:
        draft: Existing letter draft to improve
        description: Description of the issue/problem
        template_text: Template text to use as reference
        project_data: Optional project data to include
        tone: Tone parameter (-1 to +1: harsh to loyal)
        dryness: Dryness parameter (0-1: lively to dry)
        humanity: Humanity parameter (0-1: robotic to natural)
        length: Length parameter (short/medium/long)
        formality: Formality parameter (formal/informal)
        
    Returns:
        Improved letter text
    """
    if USE_OFFICIAL_TEMPLATES:
        # Official templates don't support "improvement" - return draft
        return draft
    
    # Use LM Studio for improvement
    return _lm_generator.improve_letter_draft(
        draft=draft,
        description=description,
        template_text=template_text,
        project_data=project_data,
        tone=tone,
        dryness=dryness,
        humanity=humanity,
        length=length,
        formality=formality
    )

def export_letter_to_docx(letter_text: str, filename: Optional[str] = None) -> str:
    """
    Export letter to DOCX format
    
    Args:
        letter_text: Letter text to export
        filename: Optional filename (will generate if not provided)
        
    Returns:
        Path to the generated DOCX file
    """
    return _lm_generator.export_to_docx(letter_text, filename)

def get_available_templates() -> Dict[str, str]:
    """
    Get available letter templates
    
    Returns:
        Dictionary of template names and descriptions
    """
    if USE_OFFICIAL_TEMPLATES:
        return get_letter_templates()
    else:
        # Return basic templates for LM Studio
        return {
            "compliance_sp31": "Письмо о соответствии СП31",
            "budget_approval": "Письмо о согласовании сметы",
            "work_completion": "Письмо о выполнении работ",
            "technical_spec": "Письмо с техническими спецификациями",
            "contract_proposal": "Договорное предложение"
        }