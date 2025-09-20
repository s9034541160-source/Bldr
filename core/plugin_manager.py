"""
Plugin Manager for Bldr Empire v2
Handles loading, registering, and managing plugins with real httpx.post webhooks and Google API integration
"""

import os
import importlib.util
import json
import hmac
import hashlib
from typing import Dict, List, Any, Callable
from pathlib import Path

# Try to import httpx for real webhooks
try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False
    httpx = None

# Try to import Google API client
try:
    from googleapiclient.discovery import build
    from google.oauth2 import service_account
    HAS_GOOGLE_API = True
except ImportError:
    HAS_GOOGLE_API = False
    build = None
    service_account = None

class PluginManager:
    def __init__(self, plugins_dir: str = "plugins"):
        """
        Initialize Plugin Manager
        
        Args:
            plugins_dir: Directory containing plugin files
        """
        self.plugins_dir = Path(plugins_dir)
        self.plugins_dir.mkdir(exist_ok=True)
        self.loaded_plugins = {}
        self.webhooks = {}
        self.third_party_configs = {}
        self.plugin_endpoints = {}
        
    def load_all_plugins(self) -> Dict[str, Any]:
        """
        Load all plugins from the plugins directory
        
        Returns:
            Dictionary of loaded plugins
        """
        plugins = {}
        
        # Load all Python files in the plugins directory
        for plugin_file in self.plugins_dir.glob("*.py"):
            if plugin_file.name.startswith("__"):
                continue
                
            try:
                # Load the plugin module
                spec = importlib.util.spec_from_file_location(
                    plugin_file.stem, plugin_file
                )
                if spec is not None and spec.loader is not None:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    # Store the loaded plugin
                    plugins[plugin_file.stem] = module
                    print(f"✅ Loaded plugin: {plugin_file.stem}")
                else:
                    print(f"❌ Failed to create spec for plugin: {plugin_file.stem}")
                
            except Exception as e:
                print(f"❌ Failed to load plugin {plugin_file.name}: {e}")
        
        self.loaded_plugins = plugins
        return self.loaded_plugins
    
    def get_loaded_plugins(self) -> List[str]:
        """
        Get list of loaded plugin names
        
        Returns:
            List of plugin names
        """
        return list(self.loaded_plugins.keys())
    
    def register_webhook(self, event_type: str, callback: Callable) -> None:
        """
        Register a webhook for a specific event type
        
        Args:
            event_type: Type of event (e.g., 'document_added')
            callback: Function to call when event occurs
        """
        if event_type not in self.webhooks:
            self.webhooks[event_type] = []
        self.webhooks[event_type].append(callback)
        print(f"✅ Registered webhook for event: {event_type}")
    
    def trigger_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """
        Trigger an event and call all registered webhooks with real httpx.post
        
        Args:
            event_type: Type of event to trigger
            data: Data to pass to webhook callbacks
        """
        # First, trigger internal callbacks
        if event_type in self.webhooks:
            for callback in self.webhooks[event_type]:
                try:
                    callback(data)
                except Exception as e:
                    print(f"❌ Internal webhook callback error for {event_type}: {e}")
        
        # Then, trigger external webhooks with real httpx.post
        external_webhooks = self.third_party_configs.get("webhooks", [])
        for webhook_config in external_webhooks:
            if webhook_config.get("event_type") == event_type:
                try:
                    # Prepare data for external webhook
                    webhook_data = {
                        "event_type": event_type,
                        "data": data,
                        "timestamp": __import__('time').time()
                    }
                    
                    # Add HMAC signature if secret is provided
                    secret = webhook_config.get("secret")
                    if secret and HAS_HTTPX:
                        signature = hmac.new(
                            secret.encode('utf-8'),
                            json.dumps(webhook_data).encode('utf-8'),
                            hashlib.sha256
                        ).hexdigest()
                        
                        headers = {
                            "Content-Type": "application/json",
                            "X-Signature": f"sha256={signature}"
                        }
                    else:
                        headers = {"Content-Type": "application/json"}
                    
                    # Send real HTTP POST request
                    if HAS_HTTPX:
                        url = webhook_config.get("url")
                        timeout = webhook_config.get("timeout", 30)
                        
                        response = httpx.post(
                            url,
                            json=webhook_data,
                            headers=headers,
                            timeout=timeout
                        )
                        
                        if response.status_code == 200:
                            print(f"✅ External webhook triggered successfully for {event_type}")
                        else:
                            print(f"❌ External webhook failed for {event_type}: {response.status_code}")
                    else:
                        print("⚠️  httpx not available, skipping external webhook")
                        
                except Exception as e:
                    print(f"❌ External webhook error for {event_type}: {e}")
    
    def list_webhooks(self) -> Dict[str, int]:
        """
        List all registered webhooks and their count
        
        Returns:
            Dictionary with event types and count of registered callbacks
        """
        return {event: len(callbacks) for event, callbacks in self.webhooks.items()}
    
    def configure_service(self, service_name: str, credentials: Dict[str, Any]) -> bool:
        """
        Configure a third-party service with real Google API integration
        
        Args:
            service_name: Name of the service (e.g., 'google_drive')
            credentials: Service credentials
            
        Returns:
            True if configuration successful, False otherwise
        """
        try:
            self.third_party_configs[service_name] = credentials
            print(f"✅ Configured service: {service_name}")
            
            # If this is a Google service, test the connection
            if service_name.startswith("google_") and HAS_GOOGLE_API:
                try:
                    # Test Google API connection
                    if service_name == "google_drive":
                        creds = service_account.Credentials.from_service_account_info(
                            credentials
                        )
                        service = build('drive', 'v3', credentials=creds)
                        # Test by listing files
                        results = service.files().list(pageSize=1).execute()
                        print(f"✅ Google Drive connection test successful")
                except Exception as e:
                    print(f"⚠️  Google API connection test failed: {e}")
            
            return True
        except Exception as e:
            print(f"❌ Failed to configure service {service_name}: {e}")
            return False
    
    def get_service_config(self, service_name: str) -> Dict[str, Any]:
        """
        Get configuration for a service
        
        Args:
            service_name: Name of the service
            
        Returns:
            Service configuration or empty dict if not found
        """
        return self.third_party_configs.get(service_name, {})
    
    def register_plugin_endpoint(self, plugin_name: str, endpoint: str, handler: Callable) -> None:
        """
        Register a plugin endpoint
        
        Args:
            plugin_name: Name of the plugin
            endpoint: Endpoint path
            handler: Handler function
        """
        if plugin_name not in self.plugin_endpoints:
            self.plugin_endpoints[plugin_name] = {}
        self.plugin_endpoints[plugin_name][endpoint] = handler
        print(f"✅ Registered endpoint {endpoint} for plugin {plugin_name}")
    
    def get_plugin_endpoints(self) -> Dict[str, Dict[str, Callable]]:
        """
        Get all registered plugin endpoints
        
        Returns:
            Dictionary of plugin endpoints
        """
        return self.plugin_endpoints