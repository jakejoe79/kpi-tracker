#!/usr/bin/env python3
"""
KPI Tracker Backend API Test Suite
Tests all endpoints for the reservation setter KPI tracking application
"""

import requests
import sys
import json
from datetime import datetime, date
from typing import Dict, Any

class KPITrackerAPITester:
    def __init__(self, base_url="https://kpi-tracker-55.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        self.today = date.today().isoformat()
        
    def log_test(self, name: str, success: bool, details: str = "", response_data: Any = None):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            
        result = {
            "test_name": name,
            "success": success,
            "details": details,
            "response_data": response_data
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {name}")
        if details:
            print(f"    {details}")
        if not success and response_data:
            print(f"    Response: {response_data}")
        print()

    def make_request(self, method: str, endpoint: str, data: Dict = None, params: Dict = None) -> tuple:
        """Make HTTP request and return (success, response_data, status_code)"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = {'Content-Type': 'application/json'}
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, params=params, timeout=10)
            elif method.upper() == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method.upper() == 'PUT':
                response = requests.put(url, json=data, headers=headers, params=params, timeout=10)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=10)
            else:
                return False, f"Unsupported method: {method}", 0
                
            return response.status_code < 400, response.json() if response.content else {}, response.status_code
            
        except requests.exceptions.RequestException as e:
            return False, f"Request failed: {str(e)}", 0
        except json.JSONDecodeError:
            return False, "Invalid JSON response", response.status_code if 'response' in locals() else 0

    def test_health_endpoint(self):
        """Test GET /api/health"""
        success, data, status = self.make_request('GET', '/health')
        
        if success and status == 200:
            required_fields = ['status', 'current_period']
            missing_fields = [field for field in required_fields if field not in data]
            
            if not missing_fields and data.get('status') == 'healthy':
                self.log_test("Health Check", True, f"Status: {data.get('status')}, Period: {data.get('current_period')}")
                return data
            else:
                self.log_test("Health Check", False, f"Missing fields: {missing_fields}" if missing_fields else "Status not healthy")
        else:
            self.log_test("Health Check", False, f"Status: {status}, Response: {data}")
        return None

    def test_get_today_entry(self):
        """Test GET /api/entries/today"""
        success, data, status = self.make_request('GET', '/entries/today')
        
        if success and status == 200:
            required_fields = ['id', 'date', 'calls_received', 'bookings', 'spins', 'misc_income']
            missing_fields = [field for field in required_fields if field not in data]
            
            if not missing_fields:
                self.log_test("Get Today Entry", True, f"Entry date: {data.get('date')}, Calls: {data.get('calls_received')}")
                return data
            else:
                self.log_test("Get Today Entry", False, f"Missing fields: {missing_fields}")
        else:
            self.log_test("Get Today Entry", False, f"Status: {status}, Response: {data}")
        return None

    def test_update_calls(self, entry_date: str = None):
        """Test PUT /api/entries/{date}/calls"""
        test_date = entry_date or self.today
        test_calls = 50
        
        success, data, status = self.make_request('PUT', f'/entries/{test_date}/calls', params={'calls_received': test_calls})
        
        if success and status == 200:
            if data.get('calls_received') == test_calls:
                self.log_test("Update Calls", True, f"Updated calls to {test_calls} for {test_date}")
                return data
            else:
                self.log_test("Update Calls", False, f"Expected {test_calls} calls, got {data.get('calls_received')}")
        else:
            self.log_test("Update Calls", False, f"Status: {status}, Response: {data}")
        return None

    def test_add_booking(self, entry_date: str = None):
        """Test POST /api/entries/{date}/bookings"""
        test_date = entry_date or self.today
        booking_data = {
            "profit": 25.50,
            "is_prepaid": True,
            "has_refund_protection": False,
            "time_since_last": 30
        }
        
        success, data, status = self.make_request('POST', f'/entries/{test_date}/bookings', booking_data)
        
        if success and status == 200:
            bookings = data.get('bookings', [])
            if bookings and len(bookings) > 0:
                latest_booking = bookings[-1]
                if latest_booking.get('profit') == booking_data['profit']:
                    self.log_test("Add Booking", True, f"Added booking with profit ${booking_data['profit']}")
                    return latest_booking.get('id')
                else:
                    self.log_test("Add Booking", False, f"Profit mismatch: expected {booking_data['profit']}, got {latest_booking.get('profit')}")
            else:
                self.log_test("Add Booking", False, "No bookings found in response")
        else:
            self.log_test("Add Booking", False, f"Status: {status}, Response: {data}")
        return None

    def test_delete_booking(self, entry_date: str, booking_id: str):
        """Test DELETE /api/entries/{date}/bookings/{id}"""
        if not booking_id:
            self.log_test("Delete Booking", False, "No booking ID provided")
            return False
            
        success, data, status = self.make_request('DELETE', f'/entries/{entry_date}/bookings/{booking_id}')
        
        if success and status == 200:
            # Check if booking was removed
            bookings = data.get('bookings', [])
            booking_exists = any(b.get('id') == booking_id for b in bookings)
            
            if not booking_exists:
                self.log_test("Delete Booking", True, f"Successfully deleted booking {booking_id}")
                return True
            else:
                self.log_test("Delete Booking", False, f"Booking {booking_id} still exists after deletion")
        else:
            self.log_test("Delete Booking", False, f"Status: {status}, Response: {data}")
        return False

    def test_add_spin(self, entry_date: str = None):
        """Test POST /api/entries/{date}/spins"""
        test_date = entry_date or self.today
        spin_data = {
            "amount": 15.75,
            "is_mega": False,
            "booking_number": 1
        }
        
        success, data, status = self.make_request('POST', f'/entries/{test_date}/spins', spin_data)
        
        if success and status == 200:
            spins = data.get('spins', [])
            if spins and len(spins) > 0:
                latest_spin = spins[-1]
                if latest_spin.get('amount') == spin_data['amount']:
                    self.log_test("Add Spin", True, f"Added spin with amount ${spin_data['amount']}")
                    return latest_spin.get('id')
                else:
                    self.log_test("Add Spin", False, f"Amount mismatch: expected {spin_data['amount']}, got {latest_spin.get('amount')}")
            else:
                self.log_test("Add Spin", False, "No spins found in response")
        else:
            self.log_test("Add Spin", False, f"Status: {status}, Response: {data}")
        return None

    def test_add_misc_income(self, entry_date: str = None):
        """Test POST /api/entries/{date}/misc"""
        test_date = entry_date or self.today
        misc_data = {
            "amount": 5.00,
            "source": "request_lead",
            "description": "Test misc income"
        }
        
        success, data, status = self.make_request('POST', f'/entries/{test_date}/misc', misc_data)
        
        if success and status == 200:
            misc_income = data.get('misc_income', [])
            if misc_income and len(misc_income) > 0:
                latest_misc = misc_income[-1]
                if latest_misc.get('amount') == misc_data['amount']:
                    self.log_test("Add Misc Income", True, f"Added misc income ${misc_data['amount']}")
                    return latest_misc.get('id')
                else:
                    self.log_test("Add Misc Income", False, f"Amount mismatch: expected {misc_data['amount']}, got {latest_misc.get('amount')}")
            else:
                self.log_test("Add Misc Income", False, "No misc income found in response")
        else:
            self.log_test("Add Misc Income", False, f"Status: {status}, Response: {data}")
        return None

    def test_daily_stats(self, entry_date: str = None):
        """Test GET /api/stats/daily/{date}"""
        test_date = entry_date or self.today
        success, data, status = self.make_request('GET', f'/stats/daily/{test_date}')
        
        if success and status == 200:
            required_fields = ['date', 'calls', 'reservations', 'conversion_rate', 'profit', 'spins']
            missing_fields = [field for field in required_fields if field not in data]
            
            if not missing_fields:
                calls_total = data.get('calls', {}).get('total', 0)
                reservations_total = data.get('reservations', {}).get('total', 0)
                self.log_test("Daily Stats", True, f"Date: {test_date}, Calls: {calls_total}, Reservations: {reservations_total}")
                return data
            else:
                self.log_test("Daily Stats", False, f"Missing fields: {missing_fields}")
        else:
            self.log_test("Daily Stats", False, f"Status: {status}, Response: {data}")
        return None

    def test_biweekly_stats(self):
        """Test GET /api/stats/biweekly"""
        success, data, status = self.make_request('GET', '/stats/biweekly')
        
        if success and status == 200:
            required_fields = ['period_id', 'start_date', 'end_date', 'calls', 'reservations', 'profit', 'spins', 'combined']
            missing_fields = [field for field in required_fields if field not in data]
            
            if not missing_fields:
                combined_total = data.get('combined', {}).get('total', 0)
                period_id = data.get('period_id', '')
                self.log_test("Biweekly Stats", True, f"Period: {period_id}, Combined: ${combined_total}")
                return data
            else:
                self.log_test("Biweekly Stats", False, f"Missing fields: {missing_fields}")
        else:
            self.log_test("Biweekly Stats", False, f"Status: {status}, Response: {data}")
        return None

    def test_current_period(self):
        """Test GET /api/periods/current"""
        success, data, status = self.make_request('GET', '/periods/current')
        
        if success and status == 200:
            required_fields = ['period_id', 'start_date', 'end_date', 'days_remaining']
            missing_fields = [field for field in required_fields if field not in data]
            
            if not missing_fields:
                period_id = data.get('period_id', '')
                days_remaining = data.get('days_remaining', 0)
                self.log_test("Current Period", True, f"Period: {period_id}, Days remaining: {days_remaining}")
                return data
            else:
                self.log_test("Current Period", False, f"Missing fields: {missing_fields}")
        else:
            self.log_test("Current Period", False, f"Status: {status}, Response: {data}")
        return None

    def test_period_logs(self):
        """Test GET /api/periods"""
        success, data, status = self.make_request('GET', '/periods')
        
        if success and status == 200:
            if isinstance(data, list):
                self.log_test("Period Logs", True, f"Retrieved {len(data)} archived periods")
                return data
            else:
                self.log_test("Period Logs", False, "Response is not a list")
        else:
            self.log_test("Period Logs", False, f"Status: {status}, Response: {data}")
        return None

    def run_all_tests(self):
        """Run comprehensive test suite"""
        print("🚀 Starting KPI Tracker Backend API Tests")
        print("=" * 50)
        
        # Test 1: Health check
        health_data = self.test_health_endpoint()
        
        # Test 2: Get today's entry (creates if doesn't exist)
        today_entry = self.test_get_today_entry()
        
        # Test 3: Update calls
        self.test_update_calls()
        
        # Test 4: Add booking and then delete it
        booking_id = self.test_add_booking()
        if booking_id:
            self.test_delete_booking(self.today, booking_id)
        
        # Test 5: Add spin
        self.test_add_spin()
        
        # Test 6: Add misc income
        self.test_add_misc_income()
        
        # Test 7: Get daily stats
        self.test_daily_stats()
        
        # Test 8: Get biweekly stats
        self.test_biweekly_stats()
        
        # Test 9: Get current period info
        self.test_current_period()
        
        # Test 10: Get period logs (archived periods)
        self.test_period_logs()
        
        # Print summary
        print("=" * 50)
        print(f"📊 Test Summary: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
            return 0
        else:
            print(f"❌ {self.tests_run - self.tests_passed} tests failed")
            return 1

def main():
    """Main test runner"""
    tester = KPITrackerAPITester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())