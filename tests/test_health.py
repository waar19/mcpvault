"""Tests for Health Monitor - Circuit breaker and auto-recovery."""
import pytest
import time
from mcpv.health import HealthMonitor, ServerHealth, CircuitState


class TestCircuitBreakerStates:
    """Test suite for circuit breaker state transitions."""
    
    def test_initial_state_is_closed(self):
        """New server should start in CLOSED state."""
        health = ServerHealth(name="test")
        assert health.state == CircuitState.CLOSED
    
    def test_opens_after_failure_threshold(self):
        """Should transition to OPEN after consecutive failures."""
        health = ServerHealth(name="test", failure_threshold=3)
        
        health.record_failure("error 1")
        health.record_failure("error 2")
        assert health.state == CircuitState.CLOSED
        
        health.record_failure("error 3")
        assert health.state == CircuitState.OPEN
    
    def test_success_resets_failure_count(self):
        """Success should reset consecutive failure count."""
        health = ServerHealth(name="test", failure_threshold=3)
        
        health.record_failure("error 1")
        health.record_failure("error 2")
        health.record_success()
        
        assert health.consecutive_failures == 0
        assert health.state == CircuitState.CLOSED
    
    def test_half_open_after_recovery_timeout(self):
        """Should transition to HALF_OPEN after recovery timeout."""
        health = ServerHealth(name="test", failure_threshold=1, recovery_timeout=0.1)
        
        health.record_failure("error")
        assert health.state == CircuitState.OPEN
        assert health.should_allow_request() is False
        
        time.sleep(0.15)
        
        assert health.should_allow_request() is True
        assert health.state == CircuitState.HALF_OPEN
    
    def test_half_open_closes_after_success_threshold(self):
        """Should close circuit after success threshold in HALF_OPEN."""
        health = ServerHealth(name="test", failure_threshold=1, 
                             success_threshold=2, recovery_timeout=0.1)
        
        health.record_failure("error")
        time.sleep(0.15)
        health.should_allow_request()  # Trigger HALF_OPEN
        
        health.record_success()
        assert health.state == CircuitState.HALF_OPEN
        
        health.record_success()
        assert health.state == CircuitState.CLOSED
    
    def test_half_open_reopens_on_failure(self):
        """Should reopen circuit on any failure in HALF_OPEN."""
        health = ServerHealth(name="test", failure_threshold=1, recovery_timeout=0.1)
        
        health.record_failure("error 1")
        time.sleep(0.15)
        health.should_allow_request()  # Trigger HALF_OPEN
        assert health.state == CircuitState.HALF_OPEN
        
        health.record_failure("error 2")
        assert health.state == CircuitState.OPEN


class TestHealthMonitor:
    """Test suite for HealthMonitor centralized tracking."""
    
    def test_register_creates_health_object(self):
        """Should create health object for new server."""
        monitor = HealthMonitor()
        health = monitor.register("test-server")
        
        assert health is not None
        assert health.name == "test-server"
    
    def test_register_returns_existing(self):
        """Should return existing health object."""
        monitor = HealthMonitor()
        health1 = monitor.register("test-server")
        health2 = monitor.register("test-server")
        
        assert health1 is health2
    
    def test_should_allow_unknown_server(self):
        """Unknown server should be allowed."""
        monitor = HealthMonitor()
        assert monitor.should_allow("unknown") is True
    
    def test_record_success_updates_health(self):
        """Record success should update health metrics."""
        monitor = HealthMonitor()
        monitor.record_success("test-server")
        
        health = monitor.get_health("test-server")
        assert health.total_successes == 1
    
    def test_record_failure_updates_health(self):
        """Record failure should update health metrics."""
        monitor = HealthMonitor()
        monitor.record_failure("test-server", "connection error")
        
        health = monitor.get_health("test-server")
        assert health.total_failures == 1
        assert health.last_error == "connection error"
    
    def test_reset_server_clears_state(self):
        """Reset should restore server to healthy state."""
        monitor = HealthMonitor()
        monitor.register("test-server")
        
        # Simulate failures
        for _ in range(5):
            monitor.record_failure("test-server", "error")
        
        health = monitor.get_health("test-server")
        assert health.state == CircuitState.OPEN
        
        monitor.reset_server("test-server")
        assert health.state == CircuitState.CLOSED
        assert health.consecutive_failures == 0


class TestHealthStatus:
    """Test suite for status reporting."""
    
    def test_get_all_status_returns_dict(self):
        """Should return status dict with all servers."""
        monitor = HealthMonitor()
        monitor.register("server1")
        monitor.register("server2")
        
        status = monitor.get_all_status()
        
        assert "servers" in status
        assert len(status["servers"]) == 2
        assert status["total_servers"] == 2
    
    def test_format_status_returns_string(self):
        """Should return formatted status string."""
        monitor = HealthMonitor()
        monitor.register("test-server")
        
        status = monitor.format_status()
        
        assert isinstance(status, str)
        assert "Health Monitor" in status
    
    def test_server_status_includes_metrics(self):
        """Server status should include key metrics."""
        monitor = HealthMonitor()
        monitor.record_success("test-server")
        monitor.record_failure("test-server", "error")
        
        status = monitor.get_all_status()
        server_status = status["servers"][0]
        
        assert "uptime_percent" in server_status
        assert "total_calls" in server_status
        assert server_status["total_calls"] == 2
