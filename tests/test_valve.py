"""Tests for SmartValve - token cost protection system."""
import pytest
from mcpv.valve import SmartValve


class TestSmartValve:
    """Test suite for SmartValve functionality."""
    
    def test_first_request_allowed(self):
        """First context request should always be allowed."""
        valve = SmartValve()
        
        allowed, msg = valve.check(force=False)
        
        assert allowed is True
        assert msg == ""
    
    def test_second_request_blocked(self):
        """Subsequent requests without force should be blocked."""
        valve = SmartValve()
        
        # First request
        valve.check(force=False)
        
        # Second request should be blocked
        allowed, msg = valve.check(force=False)
        
        assert allowed is False
        assert "Blocked" in msg
        assert valve.request_count == 1
    
    def test_force_bypass_after_block(self):
        """Force flag should allow request even after initial serve."""
        valve = SmartValve()
        
        # First request
        valve.check(force=False)
        
        # Force request should be allowed
        allowed, msg = valve.check(force=True)
        
        assert allowed is True
        assert msg == ""
    
    def test_multiple_blocks_increment_counter(self):
        """Each blocked request should increment the counter."""
        valve = SmartValve()
        
        # First allowed request
        valve.check(force=False)
        
        # Multiple blocked requests
        for i in range(5):
            allowed, msg = valve.check(force=False)
            assert allowed is False
        
        assert valve.request_count == 5
    
    def test_block_message_contains_attempt_number(self):
        """Block message should show which attempt number it is."""
        valve = SmartValve()
        
        valve.check(force=False)  # First allowed
        valve.check(force=False)  # First block
        allowed, msg = valve.check(force=False)  # Second block
        
        assert "#2" in msg  # Should show attempt #2
    
    def test_initial_state(self):
        """Valve should start in unserved state."""
        valve = SmartValve()
        
        assert valve.served is False
        assert valve.request_count == 0
