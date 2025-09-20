"""
Test script for the Plugin Manager and plugins
"""

import sys
import os
import json
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.plugin_manager import PluginManager

def test_plugin_manager():
    """Test the Plugin Manager functionality"""
    print("🚀 Testing Plugin Manager...")
    
    # Initialize plugin manager
    plugin_manager = PluginManager("plugins")
    
    # Load all plugins
    loaded_plugins = plugin_manager.load_all_plugins()
    print(f"✅ Loaded {len(loaded_plugins)} plugins: {list(loaded_plugins.keys())}")
    
    # Test plugin listing
    plugin_list = plugin_manager.get_loaded_plugins()
    print(f"📋 Plugin list: {plugin_list}")
    
    # Test third-party integration plugin
    print("\n🧪 Testing Third-Party Integration Plugin...")
    third_party_plugin = loaded_plugins.get("third_party_integration_plugin")
    if third_party_plugin:
        # Configure Google Drive service
        google_drive_config = {
            "client_id": "sample-client-id",
            "client_secret": "sample-client-secret",
            "refresh_token": "sample-refresh-token"
        }
        
        success = third_party_plugin.configure_service("google_drive", google_drive_config)
        print(f"✅ Google Drive configuration: {'Success' if success else 'Failed'}")
        
        # Test document sync
        documents = third_party_plugin.sync_documents("google_drive")
        print(f"📚 Synced {len(documents)} documents from Google Drive")
        
        # Show sample document
        if documents:
            print(f"📄 Sample document: {documents[0]['name']}")
        
        # Test service listing
        services = third_party_plugin.list_configured_services()
        print(f"⚙️ Configured services: {services}")
    else:
        print("❌ Third-party integration plugin not found")
    
    # Test document analyzer plugin
    print("\n🧪 Testing Document Analyzer Plugin...")
    doc_analyzer_plugin = loaded_plugins.get("document_analyzer_plugin")
    if doc_analyzer_plugin:
        # Create sample chunks
        sample_chunks = [
            {
                "chunk": "Согласно СП 45.13330.2017 п. 5.2, все конструкции должны соответствовать требованиям по прочности.",
                "meta": {
                    "entities": {
                        "ORG": ["СП 45.13330.2017"],
                        "MONEY": ["300млн руб."],
                        "PERCENT": ["99%"]
                    },
                    "finances": ["стоимость = 300 млн руб."],
                    "section": "5.2"
                }
            },
            {
                "chunk": "Нарушение требований п. 3.1 может привести к снижению несущей способности конструкции.",
                "meta": {
                    "entities": {
                        "ORG": ["п. 3.1"],
                    },
                    "section": "3.1"
                }
            }
        ]
        
        # Analyze document
        insights = doc_analyzer_plugin.analyze_document(sample_chunks, "norms")
        print(f"🔍 Document analysis completed:")
        print(f"   Total chunks: {insights['total_chunks']}")
        print(f"   Document type: {insights['doc_type']}")
        print(f"   Entities found: {len(insights['entities_found'])} types")
        print(f"   Violations detected: {len(insights['violations'])}")
        print(f"   Key phrases: {insights['key_phrases'][:5]}")
        print(f"   Recommendations: {len(insights['recommendations'])}")
        print(f"   Summary: {insights['summary']}")
    else:
        print("❌ Document analyzer plugin not found")
    
    # Test webhook plugin
    print("\n🧪 Testing Webhook Plugin...")
    webhook_plugin = loaded_plugins.get("webhook_plugin")
    if webhook_plugin:
        # Register a webhook
        success = webhook_plugin.register_webhook(
            "document_added", 
            "https://example.com/webhook", 
            "sample-secret"
        )
        print(f"✅ Webhook registration: {'Success' if success else 'Failed'}")
        
        # List webhooks
        webhooks = webhook_plugin.list_webhooks()
        print(f"🔗 Registered webhooks: {list(webhooks.keys())}")
        
        # Trigger an event
        event_data = {
            "document_id": "doc_12345",
            "document_name": "СП 45.13330.2017.pdf",
            "timestamp": "2025-09-13T10:30:00Z"
        }
        
        results = webhook_plugin.trigger_event("document_added", event_data)
        print(f"🔔 Event triggered with {len(results)} webhook calls")
    else:
        print("❌ Webhook plugin not found")
    
    print("\n🎉 All plugin tests completed!")

def test_api_integration():
    """Test API integration with plugins"""
    print("\n🚀 Testing API Integration...")
    
    # This would normally be tested with actual API calls
    # For now, we'll just show what the API endpoints would do
    
    print("🌐 Plugin API Endpoints:")
    print("   GET  /api/plugins - List all loaded plugins")
    print("   GET  /api/plugins/endpoints - List all registered plugin endpoints")
    print("   POST /api/plugins/endpoints/register - Register a plugin endpoint")
    print("   POST /api/plugins/third-party/configure - Configure a third-party service")
    print("   POST /api/plugins/third-party/sync - Sync documents from a third-party service")
    print("   POST /api/plugins/third-party/upload - Upload a document to a third-party service")
    print("   POST /api/plugins/webhooks/register - Register a webhook")
    print("   GET  /api/plugins/webhooks/list - List all registered webhooks")
    
    print("\n📝 Example API Request for Google Drive Sync:")
    print("""
    POST /api/plugins/third-party/sync
    Content-Type: application/json
    
    {
      "service": "google_drive",
      "credentials": {
        "client_id": "your-client-id",
        "client_secret": "your-client-secret",
        "refresh_token": "your-refresh-token"
      }
    }
    """)
    
    print("✅ API integration test completed!")

if __name__ == "__main__":
    test_plugin_manager()
    test_api_integration()