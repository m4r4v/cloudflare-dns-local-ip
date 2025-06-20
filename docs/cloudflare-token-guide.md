# Cloudflare API Token Configuration Guide

## 🔑 Creating the Correct API Token

### Step 1: Access Cloudflare API Tokens
1. Go to [Cloudflare Dashboard](https://dash.cloudflare.com)
2. Click on your profile icon (top right)
3. Select "My Profile"
4. Go to the "API Tokens" tab
5. Click "Create Token"

### Step 2: Configure Token Permissions
Select "Custom token" and configure:

**Token name:** `Auto-DDNS Home Lab`

**Permissions:**
- `Zone:Read` - Include: All zones
- `DNS:Edit` - Include: Specific zone (select your domain)

**Zone Resources:**
- Include: Specific zone → Select your domain (e.g., `yourdomain.com`)

**IP Address Filtering:** (Optional)
- Leave empty for no restrictions, or add your home IP range

**TTL:** (Optional)
- Leave empty for no expiration, or set a reasonable time

### Step 3: Generate and Copy Token
1. Click "Continue to summary"
2. Review the permissions
3. Click "Create Token"
4. **IMPORTANT:** Copy the token immediately - you won't see it again!

## 🔍 Common Token Issues and Solutions

### Issue 1: "Invalid API token or insufficient permissions"

**Possible causes:**
- Token was copied incorrectly
- Token has expired
- Insufficient permissions

**Solutions:**
1. **Verify token format:** Should start with a long string of characters
2. **Check permissions:** Ensure you have both `Zone:Read` and `DNS:Edit`
3. **Verify zone access:** Make sure the token can access your specific domain

### Issue 2: "Zone access failed"

**Possible causes:**
- Token doesn't have `Zone:Read` permission
- Token is restricted to wrong zone
- Domain not managed by Cloudflare

**Solutions:**
1. **Check Zone:Read permission:** Must be set to "All zones" or include your specific zone
2. **Verify domain:** Ensure your domain is actually managed by Cloudflare
3. **Check zone status:** Domain must be active in Cloudflare

### Issue 3: "DNS record not found"

**Possible causes:**
- A record doesn't exist for the domain
- Token doesn't have `DNS:Edit` permission for the zone
- Wrong domain name in configuration

**Solutions:**
1. **Create A record:** Go to Cloudflare DNS tab and create an A record for your subdomain
2. **Check DNS:Edit permission:** Must be set for the specific zone
3. **Verify domain name:** Ensure the domain in config matches exactly

## 🛠️ Manual Token Testing

You can test your token manually using curl:

### Test 1: Verify Token
```bash
curl -X GET "https://api.cloudflare.com/client/v4/user/tokens/verify" \
     -H "Authorization: Bearer YOUR_TOKEN_HERE" \
     -H "Content-Type: application/json"
```

**Expected response:**
```json
{
  "success": true,
  "errors": [],
  "messages": [],
  "result": {
    "id": "token_id",
    "status": "active"
  }
}
```

### Test 2: List Zones
```bash
curl -X GET "https://api.cloudflare.com/client/v4/zones" \
     -H "Authorization: Bearer YOUR_TOKEN_HERE" \
     -H "Content-Type: application/json"
```

**Expected response:**
```json
{
  "success": true,
  "errors": [],
  "messages": [],
  "result": [
    {
      "id": "zone_id",
      "name": "yourdomain.com",
      "status": "active"
    }
  ]
}
```

### Test 3: List DNS Records
```bash
curl -X GET "https://api.cloudflare.com/client/v4/zones/ZONE_ID/dns_records?type=A&name=lab.yourdomain.com" \
     -H "Authorization: Bearer YOUR_TOKEN_HERE" \
     -H "Content-Type: application/json"
```

## 📋 Token Permissions Checklist

Before using your token, verify:

- [ ] Token has `Zone:Read` permission for all zones OR your specific zone
- [ ] Token has `DNS:Edit` permission for your specific zone
- [ ] Your domain is active in Cloudflare
- [ ] An A record exists for your subdomain (create one if needed)
- [ ] Token hasn't expired
- [ ] Token was copied correctly (no extra spaces or characters)

## 🔧 Creating DNS A Record

If you don't have an A record yet:

1. Go to Cloudflare Dashboard
2. Select your domain
3. Go to "DNS" tab
4. Click "Add record"
5. Select "A" type
6. Name: `lab` (or your subdomain)
7. IPv4 address: Your current public IP (you can get it from https://api.ipify.org)
8. TTL: Auto or 300 seconds
9. Click "Save"

## 🚨 Security Best Practices

1. **Minimal Permissions:** Only grant the permissions you need
2. **Zone Restrictions:** Limit token to specific zones, not all zones
3. **IP Restrictions:** Consider restricting to your home IP range
4. **Token Rotation:** Regularly rotate your tokens
5. **Secure Storage:** Never commit tokens to version control

## 🆘 Still Having Issues?

If you're still experiencing problems:

1. **Check Cloudflare Status:** Visit [Cloudflare Status](https://www.cloudflarestatus.com/)
2. **Verify Domain:** Ensure your domain nameservers point to Cloudflare
3. **Test with Browser:** Log into Cloudflare dashboard to verify access
4. **Create New Token:** Sometimes starting fresh helps
5. **Check Logs:** Run the setup with detailed logging to see exact error messages

## 📞 Getting Help

If you need additional help:

1. Check the main troubleshooting section in README.md
2. Review the system logs in the `logs/` directory
3. Test your token manually using the curl commands above
4. Verify your domain configuration in Cloudflare dashboard

Remember: The most common issue is insufficient permissions. Make sure your token has both `Zone:Read` and `DNS:Edit` permissions for your domain.
