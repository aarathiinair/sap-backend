
from logging_config import logger
from functools import wraps
import asyncio

def log_function_call(func):
    if asyncio.iscoroutinefunction(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            logger.debug(f"Calling {func.__name__} with args={args}, kwargs={kwargs}")
            try:
                result = await func(*args, **kwargs)
                logger.debug(f"{func.__name__} returned {result}")
                logger.info(f"{func.__name__} completed successfully")
                return result
            except Exception as e:
                logger.exception(f"Exception in {func.__name__}: {e}")
                raise
        return wrapper
    else:
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger.debug(f"Calling {func.__name__} with args={args}, kwargs={kwargs}")
            try:
                result = func(*args, **kwargs)
                logger.debug(f"{func.__name__} returned {result}")
                logger.info(f"{func.__name__} completed successfully")
                return result
            except Exception as e:
                logger.exception(f"Exception in {func.__name__}: {e}")
                raise
        return wrapper