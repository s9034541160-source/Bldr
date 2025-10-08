# Script to add template endpoints to bldr_api.py
with open('c:\\Bldr\\core\\bldr_api.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add template endpoints before the main section
template_endpoints = '''
# Template management endpoints
@app.get("/templates")
async def get_templates(category: Optional[str] = None, credentials: dict = Depends(verify_api_token)):
    """Get all templates or templates by category"""
    try:
        from core.template_manager import template_manager
        templates = template_manager.get_templates(category)
        return templates
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get templates: {str(e)}")


@app.post("/templates")
async def create_template(template_data: Dict[str, Any], credentials: dict = Depends(verify_api_token)):
    """Create a new template"""
    try:
        from core.template_manager import template_manager
        template = template_manager.create_template(template_data)
        return template
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create template: {str(e)}")


@app.put("/templates/{template_id}")
async def update_template(template_id: str, template_data: Dict[str, Any], credentials: dict = Depends(verify_api_token)):
    """Update an existing template"""
    try:
        from core.template_manager import template_manager
        template = template_manager.update_template(template_id, template_data)
        return template
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update template: {str(e)}")


@app.delete("/templates/{template_id}")
async def delete_template(template_id: str, credentials: dict = Depends(verify_api_token)):
    """Delete a template"""
    try:
        from core.template_manager import template_manager
        result = template_manager.delete_template(template_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete template: {str(e)}")


# Add main section at the end of the file for proper execution
'''

content = content.replace('# Add main section at the end of the file for proper execution', template_endpoints)

with open('c:\\Bldr\\core\\bldr_api.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Template endpoints added successfully!")