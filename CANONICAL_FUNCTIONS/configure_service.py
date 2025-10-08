# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: configure_service
# Основной источник: C:\Bldr\core\plugin_manager.py
# Дубликаты (для справки):
#   - C:\Bldr\plugins\third_party_integration_plugin.py
#================================================================================
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