"""
Tests for Dashboard Validation System

@CONTEXT: Test suite for input validation implementation
@LAST_POINT: 2024-01-31 - Initial test implementation
"""

import unittest
import json
from flask import Flask
from dashboard.validation import (
    Validator,
    RequestValidator,
    ValidationError,
    VALIDATION_SCHEMAS
)

class TestValidator(unittest.TestCase):
    """Test cases for base Validator class"""
    
    def test_validate_number(self):
        """Test numeric validation"""
        # Test valid cases
        self.assertTrue(Validator.validate_number(42))
        self.assertTrue(Validator.validate_number(3.14))
        self.assertTrue(Validator.validate_number(0))
        self.assertTrue(Validator.validate_number(-1))
        
        # Test range validation
        self.assertTrue(Validator.validate_number(5, min_val=0, max_val=10))
        
        # Test invalid cases
        with self.assertRaises(ValidationError):
            Validator.validate_number("not a number")
        with self.assertRaises(ValidationError):
            Validator.validate_number(11, max_val=10)
        with self.assertRaises(ValidationError):
            Validator.validate_number(-1, min_val=0)
    
    def test_validate_string(self):
        """Test string validation"""
        # Test valid cases
        self.assertTrue(Validator.validate_string("test"))
        self.assertTrue(Validator.validate_string(""))
        self.assertTrue(Validator.validate_string("a" * 10, max_length=10))
        
        # Test pattern validation
        self.assertTrue(Validator.validate_string("start", pattern="^(start|stop)$"))
        
        # Test invalid cases
        with self.assertRaises(ValidationError):
            Validator.validate_string(42)
        with self.assertRaises(ValidationError):
            Validator.validate_string("", min_length=1)
        with self.assertRaises(ValidationError):
            Validator.validate_string("toolong", max_length=5)
        with self.assertRaises(ValidationError):
            Validator.validate_string("invalid", pattern="^(start|stop)$")
    
    def test_validate_boolean(self):
        """Test boolean validation"""
        # Test valid cases
        self.assertTrue(Validator.validate_boolean(True))
        self.assertTrue(Validator.validate_boolean(False))
        
        # Test invalid cases
        with self.assertRaises(ValidationError):
            Validator.validate_boolean("true")
        with self.assertRaises(ValidationError):
            Validator.validate_boolean(1)
    
    def test_validate_list(self):
        """Test list validation"""
        # Test valid cases
        self.assertTrue(Validator.validate_list([1, 2, 3], int))
        self.assertTrue(Validator.validate_list(["a", "b"], str))
        self.assertTrue(Validator.validate_list([], str))
        
        # Test length validation
        self.assertTrue(Validator.validate_list([1], int, min_length=1))
        self.assertTrue(Validator.validate_list([1, 2], int, max_length=2))
        
        # Test invalid cases
        with self.assertRaises(ValidationError):
            Validator.validate_list("not a list", str)
        with self.assertRaises(ValidationError):
            Validator.validate_list([1, "2", 3], int)
        with self.assertRaises(ValidationError):
            Validator.validate_list([], int, min_length=1)
        with self.assertRaises(ValidationError):
            Validator.validate_list([1, 2, 3], int, max_length=2)

class TestRequestValidator(unittest.TestCase):
    """Test cases for RequestValidator decorator"""
    
    def setUp(self):
        """Set up test Flask application"""
        self.app = Flask(__name__)
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        
        # Test endpoint with validation
        @self.app.route('/test', methods=['POST'])
        @RequestValidator.validate_request(VALIDATION_SCHEMAS['toggle_bot'])
        def test_endpoint():
            return json.dumps({'status': 'success'})
    
    def test_valid_request(self):
        """Test valid request validation"""
        response = self.client.post(
            '/test',
            json={'action': 'start'},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'success')
    
    def test_invalid_request(self):
        """Test invalid request validation"""
        # Test missing required field
        response = self.client.post(
            '/test',
            json={},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        
        # Test invalid action value
        response = self.client.post(
            '/test',
            json={'action': 'invalid'},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        
        # Test invalid content type
        response = self.client.post(
            '/test',
            data='not json'
        )
        self.assertEqual(response.status_code, 400)

if __name__ == '__main__':
    unittest.main()
