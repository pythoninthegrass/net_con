import main
import os
import pytest
import requests
import socket
import sys
from requests.exceptions import ConnectionError, RequestException, Timeout
from unittest.mock import MagicMock, Mock, patch


class TestTCPConnection:
    """Test TCP connection functionality."""

    @patch('socket.socket')
    def test_tcp_connection_success(self, mock_socket):
        """Test successful TCP connection."""
        mock_sock = Mock()
        mock_sock.connect_ex.return_value = 0
        mock_socket.return_value = mock_sock

        result = main.test_tcp_connection('google.com', 80)

        assert result is True
        mock_socket.assert_called_once_with(socket.AF_INET, socket.SOCK_STREAM)
        mock_sock.settimeout.assert_called_once_with(5)
        mock_sock.connect_ex.assert_called_once_with(('google.com', 80))
        mock_sock.close.assert_called_once()

    @patch('socket.socket')
    def test_tcp_connection_failure(self, mock_socket):
        """Test failed TCP connection."""
        mock_sock = Mock()
        mock_sock.connect_ex.return_value = 1  # Connection refused
        mock_socket.return_value = mock_sock

        result = main.test_tcp_connection('nonexistent.example', 80)

        assert result is False
        mock_sock.connect_ex.assert_called_once_with(('nonexistent.example', 80))

    @patch('socket.socket')
    def test_tcp_connection_exception(self, mock_socket):
        """Test TCP connection with exception."""
        mock_socket.side_effect = Exception("Network error")

        result = main.test_tcp_connection('error.example', 80)

        assert result is False


class TestHTTPRequest:
    """Test HTTP request functionality."""

    @patch('requests.get')
    def test_http_request_success(self, mock_get):
        """Test successful HTTP request."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.elapsed.total_seconds.return_value = 0.15
        mock_response.headers = {'Content-Type': 'application/json'}
        mock_get.return_value = mock_response

        result = main.test_http_request('https://api.github.com')

        assert result['success'] is True
        assert result['status_code'] == 200
        assert result['response_time'] == 0.15
        assert result['headers']['Content-Type'] == 'application/json'
        mock_get.assert_called_once_with('https://api.github.com', timeout=5)

    @patch('requests.get')
    def test_http_request_timeout(self, mock_get):
        """Test HTTP request timeout."""
        mock_get.side_effect = Timeout("Request timed out")

        result = main.test_http_request('https://slow.example.com')

        assert result['success'] is False
        assert result['error'] == 'Request timeout'

    @patch('requests.get')
    def test_http_request_rate_limited(self, mock_get):
        """Test HTTP request rate limiting."""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.elapsed.total_seconds.return_value = 0.1
        mock_response.headers = {'Retry-After': '60'}
        mock_get.return_value = mock_response

        result = main.test_http_request('https://api.example.com')

        assert result['success'] is False
        assert result['status_code'] == 429
        assert result['error'] == 'Rate limited'
        assert result['response_time'] == 0.1

    @patch('requests.get')
    def test_http_request_server_error(self, mock_get):
        """Test HTTP request server error."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.elapsed.total_seconds.return_value = 0.2
        mock_response.headers = {}
        mock_get.return_value = mock_response

        result = main.test_http_request('https://broken.example.com')

        assert result['success'] is False
        assert result['status_code'] == 500
        assert result['error'] == 'Server error (500)'

    @patch('requests.get')
    def test_http_request_connection_error(self, mock_get):
        """Test HTTP request connection error."""
        mock_get.side_effect = ConnectionError("Connection refused")

        result = main.test_http_request('https://refused.example.com')

        assert result['success'] is False
        assert result['error'] == 'Connection refused'


class TestDNSResolution:
    """Test DNS resolution functionality."""

    @patch('socket.gethostbyname')
    def test_dns_resolution_success(self, mock_gethostbyname):
        """Test successful DNS resolution."""
        mock_gethostbyname.return_value = '142.250.115.102'

        result = main.test_dns_resolution('google.com')

        assert result['success'] is True
        assert result['ip'] == '142.250.115.102'
        mock_gethostbyname.assert_called_once_with('google.com')

    @patch('socket.gethostbyname')
    def test_dns_resolution_failure(self, mock_gethostbyname):
        """Test failed DNS resolution."""
        mock_gethostbyname.side_effect = socket.gaierror("Name resolution failed")

        result = main.test_dns_resolution('nonexistent.invalid')

        assert result['success'] is False
        assert 'Name resolution failed' in result['error']


class TestMainIntegration:
    """Integration tests for the main function."""

    @patch('main.test_dns_resolution')
    @patch('main.test_http_request')
    @patch('main.test_tcp_connection')
    @patch('main.log_result')
    @patch('main.log_section_header')
    def test_main_all_tests_pass(self, mock_log_section, mock_log_result, mock_tcp, mock_http, mock_dns):
        """Test main function when all tests pass."""
        # Mock successful TCP connections
        mock_tcp.return_value = True

        # Mock successful HTTP requests
        mock_http.return_value = {'success': True, 'status_code': 200, 'response_time': 0.15}

        # Mock successful DNS resolutions
        mock_dns.return_value = {'success': True, 'ip': '142.250.115.102'}

        main.main()

        # Verify TCP connection tests
        tcp_calls = mock_tcp.call_args_list
        assert len(tcp_calls) == 5  # 5 TCP tests in main.main()
        expected_tcp_hosts = [
            ('google.com', 80),
            ('google.com', 443),
            ('8.8.8.8', 53),
            ('cloudflare.com', 443),
            ('github.com', 443),
        ]
        for i, (host, port) in enumerate(expected_tcp_hosts):
            assert tcp_calls[i][0] == (host, port)

        # Verify HTTP request tests
        http_calls = mock_http.call_args_list
        assert len(http_calls) == 4  # 4 HTTP tests in main.main()
        expected_urls = ['http://httpbin.org/get', 'https://httpbin.org/get', 'https://www.google.com', 'https://api.github.com']
        for i, url in enumerate(expected_urls):
            assert http_calls[i][0] == (url,)

        # Verify DNS resolution tests
        dns_calls = mock_dns.call_args_list
        assert len(dns_calls) == 3  # 3 DNS tests in main.main()
        expected_hosts = ['google.com', 'github.com', 'stackoverflow.com']
        for i, hostname in enumerate(expected_hosts):
            assert dns_calls[i][0] == (hostname,)

        # Verify logging functions were called
        assert mock_log_section.call_count == 3  # Three sections
        section_calls = [call[0][0] for call in mock_log_section.call_args_list]
        assert "TCP Connectivity Tests" in section_calls
        assert "HTTP/HTTPS Tests" in section_calls
        assert "DNS Resolution Tests" in section_calls

        # Verify log_result was called for each test
        assert mock_log_result.call_count == 12  # 5 TCP + 4 HTTP + 3 DNS

    @patch('main.test_dns_resolution')
    @patch('main.test_http_request')
    @patch('main.test_tcp_connection')
    @patch('main.log_result')
    @patch('main.log_section_header')
    def test_main_mixed_results(self, mock_log_section, mock_log_result, mock_tcp, mock_http, mock_dns):
        """Test main function with mixed pass/fail results."""
        # Mix of successful and failed TCP connections
        mock_tcp.side_effect = [True, False, True, False, True]

        # Mix of successful and failed HTTP requests
        mock_http.side_effect = [
            {'success': True, 'status_code': 200, 'response_time': 0.1},
            {'success': False, 'error': 'Connection timeout'},
            {'success': True, 'status_code': 503, 'response_time': 0.2},
            {'success': True, 'status_code': 200, 'response_time': 0.05},
        ]

        # Mix of successful and failed DNS resolutions
        mock_dns.side_effect = [
            {'success': True, 'ip': '142.250.115.102'},
            {'success': False, 'error': 'Name resolution failed'},
            {'success': True, 'ip': '104.18.32.7'},
        ]

        main.main()

        # Verify that logging functions were called with both pass and fail results
        assert mock_log_result.call_count == 12  # 5 TCP + 4 HTTP + 3 DNS

        # Check that we have both pass and fail results in the log_result calls
        log_calls = mock_log_result.call_args_list
        pass_calls = [call for call in log_calls if call[0][2]]  # status parameter is True
        fail_calls = [call for call in log_calls if not call[0][2]]  # status parameter is False

        assert len(pass_calls) > 0, "Should have some PASS results"
        assert len(fail_calls) > 0, "Should have some FAIL results"

    @patch('main.test_dns_resolution')
    @patch('main.test_http_request')
    @patch('main.test_tcp_connection')
    @patch('main.log_result')
    @patch('main.log_section_header')
    def test_main_error_handling(self, mock_log_section, mock_log_result, mock_tcp, mock_http, mock_dns):
        """Test main function handles exceptions gracefully."""
        # Mock functions to return False/error instead of raising exceptions
        mock_tcp.return_value = False
        mock_http.return_value = {'success': False, 'error': 'HTTP error'}
        mock_dns.return_value = {'success': False, 'error': 'DNS error'}

        # Should not raise exception - main.main() handles errors by logging them
        try:
            main.main()
        except Exception as e:
            pytest.fail(f"main.main() should handle errors gracefully, but raised: {e}")

        # Verify error results are logged
        assert mock_log_result.call_count == 12  # 5 TCP + 4 HTTP + 3 DNS
        log_calls = mock_log_result.call_args_list
        fail_calls = [call for call in log_calls if not call[0][2]]  # status parameter is False
        assert len(fail_calls) > 0, "Should have FAIL results for errors"


class TestEndToEndScenarios:
    """End-to-end test scenarios simulating real network conditions."""

    @patch('main.test_dns_resolution')
    @patch('main.test_http_request')
    @patch('main.test_tcp_connection')
    def test_network_connectivity_scenario_all_good(self, mock_tcp, mock_http, mock_dns):
        """Simulate scenario where all network connectivity is working."""
        mock_tcp.return_value = True
        mock_http.return_value = {'success': True, 'status_code': 200, 'response_time': 0.1}
        mock_dns.return_value = {'success': True, 'ip': '8.8.8.8'}

        main.main()

        # All mocks should be called appropriate number of times
        assert mock_tcp.call_count == 5
        assert mock_http.call_count == 4
        assert mock_dns.call_count == 3

    @patch('main.test_dns_resolution')
    @patch('main.test_http_request')
    @patch('main.test_tcp_connection')
    def test_network_connectivity_scenario_dns_issues(self, mock_tcp, mock_http, mock_dns):
        """Simulate scenario where DNS resolution fails."""
        mock_tcp.return_value = False  # TCP will fail due to DNS issues
        mock_http.return_value = {'success': False, 'error': 'Name resolution failed'}
        mock_dns.return_value = {'success': False, 'error': 'DNS server unreachable'}

        main.main()

        # All tests should still be attempted
        assert mock_tcp.call_count == 5
        assert mock_http.call_count == 4
        assert mock_dns.call_count == 3


if __name__ == "__main__":
    pytest.main([__file__])
