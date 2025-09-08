#!/usr/bin/env -S uv run --script

# /// script
# requires-python = ">=3.13,<3.14"
# dependencies = [
#     "requests>=2.32.5",
# ]
# [tool.uv]
# exclude-newer = "2025-09-30T00:00:00Z"
# ///

# pyright: reportMissingImports=false

import json
import logging
import platform
import requests
import socket
import sys
from datetime import datetime

IS_DARWIN = platform.system() == 'Darwin'

if not IS_DARWIN:
    logging.basicConfig(level=logging.INFO, format='%(message)s', handlers=[logging.StreamHandler(sys.stdout)])
    logger = logging.getLogger(__name__)


def log_result(test_type, target, status, details=None):
    """Log test results in platform-appropriate format"""
    timestamp = datetime.now().isoformat()

    if IS_DARWIN:
        if test_type == "tcp":
            host, port = target
            status_text = "✓ PASS" if status else "✗ FAIL"
            target_str = f"{host}:{port}"
            print(f"{target_str:<28} {status_text}")
        elif test_type == "http":
            if status and details:
                print(f"{target:<28} ✓ PASS ({details['status_code']}, {details['response_time']:.2f}s)")
            else:
                print(f"{target:<28} ✗ FAIL ({details.get('error', 'Unknown error')})")
        elif test_type == "dns":
            if status and details:
                print(f"{target:<28} ✓ PASS ({details['ip']})")
            else:
                print(f"{target:<28} ✗ FAIL ({details.get('error', 'Unknown error')})")
    else:
        log_entry = {
            "timestamp": timestamp,
            "test_type": test_type,
            "target": target if isinstance(target, str) else f"{target[0]}:{target[1]}",
            "status": "pass" if status else "fail",
        }

        if details:
            log_entry.update(details)

        logger.info(json.dumps(log_entry))


def log_section_header(section_name):
    """Log section headers in platform-appropriate format"""
    if IS_DARWIN:
        print(f"\n=== {section_name} ===")
    else:
        logger.info(json.dumps({"timestamp": datetime.now().isoformat(), "event_type": "section_start", "section": section_name}))


def test_tcp_connection(host, port, timeout=5):
    """Test TCP connection to host:port"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception:
        return False


def test_http_request(url, timeout=5):
    """Test HTTP/HTTPS request"""
    try:
        response = requests.get(url, timeout=timeout)

        # Consider 2xx and 3xx as successful, but include status code info
        success = 200 <= response.status_code < 400

        result = {
            'success': success,
            'status_code': response.status_code,
            'response_time': response.elapsed.total_seconds(),
            'headers': dict(response.headers),
        }

        # Add error info for non-successful status codes
        if not success:
            if response.status_code == 429:
                result['error'] = 'Rate limited'
            elif response.status_code >= 500:
                result['error'] = f'Server error ({response.status_code})'
            elif response.status_code >= 400:
                result['error'] = f'Client error ({response.status_code})'
            else:
                result['error'] = f'Unexpected status ({response.status_code})'

        return result
    except requests.exceptions.Timeout:
        return {'success': False, 'error': 'Request timeout'}
    except requests.exceptions.ConnectionError as e:
        if 'timeout' in str(e).lower():
            return {'success': False, 'error': 'Connection timeout'}
        elif 'refused' in str(e).lower():
            return {'success': False, 'error': 'Connection refused'}
        else:
            return {'success': False, 'error': 'Connection error'}
    except requests.exceptions.RequestException:
        return {'success': False, 'error': 'Request failed'}
    except Exception as e:
        return {'success': False, 'error': f'Unexpected error: {type(e).__name__}'}


def test_dns_resolution(hostname):
    """Test DNS resolution"""
    try:
        ip = socket.gethostbyname(hostname)
        return {'success': True, 'ip': ip}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def main():
    """Run comprehensive connectivity tests"""
    test_hosts = [('google.com', 80), ('google.com', 443), ('8.8.8.8', 53), ('cloudflare.com', 443), ('github.com', 443)]
    http_urls = ['http://httpbin.org/get', 'https://httpbin.org/get', 'https://www.google.com', 'https://api.github.com']
    dns_hosts = ['google.com', 'github.com', 'stackoverflow.com']

    log_section_header("TCP Connectivity Tests")
    for host, port in test_hosts:
        result = test_tcp_connection(host, port)
        log_result("tcp", (host, port), result)

    log_section_header("HTTP/HTTPS Tests")
    for url in http_urls:
        result = test_http_request(url)
        log_result("http", url, result['success'], result)

    log_section_header("DNS Resolution Tests")
    for hostname in dns_hosts:
        result = test_dns_resolution(hostname)
        log_result("dns", hostname, result['success'], result)


if __name__ == "__main__":
    main()
