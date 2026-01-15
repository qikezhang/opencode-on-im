# Proxy Best Practices

Guide for using residential proxies with OpenCode Cloudify on cloud servers.

## Why You Need a Proxy

When running OpenCode with ChatGPT Plus on cloud servers:

1. **OpenAI blocks datacenter IPs** - Cloud server IPs are often flagged
2. **Rate limiting** - Datacenter IPs face stricter limits
3. **Account security** - Unusual login locations may trigger security checks

A **residential proxy** makes your cloud server appear as a home internet connection.

## Proxy Types

| Type | Best For | Cost |
|------|----------|------|
| **Static Residential** | ChatGPT Plus, long sessions | $$$ |
| **Rotating Residential** | Web scraping, API calls | $$ |
| **Datacenter** | Non-OpenAI APIs | $ |
| **Mobile** | Highest trust level | $$$$ |

**Recommendation**: Static residential proxy for ChatGPT Plus usage.

## Recommended Providers

### Premium Providers

1. **Bright Data** (formerly Luminati)
   - Largest network
   - Static residential IPs
   - [brightdata.com](https://brightdata.com)

2. **Smartproxy**
   - Good for US/EU locations
   - Competitive pricing
   - [smartproxy.com](https://smartproxy.com)

3. **IPRoyal**
   - Budget-friendly residential
   - Static IP options
   - [iproyal.com](https://iproyal.com)

### Budget Options

1. **Webshare**
   - Datacenter proxies (may not work for ChatGPT)
   - Very affordable

2. **ProxyScrape**
   - Free rotating proxies
   - Unreliable for production

## Configuration

### SOCKS5 Proxy (Recommended)

```yaml
proxy:
  enabled: true
  url: "socks5://username:password@proxy.example.com:1080"
```

### HTTP/HTTPS Proxy

```yaml
proxy:
  enabled: true
  url: "http://username:password@proxy.example.com:8080"
```

### Docker

```bash
docker run -d \
  -e PROXY_ENABLED=true \
  -e PROXY_URL="socks5://user:pass@proxy:1080" \
  opencodecloudify/cloudify:latest
```

## Choosing a Location

Match the proxy location to your ChatGPT Plus account's typical location:

| Account Region | Recommended Proxy Location |
|----------------|---------------------------|
| US account | US residential (California, Texas, New York) |
| EU account | UK, Germany, Netherlands |
| Asia account | Japan, Singapore, Hong Kong |

## Testing Your Proxy

Before deploying, test your proxy:

```bash
# Test with curl
curl -x socks5://user:pass@proxy:1080 https://api.ipify.org

# Test OpenAI access
curl -x socks5://user:pass@proxy:1080 https://chat.openai.com
```

## Troubleshooting

### Connection refused

1. Verify proxy credentials
2. Check firewall allows outbound connections
3. Try a different port (1080, 8080, 3128)

### Slow performance

1. Choose a proxy closer to your server
2. Use SOCKS5 instead of HTTP
3. Try a different provider

### Still getting blocked

1. Ensure you're using **residential** (not datacenter) IPs
2. Try a **static** residential IP
3. Use a **mobile** proxy as last resort

## Cost Optimization

1. **Static IP**: Pay monthly for consistent access (~$3-10/IP/month)
2. **Bandwidth**: Choose plans with sufficient GB for your usage
3. **Location**: Some regions are cheaper than others

## Security Notes

1. **Secure credentials**: Use environment variables, not config files
2. **Rotate regularly**: Change proxy credentials periodically
3. **Monitor usage**: Check for unauthorized access
4. **Terms of service**: Ensure proxy usage complies with OpenAI ToS
