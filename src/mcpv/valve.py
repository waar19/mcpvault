"""Smart Valve - Token cost protection system for mcpv."""
from .dashboard import dashboard


class SmartValve:
    """Controls context requests to prevent token waste."""
    
    def __init__(self):
        self.served = False
        self.request_count = 0

    def check(self, force: bool) -> tuple[bool, str]:
        """
        Determines if a context request should be allowed.
        Returns: (is_allowed, reason_message)
        """
        if self.served and not force:
            self.request_count += 1
            
            # Log to dashboard
            dashboard.log_blocked_request()
            
            msg = (
                f"🛑 [MCP Vault] Context Blocked (Attempt #{self.request_count}).\n"
                "You already have the context map. Do not request it again.\n"
                "Use 'read_file' for specific details."
            )
            return False, msg
        
        self.served = True
        return True, ""


# Singleton instance
valve = SmartValve()