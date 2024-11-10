import logging
import os
from functools import wraps

LOG_FILE = "logs/application.log"

def setup_logger(log_file):
    logger = logging.getLogger("application_logger")
    if not logger.hasHandlers():
        logger.setLevel(logging.DEBUG)  
        handler = logging.FileHandler(log_file)
        formatter = logging.Formatter('%(asctime)s - %(filename)s - %(funcName)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

def log(user_id=None, object_id=None):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = setup_logger(LOG_FILE)

            function_name = func.__name__
            file_name = os.path.basename(func.__code__.co_filename)
            user_info = f"User ID: {user_id}" if user_id else "Unknown User"
            object_info = f"Object ID: {object_id}" if object_id else "No Object ID"
            

            logger.debug(f"Calling {function_name} in {file_name} with args: {args}, kwargs: {kwargs} | {user_info} | {object_info}")
            
            try:
                result = func(*args, **kwargs)
                
                logger.info(f"Function {function_name} executed successfully in {file_name} | {user_info} | {object_info}")
                return result
            
            except ValueError as ve:
                logger.warning(f"Warning in {function_name}: {str(ve)} | {user_info} | {object_info}")
            
            except Exception as e:

                logger.error(f"Error in {function_name}: {str(e)} | {user_info} | {object_info}")
                raise
            
            except SystemExit as se:
                logger.critical(f"Critical system exit in {function_name}: {str(se)} | {user_info} | {object_info}")
                raise

        return wrapper
    return decorator
