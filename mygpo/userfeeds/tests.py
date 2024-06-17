import unittest
from unittest.mock import patch, MagicMock
from django.http import HttpRequest
from .auth import view_or_basicauth  # Adjust the import path based on your project structure
from mygpo.userfeeds import auth
import base64

class TestViewOrBasicAuth(unittest.TestCase):

    @patch('mygpo.userfeeds.auth.get_user_model')
    @patch('mygpo.userfeeds.auth.get_object_or_404')
    def test_view_or_basicauth_no_token_required(self, mock_get_object_or_404, mock_get_user_model):
        # Setup
        branch_coverage = [False] * 9

        mock_view = MagicMock()
        mock_request = HttpRequest()
        mock_user = MagicMock()
        mock_user.username = 'testuser'
        mock_user.some_token_name = ""  # Assuming 'some_token_name' is the token field
        mock_get_user_model.return_value = MagicMock(return_value=mock_user)
        mock_get_object_or_404.return_value = mock_user
        auth.getattr = MagicMock()
        auth.getattr.return_value = ""

        # Attempt at no authorisation needed (empty token)
        response = view_or_basicauth(branch_coverage, mock_view, mock_request, 'testuser', 'some_token_name')
        self.assertIsNotNone(response)

        # Attempt at authorisation needed reply
        auth.getattr.return_value = "some_token"
        response = view_or_basicauth(branch_coverage, mock_view, mock_request, 'testuser', 'some_token_name')
        self.assertEqual(response.status_code, 401)

        # Attempt at HTTP_AUTHORISATION in request.META
        username = 'user'
        password = 'pass'
        credentials = f'{username}:{password}'

        # Encode credentials into base64
        encoded_credentials = base64.b64encode(credentials.encode()).decode()

        # Set the http authorization header
        mock_request.META['HTTP_AUTHORIZATION'] = f'Basic {encoded_credentials}'

        result = view_or_basicauth(branch_coverage, mock_view, mock_request, 'testuser', 'some_token_name')
        self.assertIsNotNone(result)

        # Attempt at AUTHORISATION in request.META
        mock_request.META['AUTHORIZATION'] = f'Basic {encoded_credentials}'

        result = view_or_basicauth(branch_coverage, mock_view, mock_request, 'testuser', 'some_token_name')
        self.assertIsNotNone(result)

        # Attempt at successful authentication
        auth.getattr.return_value = "token1"

        username = 'testuser'
        password = 'token1'
        credentials = f'{username}:{password}'

        # Encode credentials into base64
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        mock_request.META['AUTHORIZATION'] = f'Basic {encoded_credentials}'

        result = view_or_basicauth(branch_coverage, mock_view, mock_request, 'testuser', 'some_token_name')
        self.assertEqual(result.status_code, 401)

        total = 9
        num_taken = 0
        with open('/home/hussein/sep/fork/mygpo/view_or_basicauth_coverage.txt', 'w') as file:
            file.write(f"FILE: userfeeds/auth.py\nMethod: view_or_basic_auth\n\n")
            for index, coverage in enumerate(branch_coverage):
                if coverage:
                    file.write(f"Branch {index} was taken\n")
                    num_taken += 1
                else:
                    file.write(f"Branch {index} was not taken\n")
            file.write(f"\n")
            coverage_level = num_taken/total * 100
            file.write(f"Total coverage: {coverage_level}%\n")

    # Additional tests can be added here to cover other branches like:
    # - Token is required but not provided
    # - Token is required and provided correctly
    # - Token is required but provided incorrectly

if __name__ == '__main__':
    unittest.main()
