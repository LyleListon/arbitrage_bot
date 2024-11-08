"""Validation schemas for API requests"""

from functools import wraps
from flask import request, jsonify

# Validation schemas for different API endpoints
VALIDATION_SCHEMAS = {
    'toggle_bot': {
        'type': 'object',
        'properties': {
            'action': {'type': 'string', 'enum': ['start', 'stop']}
        },
        'required': ['action']
    },
    'alert': {
        'type': 'object',
        'properties': {
            'token': {'type': 'string'},
            'condition': {'type': 'string', 'enum': ['above', 'below']},
            'price': {'type': 'number', 'minimum': 0}
        },
        'required': ['token', 'condition', 'price']
    },
    'thresholds': {
        'type': 'object',
        'properties': {
            'gas_price_threshold': {'type': 'integer', 'minimum': 1},
            'block_time_threshold': {'type': 'integer', 'minimum': 1},
            'transaction_count_threshold': {'type': 'integer', 'minimum': 1},
            'connection_threshold': {'type': 'integer', 'minimum': 1},
            'price_deviation_threshold': {'type': 'number', 'minimum': 0, 'maximum': 1},
            'error_rate_threshold': {'type': 'number', 'minimum': 0, 'maximum': 1}
        },
        'minProperties': 1
    }
}

class RequestValidator:
    """Request validation decorator"""

    @staticmethod
    def validate_request(schema):
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                try:
                    data = request.get_json()

                    # Basic type validation
                    for field, constraints in schema['properties'].items():
                        if field in data:
                            value = data[field]

                            # Type checking
                            if constraints['type'] == 'string':
                                if not isinstance(value, str):
                                    raise ValueError(f"{field} must be a string")
                                if 'enum' in constraints and value not in constraints['enum']:
                                    raise ValueError(f"{field} must be one of {constraints['enum']}")

                            elif constraints['type'] == 'number':
                                if not isinstance(value, (int, float)):
                                    raise ValueError(f"{field} must be a number")
                                if 'minimum' in constraints and value < constraints['minimum']:
                                    raise ValueError(f"{field} must be >= {constraints['minimum']}")
                                if 'maximum' in constraints and value > constraints['maximum']:
                                    raise ValueError(f"{field} must be <= {constraints['maximum']}")

                            elif constraints['type'] == 'integer':
                                if not isinstance(value, int):
                                    raise ValueError(f"{field} must be an integer")
                                if 'minimum' in constraints and value < constraints['minimum']:
                                    raise ValueError(f"{field} must be >= {constraints['minimum']}")

                    # Required fields check
                    if 'required' in schema:
                        missing = [field for field in schema['required'] if field not in data]
                        if missing:
                            raise ValueError(f"Missing required fields: {', '.join(missing)}")

                    # Minimum properties check
                    if 'minProperties' in schema and len(data) < schema['minProperties']:
                        raise ValueError(f"Request must include at least {schema['minProperties']} property")

                    return f(*args, **kwargs)

                except ValueError as e:
                    return jsonify({
                        'status': 'error',
                        'message': str(e)
                    }), 400
                except Exception as e:
                    return jsonify({
                        'status': 'error',
                        'message': 'Invalid request format'
                    }), 400

            return decorated_function
        return decorator
