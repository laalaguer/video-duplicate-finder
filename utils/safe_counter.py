''' SafeCounter implments a thread-safe counter (starts from 1) '''
import threading


class SafeCounter:
    """Thread-safe counter that increments and returns sequential integers"""
    
    def __init__(self):
        self._value = 0
        self._lock = threading.Lock()
    
    def get_int(self) -> int:
        """Get the next integer in sequence (thread-safe)
        
        Returns:
            int: The next sequential integer starting from 1
        """
        with self._lock:
            self._value += 1
            return self._value
    
    def peek_int(self) -> int:
        ''' Peek the top of the counter, maybe not accurate '''
        return self._value