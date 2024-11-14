import logging
import os
from functools import wraps
import traceback


LOG_FILE = "logs/application.log"

# הגדרת הלוגר
def setup_logger(log_file):
    logger = logging.getLogger("application_logger")
    if not logger.hasHandlers():
        logger.setLevel(logging.DEBUG)  # הגדרת רמת הלוגים ל-Debug כדי לכלול את כל הרמות
        handler = logging.FileHandler(log_file)
        formatter = logging.Formatter('%(asctime)s - %(filename)s - %(funcName)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

# דקורטור ללוג (אפשרי לקרוא לו ככה גם בלי פרמטרים)
def log(user_id=None, object_id=None):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = setup_logger(LOG_FILE)

            function_name = func.__name__
            file_name = os.path.basename(func.__code__.co_filename)
            
            # אם לא נשלחו פרמטרים, תוצג הודעה ברירת מחדל
            user_info = f"User ID: {user_id}" if user_id else "Unknown User"
            object_info = f"Object ID: {object_id}" if object_id else "No Object ID"
            
            # רשום את קריאת הפונקציה עם כל המידע
            logger.debug(f"Calling function {function_name} in {file_name} with args: {args}, kwargs: {kwargs} | {user_info} | {object_info}")

            try:
                result = func(*args, **kwargs)

                # לוג של הצלחה לאחר ביצוע הפונקציה
                logger.info(f"Function {function_name} executed successfully in {file_name} | {user_info} | {object_info} | Result: {result}")
                return result

            except ValueError as ve:
                # לוג של אזהרה במקרה של Exception מסויים
                logger.warning(f"Warning in {function_name}: {str(ve)} | {user_info} | {object_info} | Args: {args}, Kwargs: {kwargs}")
                return None

            except Exception as e:
                # לוג של שגיאה
                logger.error(f"Error in {function_name}: {str(e)} | {user_info} | {object_info} | Args: {args}, Kwargs: {kwargs}")
                logger.error(f"Stack Trace: {traceback.format_exc()}")  # להוסיף את ה-Stack Trace בשגיאות
                raise  # להמשיך לזרוק את השגיאה

            except SystemExit as se:
                # לוג של יציאה קריטית
                logger.critical(f"Critical system exit in {function_name}: {str(se)} | {user_info} | {object_info}")
                raise  # להמשיך עם SystemExit

        return wrapper
    return decorator
