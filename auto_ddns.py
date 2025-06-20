#!/usr/bin/env python3
"""
Auto-DDNS for Home Laboratories
Automatically updates Cloudflare DNS A records with current public IP
"""

import os
import sys
import json
import time
import logging
import requests
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv
import re

# Configuration
SCRIPT_DIR = Path(__file__).parent
CONFIG_DIR = SCRIPT_DIR / "config"
LOGS_DIR = SCRIPT_DIR / "logs"
CONFIG_FILE = CONFIG_DIR / "config.json"
ENV_FILE = CONFIG_DIR / ".env"
METRICS_FILE = SCRIPT_DIR / "metrics.json"

class DDNSUpdater:
    def __init__(self):
        self.config = None
        self.logger = None
        self.metrics = {}
        self.load_configuration()
        self.setup_logging()
        self.load_metrics()

    def load_configuration(self):
        """Load configuration from config.json and .env files"""
        try:
            # Load environment variables
            if ENV_FILE.exists():
                load_dotenv(ENV_FILE)
            
            # Load main configuration
            if not CONFIG_FILE.exists():
                raise FileNotFoundError(f"Configuration file not found: {CONFIG_FILE}")
            
            with open(CONFIG_FILE, 'r') as f:
                self.config = json.load(f)
            
            # Validate required configuration
            required_fields = ['domain', 'cloudflare', 'ip_services']
            for field in required_fields:
                if field not in self.config:
                    raise ValueError(f"Missing required configuration field: {field}")
            
            # Get API token from environment
            self.api_token = os.getenv('CLOUDFLARE_API_TOKEN')
            if not self.api_token:
                raise ValueError("CLOUDFLARE_API_TOKEN not found in environment variables")
            
            # Get Telegram webhook URL if enabled
            self.telegram_webhook = None
            if self.config.get('telegram', {}).get('enabled', False):
                self.telegram_webhook = os.getenv('TELEGRAM_WEBHOOK_URL')
                
        except Exception as e:
            print(f"Configuration error: {e}")
            sys.exit(1)

    def setup_logging(self):
        """Configure rotating log system"""
        try:
            # Create logs directory if it doesn't exist
            LOGS_DIR.mkdir(exist_ok=True)
            
            # Configure logging
            log_level = getattr(logging, self.config.get('logging', {}).get('level', 'INFO'))
            log_filename = LOGS_DIR / f"ddns_{datetime.now().strftime('%Y-%m-%d')}.log"
            
            logging.basicConfig(
                level=log_level,
                format='%(asctime)s [%(levelname)s] %(message)s',
                handlers=[
                    logging.FileHandler(log_filename),
                    logging.StreamHandler(sys.stdout)
                ]
            )
            
            self.logger = logging.getLogger(__name__)
            
            # Clean up old log files
            self.cleanup_old_logs()
            
        except Exception as e:
            print(f"Logging setup error: {e}")
            sys.exit(1)

    def cleanup_old_logs(self):
        """Remove log files older than retention period"""
        try:
            retention_days = self.config.get('logging', {}).get('max_files', 90)
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            
            for log_file in LOGS_DIR.glob("ddns_*.log"):
                try:
                    file_date = datetime.fromtimestamp(log_file.stat().st_mtime)
                    if file_date < cutoff_date:
                        log_file.unlink()
                        self.logger.info(f"Removed old log file: {log_file.name}")
                except Exception as e:
                    self.logger.warning(f"Failed to remove old log file {log_file}: {e}")
                    
        except Exception as e:
            self.logger.warning(f"Log cleanup error: {e}")

    def load_metrics(self):
        """Load metrics from file or initialize new metrics"""
        try:
            if METRICS_FILE.exists():
                with open(METRICS_FILE, 'r') as f:
                    self.metrics = json.load(f)
            else:
                self.metrics = {
                    "total_runs": 0,
                    "successful_updates": 0,
                    "failed_attempts": 0,
                    "current_ip": None,
                    "last_ip_change": None,
                    "avg_response_time_ms": 0
                }
        except Exception as e:
            self.logger.warning(f"Failed to load metrics: {e}")
            self.metrics = {}

    def save_metrics(self):
        """Save metrics to file"""
        try:
            self.metrics["last_run"] = datetime.now().isoformat()
            with open(METRICS_FILE, 'w') as f:
                json.dump(self.metrics, f, indent=2)
        except Exception as e:
            self.logger.warning(f"Failed to save metrics: {e}")

    def validate_ip(self, ip):
        """Validate IP address format"""
        ip_pattern = re.compile(r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$')
        return bool(ip_pattern.match(ip))

    def get_current_public_ip(self):
        """
        Detects current public IP using multiple services
        Returns: IP address string or None if all services fail
        """
        ip_services = self.config.get('ip_services', [
            'https://api.ipify.org',
            'https://icanhazip.com'
        ])
        
        # Add ifconfig.io using curl command as specified in architecture
        curl_services = ['curl -4 ifconfig.io']
        
        start_time = time.time()
        
        # Try HTTP services first
        for service in ip_services:
            for attempt in range(3):
                try:
                    self.logger.debug(f"Attempting to get IP from {service} (attempt {attempt + 1})")
                    response = requests.get(service, timeout=10)
                    response.raise_for_status()
                    
                    ip = response.text.strip()
                    if self.validate_ip(ip):
                        response_time = (time.time() - start_time) * 1000
                        self.logger.info(f"Current public IP: {ip} (from {service})")
                        self.update_response_time_metric(response_time)
                        return ip
                    else:
                        self.logger.warning(f"Invalid IP format received from {service}: {ip}")
                        
                except requests.RequestException as e:
                    self.logger.warning(f"Failed to get IP from {service} (attempt {attempt + 1}): {e}")
                    if attempt < 2:  # Don't sleep on last attempt
                        time.sleep(5)
        
        # Try curl command as fallback
        for curl_cmd in curl_services:
            for attempt in range(3):
                try:
                    self.logger.debug(f"Attempting to get IP using: {curl_cmd} (attempt {attempt + 1})")
                    result = subprocess.run(curl_cmd.split(), capture_output=True, text=True, timeout=10)
                    
                    if result.returncode == 0:
                        ip = result.stdout.strip()
                        if self.validate_ip(ip):
                            response_time = (time.time() - start_time) * 1000
                            self.logger.info(f"Current public IP: {ip} (from curl ifconfig.io)")
                            self.update_response_time_metric(response_time)
                            return ip
                        else:
                            self.logger.warning(f"Invalid IP format from curl command: {ip}")
                    else:
                        self.logger.warning(f"Curl command failed: {result.stderr}")
                        
                except subprocess.TimeoutExpired:
                    self.logger.warning(f"Curl command timed out (attempt {attempt + 1})")
                except Exception as e:
                    self.logger.warning(f"Curl command error (attempt {attempt + 1}): {e}")
                    
                if attempt < 2:  # Don't sleep on last attempt
                    time.sleep(5)
        
        self.logger.error("Failed to get public IP from all services")
        return None

    def update_response_time_metric(self, response_time):
        """Update average response time metric"""
        current_avg = self.metrics.get('avg_response_time_ms', 0)
        total_runs = self.metrics.get('total_runs', 0)
        
        if total_runs == 0:
            self.metrics['avg_response_time_ms'] = response_time
        else:
            self.metrics['avg_response_time_ms'] = (current_avg * total_runs + response_time) / (total_runs + 1)

    def get_zone_id(self, domain):
        """Get Cloudflare zone ID for the domain"""
        try:
            # Extract root domain from subdomain
            domain_parts = domain.split('.')
            if len(domain_parts) >= 2:
                root_domain = '.'.join(domain_parts[-2:])
            else:
                root_domain = domain
            
            headers = {
                'Authorization': f'Bearer {self.api_token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(
                'https://api.cloudflare.com/client/v4/zones',
                headers=headers,
                params={'name': root_domain},
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            if data['success'] and data['result']:
                zone_id = data['result'][0]['id']
                self.logger.debug(f"Found zone ID for {root_domain}: {zone_id}")
                return zone_id
            else:
                self.logger.error(f"Zone not found for domain: {root_domain}")
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to get zone ID: {e}")
            return None

    def get_cloudflare_record(self):
        """
        Fetches current DNS A record from Cloudflare
        Returns: Current IP in DNS record or None if not found
        """
        try:
            domain = self.config['domain']
            zone_id = self.config['cloudflare'].get('zone_id')
            
            # Auto-detect zone ID if not provided
            if not zone_id or zone_id == "auto-detect":
                zone_id = self.get_zone_id(domain)
                if not zone_id:
                    return None
            
            headers = {
                'Authorization': f'Bearer {self.api_token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(
                f'https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records',
                headers=headers,
                params={'name': domain, 'type': 'A'},
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            if data['success'] and data['result']:
                current_ip = data['result'][0]['content']
                self.record_id = data['result'][0]['id']
                self.zone_id = zone_id
                self.logger.info(f"Cloudflare record IP: {current_ip}")
                return current_ip
            else:
                self.logger.warning(f"DNS A record not found for {domain}")
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to get Cloudflare record: {e}")
            return None

    def update_cloudflare_record(self, new_ip):
        """
        Updates Cloudflare DNS A record with new IP
        Returns: Boolean success status
        """
        try:
            domain = self.config['domain']
            
            headers = {
                'Authorization': f'Bearer {self.api_token}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'type': 'A',
                'name': domain,
                'content': new_ip,
                'ttl': 300  # 5 minutes TTL for quick updates
            }
            
            response = requests.put(
                f'https://api.cloudflare.com/client/v4/zones/{self.zone_id}/dns_records/{self.record_id}',
                headers=headers,
                json=data,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            if result['success']:
                self.logger.info(f"DNS record updated successfully: {domain} -> {new_ip}")
                self.metrics['successful_updates'] = self.metrics.get('successful_updates', 0) + 1
                
                # Track IP change
                if self.metrics.get('current_ip') != new_ip:
                    self.metrics['last_ip_change'] = datetime.now().isoformat()
                    self.metrics['current_ip'] = new_ip
                
                return True
            else:
                self.logger.error(f"Cloudflare API error: {result.get('errors', 'Unknown error')}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to update Cloudflare record: {e}")
            return False

    def send_telegram_alert(self, message):
        """
        Sends notification via Telegram webhook
        Optional feature for monitoring
        """
        if not self.telegram_webhook:
            return
        
        try:
            # Extract bot token and chat ID from webhook URL
            # Expected format: https://api.telegram.org/bot<token>/sendMessage?chat_id=<chat_id>
            if 'sendMessage' in self.telegram_webhook:
                payload = {
                    'text': f"🏠 Auto-DDNS Alert\n\n{message}",
                    'parse_mode': 'Markdown'
                }
                
                response = requests.post(self.telegram_webhook, json=payload, timeout=10)
                response.raise_for_status()
                
                self.logger.info("Telegram notification sent successfully")
            else:
                self.logger.warning("Invalid Telegram webhook URL format")
                
        except Exception as e:
            self.logger.warning(f"Failed to send Telegram notification: {e}")

    def main(self):
        """
        Main orchestration logic:
        1. Get current public IP
        2. Get current DNS record IP
        3. Compare and update if different
        4. Log results and send notifications
        """
        self.logger.info("Starting DDNS update check")
        self.metrics['total_runs'] = self.metrics.get('total_runs', 0) + 1
        
        try:
            # Get current public IP
            current_ip = self.get_current_public_ip()
            if not current_ip:
                self.logger.error("Failed to obtain public IP address")
                self.metrics['failed_attempts'] = self.metrics.get('failed_attempts', 0) + 1
                self.send_telegram_alert("❌ Failed to obtain public IP address")
                return False
            
            # Get current DNS record
            dns_ip = self.get_cloudflare_record()
            if dns_ip is None:
                self.logger.error("Failed to get current DNS record")
                self.metrics['failed_attempts'] = self.metrics.get('failed_attempts', 0) + 1
                self.send_telegram_alert("❌ Failed to get current DNS record from Cloudflare")
                return False
            
            # Compare IPs and update if different
            if current_ip != dns_ip:
                self.logger.info(f"IP changed from {dns_ip} to {current_ip}, updating DNS record")
                
                if self.update_cloudflare_record(current_ip):
                    success_msg = f"✅ DNS record updated successfully\n🌐 New IP: `{current_ip}`\n📍 Domain: `{self.config['domain']}`"
                    self.send_telegram_alert(success_msg)
                    self.logger.info("DDNS update completed successfully")
                    return True
                else:
                    self.metrics['failed_attempts'] = self.metrics.get('failed_attempts', 0) + 1
                    self.send_telegram_alert(f"❌ Failed to update DNS record\n🌐 Current IP: `{current_ip}`")
                    return False
            else:
                self.logger.info("IP address unchanged, no update needed")
                return True
                
        except Exception as e:
            self.logger.error(f"Unexpected error in main execution: {e}")
            self.metrics['failed_attempts'] = self.metrics.get('failed_attempts', 0) + 1
            self.send_telegram_alert(f"❌ Unexpected error: {str(e)}")
            return False
        
        finally:
            self.save_metrics()


def main():
    """Entry point for the script"""
    try:
        updater = DDNSUpdater()
        success = updater.main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nScript interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
