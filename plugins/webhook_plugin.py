"""
Webhook Plugin
Handles webhook registration and event triggering
"""

from typing import Dict, List, Any, Callable
import json
import time
import hmac
import hashlib

# In-memory storage for webhooks (in production, this would be persistent)
_webhooks = {}
_event_handlers = {}

def register_webhook(event_type: str, callback_url: str, secret: str = "") -> bool:
    """
    Register a webhook for a specific event type
    
    Args:
        event_type: Type of event (e.g., 'document_added', 'training_complete')
        callback_url: URL to call when event occurs
        secret: Optional secret for webhook authentication
        
    Returns:
        True if registration successful, False otherwise
    """
    try:
        if event_type not in _webhooks:
            _webhooks[event_type] = []
        
        webhook = {
            "url": callback_url,
            "secret": secret,
            "created_at": __import__('time').time()
        }
        
        _webhooks[event_type].append(webhook)
        print(f"✅ Registered webhook for event '{event_type}' -> {callback_url}")
        return True
    except Exception as e:
        print(f"❌ Failed to register webhook: {e}")
        return False

def trigger_event(event_type: str, data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Trigger an event and call all registered webhooks
    
    Args:
        event_type: Type of event to trigger
        data: Data to send to webhook endpoints
        
    Returns:
        List of webhook response results
    """
    results = []
    
    if event_type in _webhooks:
        try:
            import httpx
        except ImportError:
            print("⚠️ httpx not available, skipping webhook trigger")
            return results
            
        for webhook in _webhooks[event_type]:
            success = False
            attempts = 0
            max_attempts = 3
            
            while not success and attempts < max_attempts:
                try:
                    attempts += 1
                    
                    # Prepare headers
                    headers = {
                        "Content-Type": "application/json",
                        "User-Agent": "Bldr-Webhook-Client/1.0"
                    }
                    
                    # Add signature if secret is provided
                    if webhook.get("secret"):
                        # Create HMAC signature
                        signature = hmac.new(
                            webhook["secret"].encode('utf-8'),
                            json.dumps(data).encode('utf-8'),
                            hashlib.sha256
                        ).hexdigest()
                        headers["X-Bldr-Signature"] = f"sha256={signature}"
                    
                    # Send webhook request with retry logic
                    response = httpx.post(
                        webhook["url"],
                        json=data,
                        headers=headers,
                        timeout=30.0
                    )
                    
                    result = {
                        "webhook_url": webhook["url"],
                        "status_code": response.status_code,
                        "success": response.status_code in [200, 201, 204],
                        "response": response.text[:200] if response.text else "",
                        "attempt": attempts
                    }
                    
                    results.append(result)
                    success = response.status_code in [200, 201, 204]
                    
                    if success:
                        print(f"✅ Webhook triggered for {event_type} -> {webhook['url']} (Status: {response.status_code})")
                    else:
                        print(f"⚠️ Webhook trigger failed for {event_type} -> {webhook['url']} (Status: {response.status_code}), attempt {attempts}")
                        if attempts < max_attempts:
                            time.sleep(2 ** attempts)  # Exponential backoff
                    
                except Exception as e:
                    result = {
                        "webhook_url": webhook["url"],
                        "status_code": 0,
                        "success": False,
                        "error": str(e),
                        "attempt": attempts
                    }
                    results.append(result)
                    print(f"❌ Webhook trigger failed for {event_type} -> {webhook['url']}: {e}, attempt {attempts}")
                    if attempts < max_attempts:
                        time.sleep(2 ** attempts)  # Exponential backoff
    
    return results

def list_webhooks() -> Dict[str, List[Dict[str, Any]]]:
    """
    List all registered webhooks
    
    Returns:
        Dictionary of event types with their registered webhooks
    """
    # Return a copy without secrets for security
    safe_webhooks = {}
    for event_type, webhooks in _webhooks.items():
        safe_webhooks[event_type] = [
            {
                "url": webhook["url"],
                "created_at": webhook["created_at"]
            }
            for webhook in webhooks
        ]
    
    return safe_webhooks

def remove_webhook(event_type: str, callback_url: str) -> bool:
    """
    Remove a webhook registration
    
    Args:
        event_type: Type of event
        callback_url: URL of the webhook to remove
        
    Returns:
        True if removal successful, False otherwise
    """
    try:
        if event_type in _webhooks:
            original_count = len(_webhooks[event_type])
            _webhooks[event_type] = [
                webhook for webhook in _webhooks[event_type]
                if webhook["url"] != callback_url
            ]
            new_count = len(_webhooks[event_type])
            
            if new_count < original_count:
                print(f"✅ Removed webhook for {event_type} -> {callback_url}")
                return True
            else:
                print(f"⚠️ Webhook not found for {event_type} -> {callback_url}")
                return False
        else:
            print(f"⚠️ No webhooks registered for event type: {event_type}")
            return False
    except Exception as e:
        print(f"❌ Failed to remove webhook: {e}")
        return False

# Event handler registration functions
def register_event_handler(event_type: str, handler: Callable) -> None:
    """
    Register an in-process event handler (for internal events)
    
    Args:
        event_type: Type of event to handle
        handler: Function to call when event occurs
    """
    if event_type not in _event_handlers:
        _event_handlers[event_type] = []
    _event_handlers[event_type].append(handler)
    print(f"✅ Registered event handler for '{event_type}'")

def trigger_internal_event(event_type: str, data: Dict[str, Any]) -> None:
    """
    Trigger an internal event and call all registered handlers
    
    Args:
        event_type: Type of event to trigger
        data: Data to pass to event handlers
    """
    if event_type in _event_handlers:
        for handler in _event_handlers[event_type]:
            try:
                handler(data)
            except Exception as e:
                print(f"❌ Event handler error for {event_type}: {e}")