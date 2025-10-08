#!/usr/bin/env python3
"""
Performance and load testing suite
"""
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any

import pytest
import httpx
from fastapi.testclient import TestClient


@pytest.mark.performance
class TestPerformanceMetrics:
    """Test performance requirements and benchmarks"""

    def test_health_check_performance(self, client: TestClient):
        """Test health check response time"""
        times = []
        for _ in range(10):
            start = time.time()
            response = client.get("/health")
            end = time.time()
            times.append(end - start)
            assert response.status_code == 200
        
        avg_time = sum(times) / len(times)
        max_time = max(times)
        
        assert avg_time < 0.1  # Average under 100ms
        assert max_time < 0.5  # Max under 500ms

    def test_api_documentation_performance(self, client: TestClient):
        """Test API docs load time"""
        start = time.time()
        response = client.get("/docs")
        end = time.time()
        
        assert response.status_code == 200
        assert (end - start) < 2.0  # Should load within 2 seconds

    def test_authentication_performance(self, client: TestClient, test_user_data):
        """Test authentication endpoint performance"""
        # Register user first
        client.post("/api/auth/register", json=test_user_data)
        
        login_data = {
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        }
        
        times = []
        for _ in range(5):
            start = time.time()
            response = client.post("/api/auth/login", json=login_data)
            end = time.time()
            times.append(end - start)
            assert response.status_code == 200
        
        avg_time = sum(times) / len(times)
        assert avg_time < 0.5  # Average under 500ms

    def test_verification_creation_performance(self, client: TestClient):
        """Test verification creation performance"""
        verification_data = {"service_name": "whatsapp", "capability": "sms"}
        
        times = []
        for _ in range(5):
            start = time.time()
            response = client.post("/api/verification/create", json=verification_data)
            end = time.time()
            times.append(end - start)
            assert response.status_code == 200
        
        avg_time = sum(times) / len(times)
        assert avg_time < 1.0  # Average under 1 second


@pytest.mark.load
class TestLoadTesting:
    """Load testing with concurrent requests"""

    def test_concurrent_health_checks(self, client: TestClient):
        """Test concurrent health check requests"""
        def make_request():
            response = client.get("/health")
            return response.status_code == 200
        
        # Test with 10 concurrent requests
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [future.result() for future in futures]
        
        # All requests should succeed
        assert all(results)

    def test_concurrent_user_registration(self, client: TestClient):
        """Test concurrent user registrations"""
        def register_user(user_id: int):
            user_data = {
                "email": f"user{user_id}@example.com",
                "password": "TestPassword123!",
                "full_name": f"Test User {user_id}",
                "phone_number": f"+123456789{user_id}"
            }
            response = client.post("/api/auth/register", json=user_data)
            return response.status_code == 201
        
        # Test with 5 concurrent registrations
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(register_user, i) for i in range(5)]
            results = [future.result() for future in futures]
        
        # All registrations should succeed
        assert all(results)

    def test_concurrent_verification_creation(self, client: TestClient):
        """Test concurrent verification creation"""
        def create_verification():
            verification_data = {"service_name": "whatsapp", "capability": "sms"}
            response = client.post("/api/verification/create", json=verification_data)
            return response.status_code == 200
        
        # Test with 5 concurrent verifications
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(create_verification) for _ in range(5)]
            results = [future.result() for future in futures]
        
        # All verifications should succeed
        assert all(results)


@pytest.mark.stress
class TestStressTesting:
    """Stress testing with high load"""

    def test_high_volume_requests(self, client: TestClient):
        """Test handling high volume of requests"""
        def make_requests(num_requests: int) -> List[bool]:
            results = []
            for _ in range(num_requests):
                try:
                    response = client.get("/health")
                    results.append(response.status_code == 200)
                except Exception:
                    results.append(False)
            return results
        
        # Test with 50 requests per thread, 5 threads
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_requests, 50) for _ in range(5)]
            all_results = []
            for future in futures:
                all_results.extend(future.result())
        
        # At least 95% should succeed
        success_rate = sum(all_results) / len(all_results)
        assert success_rate >= 0.95

    def test_memory_usage_stability(self, client: TestClient):
        """Test memory usage remains stable under load"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Make many requests
        for _ in range(100):
            client.get("/health")
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 50MB)
        assert memory_increase < 50 * 1024 * 1024


@pytest.mark.asyncio
@pytest.mark.performance
class TestAsyncPerformance:
    """Test async endpoint performance"""

    async def test_async_client_performance(self):
        """Test async client performance"""
        async with httpx.AsyncClient(base_url="http://test") as client:
            # Test concurrent async requests
            tasks = []
            for _ in range(10):
                task = client.get("/health")
                tasks.append(task)
            
            start_time = time.time()
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            end_time = time.time()
            
            # All requests should complete within reasonable time
            assert (end_time - start_time) < 2.0
            
            # Count successful responses
            successful = sum(1 for r in responses if hasattr(r, 'status_code') and r.status_code == 200)
            assert successful >= 8  # At least 80% success rate


class TestResourceUsage:
    """Test resource usage and limits"""

    def test_database_connection_limits(self, client: TestClient):
        """Test database connection handling"""
        # Make multiple requests that use database
        for _ in range(20):
            response = client.get("/health/detailed")
            assert response.status_code == 200

    def test_file_descriptor_limits(self, client: TestClient):
        """Test file descriptor usage"""
        import resource
        
        initial_fds = len(os.listdir('/proc/self/fd')) if os.path.exists('/proc/self/fd') else 0
        
        # Make requests that might open connections
        for _ in range(50):
            client.get("/health")
        
        if os.path.exists('/proc/self/fd'):
            final_fds = len(os.listdir('/proc/self/fd'))
            # File descriptors shouldn't grow excessively
            assert final_fds - initial_fds < 10


class TestPerformanceBenchmarks:
    """Benchmark tests for performance tracking"""

    def test_benchmark_health_endpoint(self, client: TestClient):
        """Benchmark health endpoint performance"""
        num_requests = 100
        start_time = time.time()
        
        for _ in range(num_requests):
            response = client.get("/health")
            assert response.status_code == 200
        
        end_time = time.time()
        total_time = end_time - start_time
        requests_per_second = num_requests / total_time
        
        print(f"Health endpoint: {requests_per_second:.2f} requests/second")
        assert requests_per_second > 50  # Should handle at least 50 RPS

    def test_benchmark_auth_endpoint(self, client: TestClient, test_user_data):
        """Benchmark authentication endpoint"""
        # Register user first
        client.post("/api/auth/register", json=test_user_data)
        
        login_data = {
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        }
        
        num_requests = 20
        start_time = time.time()
        
        for _ in range(num_requests):
            response = client.post("/api/auth/login", json=login_data)
            assert response.status_code == 200
        
        end_time = time.time()
        total_time = end_time - start_time
        requests_per_second = num_requests / total_time
        
        print(f"Auth endpoint: {requests_per_second:.2f} requests/second")
        assert requests_per_second > 10  # Should handle at least 10 RPS