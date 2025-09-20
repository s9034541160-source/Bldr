"""
Test file for letter generation functionality
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import unittest
from core.letter_generator import LetterGenerator
from core.template_manager import TemplateManager

class TestLetterGeneration(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        self.letter_generator = LetterGenerator()
        self.template_manager = TemplateManager()
        
    def test_template_loading(self):
        """Test that templates can be loaded"""
        templates = self.template_manager.get_templates()
        self.assertGreater(len(templates), 0, "Should have at least one template")
        
        # Check that we have the expected construction templates
        template_ids = [t['id'] for t in templates]
        expected_templates = [
            'compliance_sp31',
            'violation_gesn',
            'tender_response_fz44',
            'delay_notice',
            'payment_dispute',
            'safety_incident_sanpin',
            'ecology_ovos_fz7',
            'bim_clash_report',
            'budget_overrun',
            'hr_salary_claim'
        ]
        
        for template_id in expected_templates:
            self.assertIn(template_id, template_ids, f"Missing template: {template_id}")
    
    def test_letter_generation_with_fallback(self):
        """Test letter generation with fallback when LM Studio is not available"""
        # Since we're not running LM Studio, this should use fallback
        template = self.template_manager.get_template('compliance_sp31')
        self.assertIsNotNone(template, "Should be able to get template")
        
        # Check that template has the required fields
        if template is not None:
            self.assertIn('full_text', template, "Template should have full_text field")
            
            letter_text = self.letter_generator.generate_letter_with_lm(
                description="Test violation in concrete work",
                template_text=template['full_text'],
                tone=-0.5,  # Harsh tone
                dryness=0.7,  # Dry
                humanity=0.3,  # Robotic
                length="medium",
                formality="formal"
            )
            
            self.assertIsNotNone(letter_text, "Should generate letter text")
            self.assertIn("Уважаемый", letter_text, "Should contain greeting")
        else:
            self.fail("Template should not be None")
    
    def test_letter_improvement_with_fallback(self):
        """Test letter improvement with fallback when LM Studio is not available"""
        draft = "Уважаемый клиент, у нас проблема с бетоном."
        
        improved_text = self.letter_generator.improve_letter_draft(
            draft=draft,
            description="Concrete quality issues",
            tone=0.5,  # Loyal tone
            dryness=0.3,  # Lively
            humanity=0.8,  # Natural
            length="medium",
            formality="formal"
        )
        
        self.assertIsNotNone(improved_text, "Should improve letter text")
        self.assertIn("бетон", improved_text, "Should contain reference to concrete")

if __name__ == '__main__':
    unittest.main()