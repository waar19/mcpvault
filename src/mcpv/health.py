"""Health Monitor - Circuit breaker and auto-recovery for upstream servers.

This module implements the Circuit Breaker pattern to handle upstream server
failures gracefully. It prevents cascading failures by temporarily stopping
calls to failing servers.

States:
- CLOSED: Normal operation, all calls go through
- OPEN: Server is failing, calls are blocked
- HALF_OPEN: Testing if server has recovered

Security considerations:
- Health checks use minimal resources
- State transitions are logged for auditing
- No sensitive data exposed in health status
"""
import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Optional, Any
from threading import Lock

logger = logging.getLogger("mcpv-health")


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Blocking calls (server is down)
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class ServerHealth:
    """Tracks health metrics for an upstream server."""
    name: str
    state: CircuitState = CircuitState.CLOSED
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    last_failure_time: Optional[float] = None
    last_success_time: Optional[float] = None
    last_check_time: Optional[float] = None
    total_calls: int = 0
    total_failures: int = 0
    total_successes: int = 0
    last_error: Optional[str] = None
    
    # Circuit breaker thresholds
    failure_threshold: int = 3  # Failures before opening circuit
    success_threshold: int = 2  # Successes before closing circuit
    recovery_timeout: float = 30.0  # Seconds before trying HALF_OPEN
    
    def record_success(self) -> None:
        """Record a successful call."""
        self.total_calls += 1
        self.total_successes += 1
        self.consecutive_successes += 1
        self.consecutive_failures = 0
        self.last_success_time = time.time()
        self.last_check_time = time.time()
        self.last_error = None
        
        # State transition: HALF_OPEN -> CLOSED after threshold
        if self.state == CircuitState.HALF_OPEN:
            if self.consecutive_successes >= self.success_threshold:
                self._transition_to(CircuitState.CLOSED)
    
    def record_failure(self, error: str) -> None:
        """Record a failed call."""
        self.total_calls += 1
        self.total_failures += 1
        self.consecutive_failures += 1
        self.consecutive_successes = 0
        self.last_failure_time = time.time()
        self.last_check_time = time.time()
        self.last_error = error[:200]  # Truncate for safety
        
        # State transition: CLOSED -> OPEN after threshold
        if self.state == CircuitState.CLOSED:
            if self.consecutive_failures >= self.failure_threshold:
                self._transition_to(CircuitState.OPEN)
        
        # State transition: HALF_OPEN -> OPEN on any failure
        elif self.state == CircuitState.HALF_OPEN:
            self._transition_to(CircuitState.OPEN)
    
    def should_allow_request(self) -> bool:
        """Check if a request should be allowed through."""
        if self.state == CircuitState.CLOSED:
            return True
        
        if self.state == CircuitState.OPEN:
            # Check if recovery timeout has passed
            if self.last_failure_time:
                elapsed = time.time() - self.last_failure_time
                if elapsed >= self.recovery_timeout:
                    self._transition_to(CircuitState.HALF_OPEN)
                    return True
            return False
        
        # HALF_OPEN: allow limited requests to test recovery
        return True
    
    def _transition_to(self, new_state: CircuitState) -> None:
        """Transition to a new state with logging."""
        old_state = self.state
        self.state = new_state
        logger.info(f"Circuit breaker [{self.name}]: {old_state.value} -> {new_state.value}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current health status as dict."""
        uptime_pct = (
            (self.total_successes / self.total_calls * 100) 
            if self.total_calls > 0 else 100.0
        )
        
        return {
            "name": self.name,
            "state": self.state.value,
            "uptime_percent": round(uptime_pct, 1),
            "total_calls": self.total_calls,
            "consecutive_failures": self.consecutive_failures,
            "last_error": self.last_error,
            "last_success": (
                datetime.fromtimestamp(self.last_success_time).isoformat()
                if self.last_success_time else None
            ),
            "last_failure": (
                datetime.fromtimestamp(self.last_failure_time).isoformat()
                if self.last_failure_time else None
            ),
        }
    
    def reset(self) -> None:
        """Reset health metrics (for manual recovery)."""
        self.state = CircuitState.CLOSED
        self.consecutive_failures = 0
        self.consecutive_successes = 0
        self.last_error = None
        logger.info(f"Circuit breaker [{self.name}]: RESET to CLOSED")


class HealthMonitor:
    """Centralized health monitoring for all upstream servers.
    
    Thread-safe singleton that tracks health of all registered servers
    and provides circuit breaker functionality.
    
    Usage:
        # Register server
        monitor.register("context7")
        
        # Check before calling
        if monitor.should_allow("context7"):
            try:
                result = await server.call_tool(...)
                monitor.record_success("context7")
            except Exception as e:
                monitor.record_failure("context7", str(e))
    """
    
    def __init__(self):
        self._servers: Dict[str, ServerHealth] = {}
        self._lock = Lock()
    
    def register(self, server_name: str) -> ServerHealth:
        """Register a server for health tracking."""
        with self._lock:
            if server_name not in self._servers:
                self._servers[server_name] = ServerHealth(name=server_name)
                logger.debug(f"Registered server for health tracking: {server_name}")
            return self._servers[server_name]
    
    def get_health(self, server_name: str) -> Optional[ServerHealth]:
        """Get health object for a server."""
        return self._servers.get(server_name)
    
    def should_allow(self, server_name: str) -> bool:
        """Check if request to server should be allowed."""
        health = self._servers.get(server_name)
        if not health:
            return True  # Unknown servers are allowed
        return health.should_allow_request()
    
    def record_success(self, server_name: str) -> None:
        """Record successful call to server."""
        health = self.register(server_name)
        health.record_success()
    
    def record_failure(self, server_name: str, error: str) -> None:
        """Record failed call to server."""
        health = self.register(server_name)
        health.record_failure(error)
    
    def reset_server(self, server_name: str) -> bool:
        """Reset a server's circuit breaker."""
        health = self._servers.get(server_name)
        if health:
            health.reset()
            return True
        return False
    
    def get_all_status(self) -> Dict[str, Any]:
        """Get health status of all servers."""
        with self._lock:
            return {
                "servers": [h.get_status() for h in self._servers.values()],
                "total_servers": len(self._servers),
                "healthy_count": sum(
                    1 for h in self._servers.values() 
                    if h.state == CircuitState.CLOSED
                ),
                "unhealthy_count": sum(
                    1 for h in self._servers.values() 
                    if h.state == CircuitState.OPEN
                ),
            }
    
    def format_status(self) -> str:
        """Format health status for CLI display."""
        status = self.get_all_status()
        
        lines = [
            "🏥 Server Health Monitor",
            "─" * 40,
            f"🌐 Total Servers: {status['total_servers']}",
            f"✅ Healthy: {status['healthy_count']}",
            f"❌ Unhealthy: {status['unhealthy_count']}",
        ]
        
        if status['servers']:
            lines.append("\n📋 Server Details:")
            for srv in status['servers']:
                icon = {
                    "closed": "🟢",
                    "open": "🔴",
                    "half_open": "🟡"
                }.get(srv['state'], "⚪")
                
                lines.append(f"   {icon} {srv['name']}")
                lines.append(f"      State: {srv['state']} | Uptime: {srv['uptime_percent']}%")
                if srv['last_error']:
                    lines.append(f"      Last Error: {srv['last_error'][:50]}...")
        
        return "\n".join(lines)


# Singleton instance
monitor = HealthMonitor()
