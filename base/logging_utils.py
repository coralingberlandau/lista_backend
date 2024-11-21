import json
import logging
import os
import platform
import time
import traceback
from functools import wraps
from logging.handlers import RotatingFileHandler

LOG_FILE = "logs/application.log"

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "time": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
            "function": record.funcName,
            "filename": record.filename,
            "line": record.lineno,
            "host": platform.node(),
            "system": f"{platform.system()} {platform.release()}",
            "python_version": platform.python_version(),
        }
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        
        dynamic_info = getattr(record, 'dynamic_info', None)
        if dynamic_info and isinstance(dynamic_info, dict):  
            log_record.update(dynamic_info)
        else:
            log_record["dynamic_info"] = "No dynamic info provided" 

        return json.dumps(log_record)


def setup_logger(log_file, level=logging.DEBUG):
    logger = logging.getLogger("application_logger")
    if not logger.hasHandlers():
        logger.setLevel(level)
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        handler = RotatingFileHandler(log_file, maxBytes=5 * 1024 * 1024, backupCount=3)
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)
    return logger


def log_api_call(url, method, status_code, response_time, payload=None):
    logger = setup_logger(LOG_FILE)
    logger.info({
        "event": "api_call",
        "url": url,
        "method": method,
        "status_code": status_code,
        "response_time": f"{response_time:.2f}s",
        "payload": payload,
    })


def log_deletion(user_id, object_id, object_type):
    logger = setup_logger(LOG_FILE)
    logger.warning({
        "event": "deletion",
        "user_id": user_id,
        "object_id": object_id,
        "object_type": object_type,
    })


def log(user_id=None, object_id=None):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = setup_logger(LOG_FILE)
            function_name = func.__name__
            file_name = os.path.basename(func.__code__.co_filename)
            start_time = time.time()

            request = args[1] if len(args) > 1 else None
            user_info = f"User ID: {user_id}" if user_id else "No User Info"
            object_info = f"Object ID: {object_id}" if object_id else "No Object Info"
            
            if request and hasattr(request, 'META'):
                ip_address = request.META.get('REMOTE_ADDR', 'Unknown IP')
                method = request.method if hasattr(request, 'method') else 'No Method'
                headers = request.headers if hasattr(request, 'headers') else 'No Headers'
            else:
                ip_address = 'No Request Info'
                method = 'No Method'
                headers = 'No Headers'

            logger.debug({
                "event": "function_call",
                "function": function_name,
                "file": file_name,
                "user_info": user_info,
                "object_info": object_info,
                "ip": ip_address,
                "method": method,
                "headers": dict(headers) if headers != 'No Headers' else "No Headers",
            })

            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time

                dynamic_info = {
                    "extra_info_key": "additional_value", 
                    "another_field": "another_value"
                }
                if dynamic_info is None:  
                    dynamic_info = {"message": "No additional dynamic information"}

                logger.info({
                    "event": "function_success",
                    "function": function_name,
                    "execution_time": execution_time,
                    "result": str(result),
                    "dynamic_info": dynamic_info  
                })
                return result

            except Exception as e:
                logger.error({
                    "event": "error",
                    "function": function_name,
                    "error": str(e),
                    "stack_trace": traceback.format_exc(limit=3), 
                })
                raise

        return wrapper
    return decorator
