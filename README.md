# Auto-DDNS for Home Laboratories

🏠 **Automatic Dynamic DNS updater for home laboratories using Cloudflare**

A robust, lightweight Python script that automatically updates Cloudflare DNS A records with your current public IP address. Perfect for maintaining stable remote access to home labs (like Proxmox) despite dynamic IP changes from ISPs.

## 🎯 Features

- **Automatic IP Detection**: Multiple fallback services ensure reliable IP detection
- **Cloudflare Integration**: Seamless DNS record updates via Cloudflare API
- **Telegram Notifications**: Optional alerts for IP changes and system status
- **Robust Error Handling**: Network resilience with retry mechanisms
- **Comprehensive Logging**: Detailed logs with automatic rotation and cleanup
- **Easy Setup**: Interactive configuration script for quick deployment
- **Cron Integration**: Automatic hourly execution via cron jobs
- **Metrics Tracking**: Monitor success rates and system performance

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Cloudflare account with a domain
- Internet connectivity
- Linux system with cron support

### One-Click Installation

```bash
# Clone the repository
git clone <repository-url>
cd cloudflare-dns-local-ip

# Run the installation script
./install.sh
```

The installation script will:
1. Check system requirements
2. Install Python dependencies
3. Run interactive configuration
4. Set up cron job for automatic execution
5. Test the configuration

### Manual Installation

If you prefer manual setup:

```bash
# Install dependencies
pip3 install -r requirements.txt

# Run interactive setup
python3 setup.py

# Test the configuration
python3 auto_ddns.py
```

## ⚙️ Configuration

### Cloudflare API Token

1. Go to [Cloudflare API Tokens](https://dash.cloudflare.com/profile/api-tokens)
2. Create a new token with these permissions:
   - **Zone:Read** - for all zones
   - **DNS:Edit** - for the specific zone
3. Copy the token for use during setup

**Having token issues?** Check the detailed [Cloudflare Token Guide](docs/cloudflare-token-guide.md) for step-by-step instructions and troubleshooting.

### Domain Setup

Ensure your domain is managed by Cloudflare and has an A record that you want to update automatically.

### Telegram Notifications (Optional)

1. Create a bot with [@BotFather](https://t.me/BotFather) on Telegram
2. Get your chat ID from [@userinfobot](https://t.me/userinfobot)
3. Format the webhook URL: `https://api.telegram.org/bot<BOT_TOKEN>/sendMessage?chat_id=<CHAT_ID>`

## 📁 Project Structure

```
cloudflare-dns-local-ip/
├── auto_ddns.py              # Main script
├── setup.py                  # Interactive setup script
├── install.sh               # One-click installation
├── requirements.txt          # Python dependencies
├── config/
│   ├── config.json          # Main configuration (created during setup)
│   ├── .env                 # Environment variables (created during setup)
│   ├── config.json.example  # Configuration template
│   └── .env.example         # Environment template
├── logs/                    # Log files (auto-created)
├── docs/
│   └── system-architecture.md # Technical documentation
└── README.md               # This file
```

## 🔧 Usage

### Automatic Execution

Once configured, the system runs automatically every hour via cron. No manual intervention required.

### Manual Execution

```bash
# Run once
python3 auto_ddns.py

# Reconfigure the system
python3 setup.py

# View logs
tail -f logs/ddns_$(date +%Y-%m-%d).log
```

### Monitoring

- **Logs**: Check `logs/` directory for detailed execution logs
- **Metrics**: View `metrics.json` for performance statistics
- **Telegram**: Receive real-time notifications (if configured)

## 📊 Configuration Options

### Main Configuration (`config/config.json`)

```json
{
  "domain": "lab.yourdomain.com",
  "cloudflare": {
    "zone_id": "auto-detect",
    "record_name": "lab"
  },
  "ip_services": [
    "https://api.ipify.org",
    "https://icanhazip.com"
  ],
  "logging": {
    "level": "INFO",
    "max_files": 90,
    "max_size_mb": 10
  },
  "telegram": {
    "enabled": true,
    "webhook_url": "from_env"
  }
}
```

### Environment Variables (`config/.env`)

```bash
CLOUDFLARE_API_TOKEN=your_api_token_here
TELEGRAM_WEBHOOK_URL=https://api.telegram.org/bot<token>/sendMessage?chat_id=<chat_id>
```

## 🔍 Troubleshooting

### Common Issues

1. **"Configuration file not found"**
   - Run `python3 setup.py` to create configuration

2. **"Failed to get public IP"**
   - Check internet connectivity
   - Verify firewall settings

3. **"Cloudflare API error"**
   - Verify API token permissions
   - Check domain configuration in Cloudflare

4. **"DNS record not found"**
   - Ensure A record exists in Cloudflare
   - Verify domain name in configuration

### Log Analysis

```bash
# View today's logs
cat logs/ddns_$(date +%Y-%m-%d).log

# Monitor real-time
tail -f logs/ddns_$(date +%Y-%m-%d).log

# Search for errors
grep ERROR logs/ddns_*.log
```

### Testing Configuration

```bash
# Test IP detection
python3 -c "from auto_ddns import DDNSUpdater; print(DDNSUpdater().get_current_public_ip())"

# Test Cloudflare connection
python3 -c "from auto_ddns import DDNSUpdater; u=DDNSUpdater(); print(u.get_cloudflare_record())"
```

## 📈 Monitoring & Metrics

The system tracks various metrics in `metrics.json`:

- **Total runs**: Number of script executions
- **Successful updates**: DNS updates completed successfully
- **Failed attempts**: Number of failures
- **Current IP**: Last detected public IP
- **Last IP change**: Timestamp of most recent IP change
- **Average response time**: Performance metrics

## 🔒 Security

- **API tokens** stored in environment variables
- **Configuration files** have restricted permissions (600)
- **No hardcoded credentials** in source code
- **HTTPS-only** communication with external services
- **Error sanitization** prevents credential exposure in logs

## 🛠️ Advanced Configuration

### Custom IP Services

Add custom IP detection services in `config.json`:

```json
{
  "ip_services": [
    "https://api.ipify.org",
    "https://icanhazip.com",
    "https://ipecho.net/plain",
    "https://myexternalip.com/raw"
  ]
}
```

### Multiple Domains

Currently supports one domain per instance. For multiple domains, run separate instances with different configurations.

### Custom Cron Schedule

Modify the cron job for different execution intervals:

```bash
# Edit crontab
crontab -e

# Examples:
# Every 30 minutes: */30 * * * * /usr/bin/python3 /path/to/auto_ddns.py
# Every 6 hours: 0 */6 * * * /usr/bin/python3 /path/to/auto_ddns.py
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- [Cloudflare](https://cloudflare.com) for their excellent DNS API
- [ipify.org](https://ipify.org) for reliable IP detection service
- The open-source community for inspiration and tools

## 📞 Support

- **Documentation**: Check `docs/system-architecture.md` for technical details
- **Issues**: Report bugs and feature requests via GitHub issues
- **Logs**: Always check log files for detailed error information

---

**Made with ❤️ for home lab enthusiasts**
