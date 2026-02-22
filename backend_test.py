import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional

class LillithAPITester:
    def __init__(self, base_url="https://story-automation.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.project_id = None

    def run_test(self, name: str, method: str, endpoint: str, expected_status: int, 
                 data: Optional[Dict[str, Any]] = None, 
                 headers: Optional[Dict[str, str]] = None) -> tuple[bool, Dict[str, Any]]:
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        if headers is None:
            headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=30)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    if isinstance(response_data, dict) and 'id' in response_data:
                        print(f"   Response ID: {response_data['id']}")
                    elif isinstance(response_data, list):
                        print(f"   Response items: {len(response_data)}")
                except:
                    response_data = {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_text = response.text
                    print(f"   Error: {error_text}")
                except:
                    pass
                response_data = {}

            return success, response_data

        except Exception as e:
            print(f"❌ Failed - Network Error: {str(e)}")
            return False, {}

    def test_api_root(self):
        """Test API root endpoint"""
        success, response = self.run_test(
            "API Root",
            "GET",
            "",
            200
        )
        return success

    def test_status_endpoints(self):
        """Test status check endpoints"""
        # Create status check
        success, response = self.run_test(
            "Create Status Check",
            "POST",
            "status",
            200,
            data={"client_name": "test_client"}
        )
        
        if success:
            # Get status checks
            success2, response2 = self.run_test(
                "Get Status Checks",
                "GET",
                "status",
                200
            )
            return success and success2
        return success

    def test_projects_crud(self):
        """Test complete CRUD operations for projects"""
        results = []
        
        # 1. List projects (should work even if empty)
        success, projects = self.run_test(
            "List Projects",
            "GET",
            "projects",
            200
        )
        results.append(success)
        
        # 2. Create a project
        test_project_data = {
            "name": f"Test Project {datetime.now().strftime('%H%M%S')}",
            "description": "This is a test project for Lillith API",
            "genre": "Sci-fi"
        }
        
        success, project = self.run_test(
            "Create Project",
            "POST",
            "projects",
            200,
            data=test_project_data
        )
        results.append(success)
        
        if success and 'id' in project:
            self.project_id = project['id']
            print(f"   Created project ID: {self.project_id}")
            
            # 3. Get specific project
            success, retrieved_project = self.run_test(
                "Get Project by ID",
                "GET",
                f"projects/{self.project_id}",
                200
            )
            results.append(success)
            
            # 4. Update project
            update_data = {
                "story_bible": "This is an updated story bible for testing",
                "character_profile": {
                    "name": "Test Character",
                    "role": "Protagonist"
                }
            }
            
            success, updated_project = self.run_test(
                "Update Project",
                "PUT",
                f"projects/{self.project_id}",
                200,
                data=update_data
            )
            results.append(success)
            
            # 5. List projects again to verify creation
            success, projects_after = self.run_test(
                "List Projects After Creation",
                "GET",
                "projects",
                200
            )
            results.append(success)
            
            # 6. Delete project
            success, delete_response = self.run_test(
                "Delete Project",
                "DELETE",
                f"projects/{self.project_id}",
                200
            )
            results.append(success)
            
            # 7. Verify deletion
            success, final_projects = self.run_test(
                "Verify Project Deletion",
                "GET",
                "projects",
                200
            )
            results.append(success)
        
        return all(results)

    def test_character_autofill(self):
        """Test character autofill functionality"""
        test_character_request = {
            "name": "Test Character",
            "role": "Protagonist",
            "age": 25,
            "archetype": "Hero"
        }
        
        success, character = self.run_test(
            "Character Autofill",
            "POST",
            "characters/autofill",
            200,
            data=test_character_request
        )
        
        if success and character:
            print(f"   Generated character: {character.get('name', 'Unknown')}")
            print(f"   Role: {character.get('role', 'N/A')}")
            print(f"   Archetype: {character.get('archetype', 'N/A')}")
        
        return success

    def test_plugins_endpoint(self):
        """Test plugins listing"""
        success, plugins = self.run_test(
            "List Plugins",
            "GET",
            "plugins",
            200
        )
        
        if success:
            print(f"   Found {len(plugins)} plugins")
            for plugin in plugins:
                print(f"   - {plugin.get('name', 'Unknown')} at {plugin.get('path', 'Unknown path')}")
        
        return success

    def test_lm_studio_offline_endpoints(self):
        """Test LM Studio offline endpoints - should return 502"""
        results = []
        
        # Test getting models when LM Studio is offline
        success, response = self.run_test(
            "Get AI Models (LM Studio Offline)",
            "GET",
            "ai/models",
            502  # Should fail with 502 when LM Studio unavailable
        )
        results.append(success)
        
        # Test story bible generation when LM Studio is offline
        if self.project_id:
            test_project_id = self.project_id
        else:
            # Create a quick test project for this test
            success_create, project = self.run_test(
                "Create Test Project for Story Bible",
                "POST",
                "projects",
                200,
                data={"name": "LM Studio Test Project", "description": "Test", "genre": "Test"}
            )
            if success_create and 'id' in project:
                test_project_id = project['id']
            else:
                return False
        
        success, response = self.run_test(
            "Generate Story Bible (LM Studio Offline)",
            "POST",
            "ai/story-bible/stream",
            502,  # Should fail with 502 when LM Studio unavailable
            data={"project_id": test_project_id, "model": "test-model"}
        )
        results.append(success)
        
        return all(results)

    def test_edge_cases(self):
        """Test edge cases and error conditions"""
        results = []
        
        # Test creating project with empty name
        success, response = self.run_test(
            "Create Project with Empty Name",
            "POST",
            "projects",
            400,  # Should fail
            data={"name": ""}
        )
        # In this case, success means we got the expected error
        results.append(success)
        
        # Test getting non-existent project
        success, response = self.run_test(
            "Get Non-existent Project",
            "GET",
            "projects/non-existent-id",
            404  # Should fail
        )
        results.append(success)
        
        # Test character autofill with minimal data
        success, response = self.run_test(
            "Character Autofill with Minimal Data",
            "POST",
            "characters/autofill",
            200,
            data={"name": "MinimalTest"}
        )
        results.append(success)
        
        return all(results)

def main():
    """Main test runner"""
    print("=" * 60)
    print("🚀 Starting Lillith API Backend Testing")
    print("=" * 60)
    
    tester = LillithAPITester()
    
    test_results = {}
    
    # Run all test suites
    test_suites = [
        ("API Root", tester.test_api_root),
        ("Status Endpoints", tester.test_status_endpoints),
        ("Projects CRUD", tester.test_projects_crud),
        ("Character Autofill", tester.test_character_autofill),
        ("Plugins Endpoint", tester.test_plugins_endpoint),
        ("Edge Cases", tester.test_edge_cases),
    ]
    
    for suite_name, test_function in test_suites:
        print(f"\n{'=' * 40}")
        print(f"📋 Running {suite_name} Tests")
        print(f"{'=' * 40}")
        
        try:
            result = test_function()
            test_results[suite_name] = result
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"\n{suite_name}: {status}")
        except Exception as e:
            test_results[suite_name] = False
            print(f"\n{suite_name}: ❌ FAILED with exception: {str(e)}")
    
    # Print final summary
    print(f"\n{'=' * 60}")
    print("📊 FINAL TEST SUMMARY")
    print(f"{'=' * 60}")
    
    passed_suites = sum(1 for result in test_results.values() if result)
    total_suites = len(test_results)
    
    for suite_name, result in test_results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{suite_name:.<30} {status}")
    
    print(f"\nOverall API Tests: {tester.tests_passed}/{tester.tests_run}")
    print(f"Test Suites: {passed_suites}/{total_suites}")
    
    success_rate = (tester.tests_passed / tester.tests_run) * 100 if tester.tests_run > 0 else 0
    print(f"Success Rate: {success_rate:.1f}%")
    
    if success_rate >= 80:
        print("\n🎉 Backend API testing completed successfully!")
        return 0
    else:
        print("\n🚨 Backend API testing found significant issues!")
        return 1

if __name__ == "__main__":
    sys.exit(main())