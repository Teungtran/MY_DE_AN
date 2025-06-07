import time
import datetime
from typing import Optional

class SnowflakeGenerator:
    DEFAULT_CUSTOM_EPOCH = 1735664400000

    def __init__(self, node_id: int = 1):
        self._node_id = node_id
        self._sequence = 0
        self._last_timestamp = -1
        self._epoch = self.DEFAULT_CUSTOM_EPOCH

    def _wait_next_millis(self, last_timestamp: int) -> int:
        timestamp = int(time.time() * 1000)
        while timestamp <= last_timestamp:
            timestamp = int(time.time() * 1000)
        return timestamp

    def _get_timestamp(self, dt: Optional[datetime.datetime] = None) -> int:
        """
        Converts a datetime object to milliseconds since custom epoch.
        If no datetime is provided, uses current time.
        """
        if dt is None:
            timestamp_ms = int(time.time() * 1000)
        else:
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=datetime.timezone.utc)
            timestamp_ms = int(dt.timestamp() * 1000)
        
        return timestamp_ms - self._epoch

    def generate_snowflake_id(self, time: Optional[datetime.datetime] = None) -> str:
        """
        Generate a unique snowflake ID using the given start_time or current time.
        
        Args:
            start_time: Optional datetime to use for timestamp part of ID
            end_time: Optional datetime (not used in ID generation but provided for API compatibility)
        
        Returns:
            String representation of the snowflake ID
        """
        timestamp = self._get_timestamp(time)
        
        if timestamp < self._last_timestamp:
            timestamp = self._last_timestamp
            
        if timestamp == self._last_timestamp:
            self._sequence = (self._sequence + 1) & 0xFFF  
            if self._sequence == 0:
                timestamp = self._wait_next_millis(self._last_timestamp)
        else:
            self._sequence = 0
            
        self._last_timestamp = timestamp
        
        snowflake_id = ((timestamp & 0x1FFFFFFFFFF) << 22) | (self._node_id << 12) | self._sequence
        return str(snowflake_id)