from functools import wraps
from .responses import internal_error_response

def handle_api_errors(error_message=None):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except Exception as e:
                # Use custom error message or default to function name
                base_message = error_message or f"Error in {f.__name__.replace('_', ' ')}"
                return internal_error_response(f"{base_message}: {str(e)}")
        return decorated_function
    return decorator