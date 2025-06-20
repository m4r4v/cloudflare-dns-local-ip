#!/usr/bin/env python3
"""
Interactive setup script for Auto-DDNS
Guides users through configuration and installation
"""

import os
import sys
import json
import subprocess
from pathlib import Path
import requests
import getpass

class DDNSSetup:
    def __init__(self):
        self.script_dir = Path(__file__).parent
        self.config_dir = self.script_dir / "config"
        self.config_file = self.config_dir / "config.json"
        self.env_file = self.config_dir / ".env"
        self.logs_dir = self.script_dir / "logs"
        
    def print_header(self):
        """Print setup header"""
        print("=" * 60)
        print("🏠 Auto-DDNS for Home Laboratories - Setup")
        print("=" * 60)
        print("This setup will guide you through configuring your Auto-DDNS system.")
        print()

    def create_directories(self):
        """Create necessary directories"""
        print("📁 Creating directories...")
        self.config_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)
        print("✅ Directories created successfully")
        print()

    def get_domain_info(self):
        """Get domain information from user"""
        print("🌐 Domain Configuration")
        print("-" * 30)
        
        while True:
            domain = input("Enter your domain name (e.g., lab.yourdomain.com): ").strip()
            if domain and '.' in domain:
                break
            print("❌ Please enter a valid domain name")
        
        # Extract record name from domain
        domain_parts = domain.split('.')
        if len(domain_parts) > 2:
            record_name = domain_parts[0]
        else:
            record_name = "@"  # Root domain
        
        print(f"📝 Domain: {domain}")
        print(f"📝 Record name: {record_name}")
        print()
        
        return domain, record_name

    def get_cloudflare_token(self):
        """Get and validate Cloudflare API token"""
        print("☁️  Cloudflare Configuration")
        print("-" * 30)
        print("You need a Cloudflare API token with Zone:Read and DNS:Edit permissions.")
        print("Create one at: https://dash.cloudflare.com/profile/api-tokens")
        print()
        
        while True:
            token = getpass.getpass("Enter your Cloudflare API token: ").strip()
            if not token:
                print("❌ Token cannot be empty")
                continue
            
            # Validate token
            print("🔍 Validating API token...")
            if self.validate_cloudflare_token(token):
                print("✅ API token validated successfully")
                print()
                return token
            else:
                print("❌ Invalid API token or insufficient permissions")
                retry = input("Try again? (y/n): ").lower()
                if retry != 'y':
                    sys.exit(1)

    def validate_cloudflare_token(self, token):
        """Validate Cloudflare API token"""
        try:
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            # First try to verify the token
            print("  🔍 Checking token validity...")
            response = requests.get(
                'https://api.cloudflare.com/client/v4/user/tokens/verify',
                headers=headers,
                timeout=15
            )
            
            print(f"  📡 Response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"  📄 Response data: {data}")
                
                if data.get('success', False):
                    print("  ✅ Token verification successful")
                    
                    # Additional test: try to list zones to verify permissions
                    print("  🔍 Testing zone access permissions...")
                    zones_response = requests.get(
                        'https://api.cloudflare.com/client/v4/zones',
                        headers=headers,
                        timeout=15
                    )
                    
                    if zones_response.status_code == 200:
                        zones_data = zones_response.json()
                        if zones_data.get('success', False):
                            zone_count = len(zones_data.get('result', []))
                            print(f"  ✅ Zone access successful - Found {zone_count} zones")
                            return True
                        else:
                            print(f"  ❌ Zone access failed: {zones_data.get('errors', 'Unknown error')}")
                            print("  💡 Make sure your token has 'Zone:Read' permission")
                            return False
                    else:
                        print(f"  ❌ Zone access failed with status {zones_response.status_code}")
                        print("  💡 Make sure your token has 'Zone:Read' permission")
                        return False
                else:
                    errors = data.get('errors', [])
                    print(f"  ❌ Token verification failed: {errors}")
                    if errors:
                        for error in errors:
                            print(f"      Error {error.get('code', 'N/A')}: {error.get('message', 'Unknown error')}")
                    return False
            elif response.status_code == 401:
                print("  ❌ Unauthorized - Invalid token")
                print("  💡 Please check that your token is correct")
                return False
            elif response.status_code == 403:
                print("  ❌ Forbidden - Insufficient permissions")
                print("  💡 Make sure your token has the required permissions:")
                print("      - Zone:Read (for all zones)")
                print("      - DNS:Edit (for the specific zone)")
                return False
            else:
                print(f"  ❌ Unexpected response status: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"  📄 Error details: {error_data}")
                except:
                    print(f"  📄 Response text: {response.text}")
                return False
            
        except requests.exceptions.Timeout:
            print("  ❌ Request timed out - Check your internet connection")
            return False
        except requests.exceptions.ConnectionError:
            print("  ❌ Connection error - Check your internet connection")
            return False
        except Exception as e:
            print(f"  ❌ Error validating token: {e}")
            return False

    def get_telegram_config(self):
        """Get Telegram configuration (optional)"""
        print("📱 Telegram Notifications (Optional)")
        print("-" * 30)
        print("You can receive notifications via Telegram when IP changes occur.")
        
        enable_telegram = input("Enable Telegram notifications? (y/n): ").lower() == 'y'
        
        webhook_url = None
        if enable_telegram:
            print()
            print("To set up Telegram notifications:")
            print("1. Create a bot with @BotFather on Telegram")
            print("2. Get your chat ID by messaging @userinfobot")
            print("3. Format: https://api.telegram.org/bot<BOT_TOKEN>/sendMessage?chat_id=<CHAT_ID>")
            print()
            
            webhook_url = input("Enter Telegram webhook URL (or press Enter to skip): ").strip()
            if not webhook_url:
                enable_telegram = False
                print("📱 Telegram notifications disabled")
        
        print()
        return enable_telegram, webhook_url

    def get_ip_services(self):
        """Configure IP detection services"""
        print("🌍 IP Detection Services")
        print("-" * 30)
        
        default_services = [
            "https://api.ipify.org",
            "https://icanhazip.com"
        ]
        
        print("Default IP detection services:")
        for i, service in enumerate(default_services, 1):
            print(f"  {i}. {service}")
        
        use_default = input("\nUse default services? (y/n): ").lower() == 'y'
        
        if use_default:
            return default_services
        else:
            services = []
            print("\nEnter custom IP services (press Enter when done):")
            while True:
                service = input(f"Service {len(services) + 1}: ").strip()
                if not service:
                    break
                if service.startswith('http'):
                    services.append(service)
                else:
                    print("❌ Please enter a valid HTTP/HTTPS URL")
            
            return services if services else default_services

    def get_logging_config(self):
        """Configure logging settings"""
        print("📝 Logging Configuration")
        print("-" * 30)
        
        log_levels = ["DEBUG", "INFO", "WARNING", "ERROR"]
        print("Available log levels:")
        for i, level in enumerate(log_levels, 1):
            print(f"  {i}. {level}")
        
        while True:
            try:
                choice = input("\nSelect log level (1-4, default: 2 for INFO): ").strip()
                if not choice:
                    choice = "2"
                
                level_index = int(choice) - 1
                if 0 <= level_index < len(log_levels):
                    log_level = log_levels[level_index]
                    break
                else:
                    print("❌ Please enter a number between 1 and 4")
            except ValueError:
                print("❌ Please enter a valid number")
        
        # Log retention
        while True:
            try:
                retention = input("Log retention days (default: 90): ").strip()
                if not retention:
                    retention = 90
                else:
                    retention = int(retention)
                
                if retention > 0:
                    break
                else:
                    print("❌ Retention days must be positive")
            except ValueError:
                print("❌ Please enter a valid number")
        
        print(f"📝 Log level: {log_level}")
        print(f"📝 Retention: {retention} days")
        print()
        
        return log_level, retention

    def create_config_files(self, domain, record_name, token, telegram_enabled, 
                          webhook_url, ip_services, log_level, log_retention):
        """Create configuration files"""
        print("📄 Creating configuration files...")
        
        # Create main config
        config = {
            "domain": domain,
            "cloudflare": {
                "zone_id": "auto-detect",
                "record_name": record_name
            },
            "ip_services": ip_services,
            "logging": {
                "level": log_level,
                "max_files": log_retention,
                "max_size_mb": 10
            },
            "telegram": {
                "enabled": telegram_enabled,
                "webhook_url": "from_env" if telegram_enabled else None
            }
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        # Create .env file
        env_content = f"CLOUDFLARE_API_TOKEN={token}\n"
        if telegram_enabled and webhook_url:
            env_content += f"TELEGRAM_WEBHOOK_URL={webhook_url}\n"
        
        with open(self.env_file, 'w') as f:
            f.write(env_content)
        
        # Set secure permissions
        os.chmod(self.env_file, 0o600)
        
        print("✅ Configuration files created successfully")
        print()

    def test_configuration(self):
        """Test the configuration"""
        print("🧪 Testing configuration...")
        
        try:
            # Import and test the main script
            sys.path.insert(0, str(self.script_dir))
            from auto_ddns import DDNSUpdater
            
            updater = DDNSUpdater()
            
            # Test IP detection
            print("  🌐 Testing IP detection...")
            current_ip = updater.get_current_public_ip()
            if current_ip:
                print(f"  ✅ Current IP detected: {current_ip}")
            else:
                print("  ❌ Failed to detect IP")
                return False
            
            # Test Cloudflare connection
            print("  ☁️  Testing Cloudflare connection...")
            dns_ip = updater.get_cloudflare_record()
            if dns_ip is not None:
                print(f"  ✅ DNS record found: {dns_ip}")
            else:
                print("  ❌ Failed to get DNS record")
                return False
            
            print("✅ Configuration test completed successfully")
            print()
            return True
            
        except Exception as e:
            print(f"  ❌ Configuration test failed: {e}")
            return False

    def setup_cron_job(self):
        """Setup cron job for automatic execution"""
        print("⏰ Setting up cron job...")
        
        script_path = self.script_dir / "auto_ddns.py"
        python_path = sys.executable
        
        # Create cron entry
        cron_command = f"0 * * * * {python_path} {script_path} >> {self.logs_dir}/cron.log 2>&1"
        
        print(f"Cron command: {cron_command}")
        
        install_cron = input("Install cron job to run hourly? (y/n): ").lower() == 'y'
        
        if install_cron:
            try:
                # Get current crontab
                result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
                current_crontab = result.stdout if result.returncode == 0 else ""
                
                # Check if entry already exists
                if script_path.name in current_crontab:
                    print("⚠️  Cron job already exists, skipping...")
                else:
                    # Add new entry
                    new_crontab = current_crontab + f"\n{cron_command}\n"
                    
                    # Install new crontab
                    process = subprocess.Popen(['crontab', '-'], stdin=subprocess.PIPE, text=True)
                    process.communicate(input=new_crontab)
                    
                    if process.returncode == 0:
                        print("✅ Cron job installed successfully")
                    else:
                        print("❌ Failed to install cron job")
                        return False
                
            except Exception as e:
                print(f"❌ Error setting up cron job: {e}")
                print("You can manually add this cron entry:")
                print(f"  {cron_command}")
                return False
        else:
            print("⏭️  Skipping cron job installation")
            print("To run manually, use:")
            print(f"  {python_path} {script_path}")
        
        print()
        return True

    def print_summary(self):
        """Print setup summary"""
        print("🎉 Setup Complete!")
        print("=" * 60)
        print("Your Auto-DDNS system has been configured successfully.")
        print()
        print("📁 Files created:")
        print(f"  • {self.config_file}")
        print(f"  • {self.env_file}")
        print()
        print("🔧 Next steps:")
        print("  1. The system will run automatically via cron (if installed)")
        print("  2. Check logs in the 'logs' directory")
        print("  3. Monitor Telegram notifications (if enabled)")
        print()
        print("🚀 To run manually:")
        print(f"  python3 {self.script_dir / 'auto_ddns.py'}")
        print()
        print("📖 For troubleshooting, check the logs and documentation.")
        print("=" * 60)

    def run_setup(self):
        """Run the complete setup process"""
        try:
            self.print_header()
            
            # Create directories
            self.create_directories()
            
            # Get configuration
            domain, record_name = self.get_domain_info()
            token = self.get_cloudflare_token()
            telegram_enabled, webhook_url = self.get_telegram_config()
            ip_services = self.get_ip_services()
            log_level, log_retention = self.get_logging_config()
            
            # Create config files
            self.create_config_files(
                domain, record_name, token, telegram_enabled,
                webhook_url, ip_services, log_level, log_retention
            )
            
            # Test configuration
            if not self.test_configuration():
                print("❌ Setup failed during testing. Please check your configuration.")
                sys.exit(1)
            
            # Setup cron job
            self.setup_cron_job()
            
            # Print summary
            self.print_summary()
            
        except KeyboardInterrupt:
            print("\n❌ Setup interrupted by user")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Setup failed: {e}")
            sys.exit(1)


def main():
    """Main entry point"""
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help']:
        print("Auto-DDNS Setup Script")
        print("Usage: python3 setup.py")
        print("This script will guide you through the interactive setup process.")
        sys.exit(0)
    
    setup = DDNSSetup()
    setup.run_setup()


if __name__ == "__main__":
    main()
