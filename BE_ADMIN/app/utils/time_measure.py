from functools import wraps
import time


def measure_time(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()  # Capture the start time
        result = await func(*args, **kwargs)  # Call the wrapped function
        end_time = time.time()  # Capture the end time
        execution_time = end_time - start_time  # Calculate the execution time
        print(f"{func.__name__} took {execution_time:.4f} seconds")
        return result

    return wrapper
