#!/usr/bin/env python3
"""
Automated API Endpoint Testing Script
Tests all API endpoints to identify SQL errors and other issues
"""
import requests
import json
import time
import sys
from typing import Dict, List, Any

# API Configuration
BASE_URL = "http://localhost:8000"
TEST_USERNAME = "admin"
TEST_PASSWORD = "admin123"

class APITester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.errors = []
        self.success_count = 0
        self.total_count = 0
        
    def authenticate(self) -> bool:
        """Authenticate and get access token"""
        try:
            response = self.session.post(f"{BASE_URL}/api/v1/auth/token", json={
                "username": TEST_USERNAME,
                "password": TEST_PASSWORD
            })
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.session.headers.update({"Authorization": f"Bearer {self.token}"})
                print("✅ Authentication successful")
                return True
            else:
                print(f"❌ Authentication failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return False
    
    def test_endpoint(self, method: str, endpoint: str, description: str) -> Dict[str, Any]:
        """Test a single endpoint"""
        self.total_count += 1
        url = f"{BASE_URL}{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = self.session.get(url, timeout=10)
            elif method.upper() == "POST":
                response = self.session.post(url, json={}, timeout=10)
            else:
                response = self.session.request(method, url, timeout=10)
                
            result = {
                "endpoint": endpoint,
                "method": method,
                "description": description,
                "status_code": response.status_code,
                "success": response.status_code < 400,
                "response_size": len(response.content),
                "content_type": response.headers.get("content-type", ""),
            }
            
            # Try to parse JSON response
            try:
                json_data = response.json()
                result["has_data"] = "data" in json_data and len(json_data.get("data", [])) > 0
                result["message"] = json_data.get("message", "")
                
                # Check for SQL errors in response
                if "error" in json_data and "Column" in str(json_data.get("error", "")):
                    result["sql_error"] = json_data["error"]
                    
            except:
                result["json_parseable"] = False
                
            if result["success"]:
                self.success_count += 1
                print(f"✅ {method} {endpoint} - {response.status_code}")
            else:
                self.errors.append(result)
                print(f"❌ {method} {endpoint} - {response.status_code}")
                
            return result
            
        except Exception as e:
            result = {
                "endpoint": endpoint,
                "method": method,
                "description": description,
                "success": False,
                "error": str(e)
            }
            self.errors.append(result)
            print(f"❌ {method} {endpoint} - ERROR: {e}")
            return result
    
    def run_all_tests(self) -> None:
        """Run comprehensive API endpoint tests"""
        print("🚀 Starting comprehensive API endpoint testing...")
        print(f"Target: {BASE_URL}")
        print("-" * 60)
        
        # Authentication required endpoints
        endpoints = [
            # Health & Root
            ("GET", "/health", "Health check"),
            ("GET", "/", "Root endpoint"),
            
            # Authentication
            ("GET", "/api/v1/auth/me", "Get current user"),
            ("GET", "/api/v1/auth/permissions", "Get user permissions"),
            
            # System
            ("GET", "/api/v1/system/dashboard-stats", "Dashboard statistics"),
            ("GET", "/api/v1/system/periods", "Accounting periods"),
            ("GET", "/api/v1/system/config", "System configuration"),
            ("GET", "/api/v1/system/audit", "Audit trail"),
            
            # Master Data
            ("GET", "/api/v1/master/customers", "Customer list"),
            ("GET", "/api/v1/master/suppliers", "Supplier list"),
            
            # Sales
            ("GET", "/api/v1/sales/orders", "Sales orders"),
            ("GET", "/api/v1/sales/invoices", "Sales invoices"),
            ("GET", "/api/v1/sales/payments", "Customer payments"),
            
            # Purchase
            ("GET", "/api/v1/purchase/orders", "Purchase orders"),
            ("GET", "/api/v1/purchase/receipts", "Goods receipts"),
            ("GET", "/api/v1/purchase/invoices", "Purchase invoices"),
            ("GET", "/api/v1/purchase/payments", "Supplier payments"),
            
            # Stock
            ("GET", "/api/v1/stock/items", "Stock items"),
            ("GET", "/api/v1/stock/movements", "Stock movements"),
            ("GET", "/api/v1/stock/takes", "Stock takes"),
            ("GET", "/api/v1/stock/reports", "Stock reports list"),
            ("GET", "/api/v1/stock/reports/valuation", "Stock valuation report"),
            
            # General Ledger
            ("GET", "/api/v1/general/accounts", "Chart of accounts"),
            ("GET", "/api/v1/general/accounts?active_only=true", "Active accounts only"),
            ("GET", "/api/v1/general/journals", "Journal entries"),
            ("GET", "/api/v1/general/batches", "GL batches"),
            ("GET", "/api/v1/general/reports", "Financial reports list"),
            ("GET", "/api/v1/general/reports/trial-balance", "Trial balance report"),
            ("GET", "/api/v1/general/budgets", "Budgets"),
        ]
        
        # Authenticate first
        if not self.authenticate():
            print("❌ Cannot proceed without authentication")
            return
            
        print("\n📊 Testing API endpoints...")
        print("-" * 60)
        
        # Test all endpoints
        results = []
        for method, endpoint, description in endpoints:
            result = self.test_endpoint(method, endpoint, description)
            results.append(result)
            time.sleep(0.1)  # Small delay between requests
            
        # Summary
        print("\n" + "="*60)
        print("📈 TEST SUMMARY")
        print("="*60)
        print(f"Total endpoints tested: {self.total_count}")
        print(f"Successful: {self.success_count}")
        print(f"Failed: {len(self.errors)}")
        print(f"Success rate: {(self.success_count/self.total_count)*100:.1f}%")
        
        if self.errors:
            print(f"\n❌ FAILED ENDPOINTS ({len(self.errors)}):")
            print("-" * 40)
            for error in self.errors:
                print(f"  {error['method']} {error['endpoint']}")
                if 'sql_error' in error:
                    print(f"    SQL Error: {error['sql_error']}")
                elif 'error' in error:
                    print(f"    Error: {error['error']}")
                print()
                
        # Check for SQL errors specifically
        sql_errors = [e for e in self.errors if 'sql_error' in e]
        if sql_errors:
            print(f"\n🔴 SQL ERRORS DETECTED ({len(sql_errors)}):")
            print("-" * 50)
            for error in sql_errors:
                print(f"  {error['method']} {error['endpoint']}")
                print(f"    {error['sql_error']}")
                print()
        
        if len(self.errors) == 0:
            print("\n🎉 ALL ENDPOINTS WORKING PERFECTLY!")
        else:
            print(f"\n⚠️  {len(self.errors)} endpoints need attention")
            
        return results

def main():
    """Main function"""
    tester = APITester()
    results = tester.run_all_tests()
    
    # Exit with error code if there were failures
    if tester.errors:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()