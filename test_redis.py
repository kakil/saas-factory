#!/usr/bin/env python3
"""
Redis Connection Test Script

This script tests the connection to the Redis server and performs basic operations
to verify that Redis is functioning correctly.
"""

import asyncio
import redis.asyncio as redis
import sys

async def test_redis_connection():
    """Test Redis connection and basic operations."""
    print("Testing Redis connection...")
    
    try:
        # Connect to Redis
        r = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)
        
        # Ping to test connection
        pong = await r.ping()
        print(f"Connection test: {'PASSED' if pong else 'FAILED'}")
        
        if not pong:
            print("ERROR: Redis server did not respond to ping.")
            return False
            
        # Set a value
        await r.set("test_key", "test_value")
        print("Set value test: PASSED")
        
        # Get the value back
        value = await r.get("test_key")
        print(f"Get value test: {'PASSED' if value == 'test_value' else 'FAILED'}")
        
        if value != "test_value":
            print(f"ERROR: Expected 'test_value', got '{value}'")
            return False
            
        # Delete the key
        await r.delete("test_key")
        print("Delete key test: PASSED")
        
        # Check it's gone
        value = await r.get("test_key")
        print(f"Key deleted test: {'PASSED' if value is None else 'FAILED'}")
        
        if value is not None:
            print(f"ERROR: Key should be deleted but returned '{value}'")
            return False
        
        print("\nAll Redis tests PASSED!")
        return True
        
    except redis.ConnectionError as e:
        print(f"Connection Error: {e}")
        print("\nDiagnostic information:")
        print("1. Ensure Redis container is running: docker-compose ps")
        print("2. Check Redis logs: docker-compose logs redis")
        print("3. Verify Redis is bound to 0.0.0.0 and not just 127.0.0.1")
        print("4. Check if port 6379 is exposed correctly in docker-compose.yml")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False
    finally:
        try:
            await r.close()
        except:
            pass

if __name__ == "__main__":
    result = asyncio.run(test_redis_connection())
    sys.exit(0 if result else 1)