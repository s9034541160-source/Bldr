#!/usr/bin/env python3
"""
Health check script for Bldr Empire v0.6 MVP
"""
import requests
import time
import sys
import json
from typing import Dict, List, Tuple

class HealthChecker:
    """Health checker for all Bldr services"""
    
    def __init__(self):
        self.services = {
            "redis": "http://localhost:6379",
            "neo4j": "http://localhost:7474",
            "qdrant": "http://localhost:6333/health",
            "postgres": "localhost:5432",  # No HTTP endpoint
            "backend": "http://localhost:8000/health",
            "bot-webhook": "http://localhost:8001/tg/health",
            "frontend": "http://localhost:3000",
            "estimate-calculator": "http://localhost:8000/tools/estimate_calculator/health",
            "tender-analyzer": "http://localhost:8000/analyze/health"
        }
        
        self.results = {}
    
    def check_service(self, name: str, url: str) -> Tuple[bool, str]:
        """Check individual service health"""
        try:
            if name == "postgres":
                # PostgreSQL doesn't have HTTP endpoint, skip for now
                return True, "PostgreSQL (no HTTP endpoint)"
            
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                return True, f"HTTP {response.status_code}"
            else:
                return False, f"HTTP {response.status_code}"
                
        except requests.exceptions.ConnectionError:
            return False, "Connection refused"
        except requests.exceptions.Timeout:
            return False, "Timeout"
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def check_all_services(self) -> Dict[str, Dict]:
        """Check all services and return results"""
        print("Checking Bldr Empire v0.6 MVP services...")
        print("=" * 50)
        
        for name, url in self.services.items():
            print(f"Checking {name}...", end=" ")
            
            is_healthy, message = self.check_service(name, url)
            self.results[name] = {
                "healthy": is_healthy,
                "message": message,
                "url": url
            }
            
            status = "OK" if is_healthy else "FAIL"
            print(f"{status} {message}")
        
        return self.results
    
    def get_summary(self) -> Dict:
        """Get health check summary"""
        total_services = len(self.results)
        healthy_services = sum(1 for r in self.results.values() if r["healthy"])
        health_percentage = (healthy_services / total_services) * 100
        
        return {
            "total_services": total_services,
            "healthy_services": healthy_services,
            "unhealthy_services": total_services - healthy_services,
            "health_percentage": health_percentage,
            "overall_status": "healthy" if health_percentage >= 75 else "unhealthy"
        }
    
    def print_summary(self):
        """Print health check summary"""
        summary = self.get_summary()
        
        print("\n" + "=" * 50)
        print("HEALTH CHECK SUMMARY")
        print("=" * 50)
        print(f"Total services: {summary['total_services']}")
        print(f"Healthy: {summary['healthy_services']}")
        print(f"Unhealthy: {summary['unhealthy_services']}")
        print(f"Health percentage: {summary['health_percentage']:.1f}%")
        print(f"Overall status: {summary['overall_status'].upper()}")
        
        if summary['overall_status'] == 'healthy':
            print("\nAll critical services are healthy!")
        else:
            print("\nSome services are unhealthy. Check the details above.")
    
    def print_unhealthy_services(self):
        """Print details of unhealthy services"""
        unhealthy = {name: result for name, result in self.results.items() if not result["healthy"]}
        
        if unhealthy:
            print("\nUNHEALTHY SERVICES:")
            print("-" * 30)
            for name, result in unhealthy.items():
                print(f"- {name}: {result['message']}")
        else:
            print("\nAll services are healthy!")
    
    def save_results(self, filename: str = "health_check_results.json"):
        """Save health check results to file"""
        results = {
            "timestamp": time.time(),
            "summary": self.get_summary(),
            "services": self.results
        }
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\nResults saved to {filename}")


def main():
    """Main health check function"""
    print("Bldr Empire v0.6 MVP - Health Check")
    print("=" * 50)
    
    checker = HealthChecker()
    
    # Check all services
    checker.check_all_services()
    
    # Print summary
    checker.print_summary()
    
    # Print unhealthy services
    checker.print_unhealthy_services()
    
    # Save results
    checker.save_results()
    
    # Exit with appropriate code
    summary = checker.get_summary()
    if summary['overall_status'] == 'healthy':
        print("\nHealth check passed!")
        sys.exit(0)
    else:
        print("\nHealth check failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
