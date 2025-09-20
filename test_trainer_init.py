import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'scripts'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'core'))

# Test trainer initialization
def test_trainer_initialization():
    try:
        # Import and initialize trainer like in bldr_api.py
        from scripts.bldr_rag_trainer import BldrRAGTrainer
        
        base_dir_env = os.getenv("BASE_DIR", "I:/docs")
        trainer = BldrRAGTrainer(
            base_dir=os.path.join(base_dir_env, "documents"),
            neo4j_uri='neo4j://localhost:7687',
            neo4j_user='neo4j',
            neo4j_pass='neopassword',
            qdrant_path=os.path.join(base_dir_env, 'qdrant_db')
        )
        
        print("✅ BldrRAGTrainer initialized successfully")
        print(f"Trainer type: {type(trainer)}")
        print(f"Tools system type: {type(trainer.tools_system)}")
        
        # Check if tools system has the generate_letter method
        if hasattr(trainer.tools_system, 'tool_methods'):
            print(f"Available tools: {list(trainer.tools_system.tool_methods.keys())}")
            if 'generate_letter' in trainer.tools_system.tool_methods:
                print("✅ generate_letter tool is registered")
            else:
                print("❌ generate_letter tool is NOT registered")
        else:
            print("❌ tool_methods attribute not found")
            
        # Test executing the tool directly
        try:
            tool_args = {
                "template_id": "compliance_sp31",
                "recipient": "Test Recipient",
                "sender": "Test Sender",
                "subject": "Test Subject",
                "compliance_details": ["Test detail 1", "Test detail 2"],
                "violations": ["Test violation 1"]
            }
            
            result = trainer.tools_system.execute_tool("generate_letter", tool_args)
            print(f"Direct tool execution result: {result}")
        except Exception as e:
            print(f"Direct tool execution failed: {e}")
            
    except Exception as e:
        print(f"❌ Failed to initialize BldrRAGTrainer: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_trainer_initialization()