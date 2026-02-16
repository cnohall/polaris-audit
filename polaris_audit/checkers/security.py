import ssl
import socket
import logging
from urllib.parse import urlparse
from datetime import datetime
from typing import Dict, Any, Optional, List
from bs4 import BeautifulSoup
from requests import Response
from .base import BaseChecker
from .security_headers import SecurityHeadersService

logger = logging.getLogger(__name__)


class SecurityChecker(BaseChecker):
    """Enhanced security checker with comprehensive coverage and practical business focus."""

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.headers_service = SecurityHeadersService()

    @property
    def name(self) -> str:
        return "security"

    def check(self, response: Response, soup: Optional[BeautifulSoup], result: dict) -> None:
        """Perform comprehensive security checks."""
        self._check_https(response, result)
        self._check_ssl_certificate(result)
        self._check_security_headers(response, result)
        self._check_mixed_content(soup, result)
        self._check_form_security(soup, result)
        self._check_cookie_security(response, result)
        # Score calculation is now handled by UnifiedScoringService
        # self._calculate_security_score(result)
        
        logger.info(f"Security checker completed: {len(result.get('business_issues', []))} issues found")

    def _check_https(self, response: Response, result: dict) -> None:
        """Check HTTPS usage and redirect behavior."""
        try:
            final_url = response.url
            uses_https = urlparse(final_url).scheme == "https"
            
            # Check if original request was HTTP but redirected to HTTPS
            initial_url = result.get("url", "")
            http_redirects_to_https = (
                urlparse(initial_url).scheme == "http" and 
                uses_https and 
                initial_url != final_url
            )
            
            self.set_check_result(result, "uses_https", uses_https)
            self.set_check_result(result, "http_redirects_to_https", http_redirects_to_https)

            if not uses_https:
                self.add_business_issue(
                    result,
                    title="Switch to secure HTTPS",
                    impact="Customer data is not encrypted and your site shows 'Not Secure' warnings",
                    priority="must_fix",
                    fix_time=30,
                    difficulty="easy",
                    category="security",
                    technical_details="Website not served over HTTPS protocol",
                    fix_instructions="""HOW TO ENABLE HTTPS (STEP-BY-STEP):

🔒 **OPTION 1: POPULAR HOSTING PROVIDERS (5-10 MINUTES)**

**Cloudflare Users:**
1. Log into your Cloudflare dashboard
2. Go to SSL/TLS → Overview
3. Set SSL/TLS encryption mode to "Full (strict)"
4. Go to SSL/TLS → Edge Certificates
5. Enable "Always Use HTTPS"
6. Wait 5 minutes for changes to propagate

**cPanel Hosting (Shared Hosting):**
1. Log into your cPanel
2. Find "SSL/TLS" in the Security section
3. Click "Let's Encrypt SSL" or "SSL Certificates"
4. Select your domain and click "Install"
5. In File Manager, edit .htaccess file and add:
   ```
   RewriteEngine On
   RewriteCond %{HTTPS} off
   RewriteRule ^(.*)$ https://%{HTTP_HOST}%{REQUEST_URI} [L,R=301]
   ```

**WordPress Users:**
1. Install "SSL Insecure Content Fixer" plugin
2. Go to Settings → SSL Insecure Content Fixer
3. Enable "Force SSL" and "Fix mixed content"
4. Update WordPress URLs in Settings → General to use https://

🔒 **OPTION 2: MANUAL SERVER CONFIGURATION**

**Apache (.htaccess):**
```apache
RewriteEngine On
RewriteCond %{HTTPS} off
RewriteRule ^(.*)$ https://%{HTTP_HOST}%{REQUEST_URI} [L,R=301]
```

**Nginx:**
```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}
```

**Django (settings.py):**
```python
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
```

🔒 **OPTION 3: HOSTING-SPECIFIC INSTRUCTIONS**

**AWS CloudFront/Route 53:**
1. Create ACM certificate in Certificate Manager
2. Add certificate to CloudFront distribution
3. Set "Viewer Protocol Policy" to "Redirect HTTP to HTTPS"

**Netlify:**
1. Go to Site Settings → Domain management
2. Click "Force HTTPS" toggle (automatic with custom domains)

**Vercel:**
1. HTTPS is automatically enabled for all deployments
2. Check "Security" tab in dashboard to confirm

**DigitalOcean/VPS:**
1. Install Certbot: `sudo apt install certbot python3-certbot-apache`
2. Run: `sudo certbot --apache -d yourdomain.com`
3. Follow prompts to install certificate

🔒 **VERIFICATION STEPS:**
1. Visit http://yourdomain.com (should redirect to https://)
2. Check for green lock icon in browser address bar
3. Test at: https://www.ssllabs.com/ssltest/
4. Use curl: `curl -I http://yourdomain.com` (should show 301 redirect)

🔒 **TROUBLESHOOTING:**
- **Mixed content errors**: Update all http:// links to https://
- **Certificate not working**: Wait 24-48 hours for DNS propagation
- **Redirect loop**: Check if hosting provider already redirects HTTP
- **WordPress issues**: Update site URL in wp-config.php or database""",
                    business_value="Protects customer data, prevents browser warnings, improves SEO rankings",
                    recurring_check=True,
                    code_snippets=[
                        {
                            "title": "Force HTTPS Redirect (.htaccess)",
                            "code": "# Add to your .htaccess file\nRewriteEngine On\nRewriteCond %{HTTPS} off\nRewriteRule ^(.*)$ https://%{HTTP_HOST}%{REQUEST_URI} [L,R=301]",
                            "language": "apache"
                        },
                        {
                            "title": "WordPress HTTPS Force",
                            "code": "// Add to functions.php\nif (!is_ssl() && !is_admin()) {\n    $redirect_url = 'https://' . $_SERVER['HTTP_HOST'] . $_SERVER['REQUEST_URI'];\n    wp_redirect($redirect_url, 301);\n    exit();\n}",
                            "language": "php"
                        }
                    ],
                    testing_steps=[
                        "Visit your site with http:// to verify it redirects to https://",
                        "Check for green lock icon in browser address bar",
                        "Test on multiple browsers and devices"
                    ]
                )
            elif not http_redirects_to_https and urlparse(initial_url).scheme == "http":
                self.add_business_issue(
                    result,
                    title="Set up HTTP to HTTPS redirect",
                    impact="Visitors accessing via HTTP don't get automatically protected",
                    priority="should_fix",
                    fix_time=15,
                    difficulty="easy",
                    category="security",
                    technical_details="HTTPS available but HTTP requests not redirected",
                    fix_instructions="""HOW TO SET UP AUTOMATIC HTTP TO HTTPS REDIRECTS:

🔄 **OPTION 1: WEB SERVER CONFIGURATION**

**Apache (.htaccess file):**
1. Access your website files via FTP, cPanel File Manager, or hosting dashboard
2. Find the .htaccess file in your website's root directory (create if it doesn't exist)
3. Add these lines at the top:
```apache
RewriteEngine On
RewriteCond %{HTTPS} off
RewriteRule ^(.*)$ https://%{HTTP_HOST}%{REQUEST_URI} [L,R=301]

# Alternative if using CloudFlare:
RewriteCond %{HTTP:CF-Visitor} '"scheme":"http"'
RewriteRule ^(.*)$ https://%{HTTP_HOST}%{REQUEST_URI} [L,R=301]
```

**Nginx (server configuration):**
1. Edit your Nginx configuration file (usually in /etc/nginx/sites-available/)
2. Add this server block:
```nginx
server {
    listen 80;
    listen [::]:80;
    server_name yourdomain.com www.yourdomain.com;

    # Redirect all HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}
```
3. Reload Nginx: `sudo systemctl reload nginx`

🔄 **OPTION 2: HOSTING CONTROL PANELS**

**cPanel:**
1. Log into cPanel
2. Go to "Domains" → "Redirects"
3. Type: Permanent (301)
4. From: http://yourdomain.com
5. To: https://yourdomain.com
6. Click "Add"

**Cloudflare:**
1. Log into Cloudflare dashboard
2. Go to SSL/TLS → Edge Certificates
3. Toggle "Always Use HTTPS" to ON
4. Changes take effect in ~5 minutes

**WordPress:**
1. Install "Easy HTTPS Redirection" plugin, OR
2. Add to wp-config.php:
```php
if (!is_ssl() && $_SERVER['HTTP_X_FORWARDED_PROTO'] !== 'https') {
    $redirect_url = 'https://' . $_SERVER['HTTP_HOST'] . $_SERVER['REQUEST_URI'];
    wp_redirect($redirect_url, 301);
    exit();
}
```

🔄 **OPTION 3: FRAMEWORK-SPECIFIC**

**Django (settings.py):**
```python
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_TLS = True
```

**Node.js/Express:**
```javascript
app.use((req, res, next) => {
  if (req.header('x-forwarded-proto') !== 'https') {
    res.redirect(`https://${req.header('host')}${req.url}`);
  } else {
    next();
  }
});
```

**Laravel (.env file):**
```
FORCE_HTTPS=true
```

🔄 **VERIFICATION & TESTING:**
1. Clear browser cache
2. Visit http://yourdomain.com (should redirect to https://)
3. Check redirect status: `curl -I http://yourdomain.com`
   - Look for "HTTP/1.1 301 Moved Permanently"
   - Location header should show https:// URL
4. Test subpages: http://yourdomain.com/about
5. Use online tools:
   - https://httpstatus.io
   - https://www.redirect-checker.org

🔄 **COMMON ISSUES & FIXES:**
- **Redirect loop**: Remove duplicate redirects from hosting provider
- **Only homepage redirects**: Check .htaccess covers all paths with ^(.*)$
- **WordPress admin issues**: Add to wp-config.php: `define('FORCE_SSL_ADMIN', true);`
- **Mixed content warnings**: Use protocol-relative URLs or update all links to https://""",
                    business_value="Ensures all visitors get encrypted connection",
                    recurring_check=True
                )
                
        except Exception as e:
            self.add_issue(result, f"Error checking HTTPS: {str(e)}", "warning", "security")

    def _check_ssl_certificate(self, result: dict) -> None:
        """Check SSL certificate validity, expiry, and common issues."""
        if not result.get("checks", {}).get("security_uses_https", False):
            self.set_check_result(result, "ssl_valid", False)
            return

        try:
            final_url = result.get("final_url") or result.get("url")
            hostname = urlparse(final_url).hostname
            
            if not hostname:
                return

            # Create SSL context and connect
            context = ssl.create_default_context()
            with socket.create_connection((hostname, 443), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert()
                    cipher = ssock.cipher()

            # Check certificate expiry
            not_after = datetime.strptime(cert["notAfter"], "%b %d %H:%M:%S %Y %Z")
            days_until_expiry = (not_after - datetime.now()).days

            self.set_check_result(result, "ssl_valid", True)
            self.set_check_result(result, "ssl_days_until_expiry", days_until_expiry)
            self.set_check_result(result, "ssl_expires_soon", days_until_expiry <= 30)
            
            # Check SSL strength
            ssl_strength = "strong" if cipher and cipher[1] in ["TLSv1.2", "TLSv1.3"] else "weak"
            self.set_check_result(result, "ssl_strength", ssl_strength)

            # Certificate expiry warnings
            if days_until_expiry <= 30:
                priority = "must_fix" if days_until_expiry <= 7 else "should_fix"
                urgency = "immediately" if days_until_expiry <= 7 else "soon"
                
                self.add_business_issue(
                    result,
                    title=f"SSL certificate expires {urgency}",
                    impact=f"Website will show security warnings in {days_until_expiry} days, blocking visitors",
                    priority=priority,
                    fix_time=20,
                    difficulty="easy",
                    category="security",
                    technical_details=f"SSL certificate expires in {days_until_expiry} days",
                    fix_instructions="""HOW TO RENEW YOUR SSL CERTIFICATE BEFORE EXPIRY:

🔄 **STEP 1: IDENTIFY YOUR SSL CERTIFICATE TYPE**

Check what type of SSL certificate you have:
1. Click the lock icon in your browser address bar
2. Click "Certificate" or "View Certificate"
3. Look for the issuer name (e.g., Let's Encrypt, Cloudflare, DigiCert)

🔄 **STEP 2: RENEWAL BY CERTIFICATE TYPE**

**Let's Encrypt (Free, Auto-Renewing):**
Most hosting providers auto-renew Let's Encrypt certificates. If yours doesn't:

*Via cPanel:*
1. Log into cPanel
2. Go to "Security" → "SSL/TLS"
3. Click "Let's Encrypt SSL"
4. Find your domain and click "Renew"

*Via Command Line (VPS/Dedicated):*
```bash
# Test renewal (dry run)
sudo certbot renew --dry-run

# Actual renewal
sudo certbot renew

# Force renewal if close to expiry
sudo certbot renew --force-renewal
```

**Cloudflare (Free/Universal SSL):**
1. Log into Cloudflare dashboard
2. Go to SSL/TLS → Overview
3. If certificate shows as expired, toggle SSL off and on again
4. Wait 15 minutes for new certificate issuance

**Paid SSL Certificates (GoDaddy, Namecheap, etc.):**

*Option A: Purchase Renewal*
1. Log into your domain registrar/hosting account
2. Go to SSL certificate management
3. Click "Renew" for your certificate
4. Complete purchase (usually $50-200/year)
5. Follow installation instructions

*Option B: Switch to Free Alternative*
1. Cancel paid SSL and switch to Let's Encrypt
2. Most hosting providers offer this for free
3. Better option unless you need Extended Validation (EV)

🔄 **STEP 3: HOSTING PROVIDER SPECIFIC**

**Shared Hosting (cPanel/Plesk):**
1. Log into hosting control panel
2. Look for "SSL Certificates" or "SSL/TLS"
3. Click "Auto SSL" or "Let's Encrypt" (if available)
4. Select your domain and enable

**WordPress Hosting:**
- **WP Engine**: SSL auto-renews, contact support if issues
- **SiteGround**: Go to Site Tools → Security → SSL Manager
- **Bluehost**: Go to My Sites → Manage Sites → Security → SSL

**Cloud Hosting:**
- **AWS**: Use Certificate Manager (ACM) for auto-renewal
- **Google Cloud**: SSL certificates auto-renew
- **DigitalOcean**: Use their Load Balancer SSL or Certbot

🔄 **STEP 4: IMMEDIATE ACTIONS (If Certificate Expires Soon)**

**If expires in < 7 days:**
1. Contact hosting provider support immediately
2. Request expedited SSL renewal
3. Consider temporary Cloudflare setup:
   - Add domain to Cloudflare (free)
   - Change DNS to Cloudflare nameservers
   - Enable "Universal SSL" (takes 15 minutes)

**Emergency Cloudflare Setup:**
1. Sign up at cloudflare.com
2. Add your domain
3. Copy the 2 nameservers Cloudflare provides
4. Go to your domain registrar and update nameservers
5. Wait 24 hours for DNS propagation
6. SSL will be automatically provided

🔄 **VERIFICATION AFTER RENEWAL:**
1. Visit https://yourdomain.com
2. Click lock icon → Certificate details
3. Check "Valid until" date (should be 90 days for Let's Encrypt, 1 year for paid)
4. Test at: https://www.ssllabs.com/ssltest/
5. Use: `curl -I https://yourdomain.com` (should return 200 OK)

🔄 **SET UP AUTO-RENEWAL (PREVENT FUTURE ISSUES):**
1. **cPanel users**: Enable "Auto SSL" in SSL/TLS settings
2. **VPS users**: Add cron job: `0 12 * * * /usr/bin/certbot renew --quiet`
3. **Cloudflare users**: Automatic (no action needed)
4. **Ask hosting provider** to enable auto-renewal for your account

🔄 **COSTS BY OPTION:**
- **Let's Encrypt**: Free forever
- **Cloudflare**: Free forever
- **Paid SSL**: $50-200/year (unnecessary for most websites)
- **Extended Validation (EV)**: $100-500/year (only for major e-commerce)""",
                    business_value="Prevents website outages and security warnings",
                    recurring_check=True,
                    testing_steps=[
                        "Check certificate status in browser (click lock icon)",
                        "Use SSL checker tools to verify renewal",
                        "Set up monitoring for future expiries"
                    ]
                )

            # Check for weak SSL
            if ssl_strength == "weak":
                self.add_business_issue(
                    result,
                    title="Upgrade SSL/TLS security",
                    impact="Your encryption uses outdated protocols vulnerable to attacks",
                    priority="should_fix",
                    fix_time=45,
                    difficulty="medium",
                    category="security",
                    technical_details=f"SSL/TLS version: {cipher[1] if cipher else 'unknown'}",
                    fix_instructions="""HOW TO ENABLE MODERN TLS 1.2+ AND DISABLE OUTDATED PROTOCOLS:

⚠️ **WHY THIS MATTERS:**
Your server supports outdated SSL/TLS versions that have known security vulnerabilities. Modern browsers and security scanners flag this as a risk.

🔒 **STEP 1: CHECK CURRENT TLS CONFIGURATION**

Test your current setup:
1. Visit: https://www.ssllabs.com/ssltest/
2. Enter your domain name
3. Look for "Protocols" section in results
4. Should see: TLS 1.2 ✓ and TLS 1.3 ✓ (Good)
5. Should NOT see: SSL 2.0, SSL 3.0, TLS 1.0, TLS 1.1 (Bad)

🔒 **STEP 2: FIX BY SERVER TYPE**

**Apache Web Server:**
1. Edit your Apache SSL configuration file:
   - Usually `/etc/apache2/sites-available/default-ssl.conf`
   - Or `/etc/httpd/conf.d/ssl.conf`

2. Add these lines inside the `<VirtualHost *:443>` block:
```apache
# Enable only TLS 1.2 and 1.3
SSLProtocol all -SSLv2 -SSLv3 -TLSv1 -TLSv1.1

# Use modern cipher suites
SSLCipherSuite ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384

# Prefer server ciphers
SSLHonorCipherOrder off
SSLSessionTickets off
```

3. Restart Apache:
```bash
sudo systemctl restart apache2
# or
sudo systemctl restart httpd
```

**Nginx Web Server:**
1. Edit your Nginx SSL configuration:
   - Usually `/etc/nginx/sites-available/default`
   - Or `/etc/nginx/conf.d/default.conf`

2. Add these lines in the `server` block:
```nginx
# Enable only TLS 1.2 and 1.3
ssl_protocols TLSv1.2 TLSv1.3;

# Use modern cipher suites
ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384;

# Prefer server ciphers
ssl_prefer_server_ciphers off;

# Additional security settings
ssl_session_cache shared:le_nginx_SSL:10m;
ssl_session_timeout 1440m;
ssl_session_tickets off;
```

3. Restart Nginx:
```bash
sudo systemctl restart nginx
```

🔒 **STEP 3: HOSTING PROVIDER SOLUTIONS**

**Shared Hosting (cPanel):**
1. Log into cPanel
2. Go to "SSL/TLS" → "SSL/TLS Status"
3. Find "TLS Version" settings
4. Enable "TLS 1.2" and "TLS 1.3"
5. Disable older versions

**Cloudflare Users:**
1. Log into Cloudflare dashboard
2. Go to SSL/TLS → Edge Certificates
3. Set "Minimum TLS Version" to "TLS 1.2"
4. Enable "TLS 1.3" if available

**AWS CloudFront:**
1. Go to CloudFront console
2. Edit your distribution
3. Set "Security policy" to:
   - TLSv1.2_2021 (recommended)
   - TLSv1.2_2019 (minimum)

**Popular Hosting Providers:**

*cPanel/WHM Hosting:*
- Contact support: "Please enable TLS 1.2/1.3 and disable older SSL/TLS protocols"
- They can update this server-wide

*Managed WordPress:*
- **WP Engine**: Automatically uses modern TLS
- **SiteGround**: Go to Site Tools → Security → SSL Manager
- **Kinsta**: Contact support to verify TLS configuration

🔒 **STEP 4: APPLICATION-LEVEL FIXES**

**Node.js/Express Applications:**
```javascript
const https = require('https');
const fs = require('fs');

const options = {
  key: fs.readFileSync('path/to/private-key.pem'),
  cert: fs.readFileSync('path/to/certificate.pem'),
  secureProtocol: 'TLSv1_2_method',  // Force TLS 1.2+
  ciphers: 'ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384'
};

https.createServer(options, app).listen(443);
```

**Django Applications (settings.py):**
```python
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Force modern TLS if using gunicorn
SECURE_SSL_HOST = None
```

🔒 **VERIFICATION STEPS:**
1. Wait 5-10 minutes after making changes
2. Test at: https://www.ssllabs.com/ssltest/
3. Look for "A" or "A+" rating
4. Verify only TLS 1.2 and 1.3 are enabled
5. Check that old protocols show "No" in results

🔒 **TROUBLESHOOTING:**
- **Website not loading**: Old browsers (IE 10 and below) won't work with TLS 1.2+
- **Mobile app issues**: Update app to support modern TLS
- **API integration problems**: Update API clients to use TLS 1.2+
- **Still showing old protocols**: Clear browser cache and wait for DNS propagation

🔒 **WHAT TO TELL YOUR HOSTING PROVIDER:**
"Please configure our server to support only TLS 1.2 and TLS 1.3 protocols and disable SSLv2, SSLv3, TLS 1.0, and TLS 1.1. Also ensure we're using modern cipher suites.""",
                    business_value="Protects against known SSL vulnerabilities",
                    recurring_check=True
                )

        except socket.timeout:
            self.set_check_result(result, "ssl_valid", False)
            self.add_issue(result, "SSL certificate check timed out", "warning", "security")
            
        except ssl.SSLError as e:
            self.set_check_result(result, "ssl_valid", False)
            error_msg = str(e).lower()
            
            if "certificate verify failed" in error_msg:
                self.add_business_issue(
                    result,
                    title="Fix SSL certificate problems",
                    impact="Visitors see 'Your connection is not private' warnings",
                    priority="must_fix",
                    fix_time=60,
                    difficulty="medium",
                    category="security",
                    technical_details=f"SSL verification failed: {str(e)}",
                    fix_instructions="""URGENT: HOW TO FIX INVALID/MISCONFIGURED SSL CERTIFICATE:

🚨 **IMMEDIATE ACTIONS (Do First):**

Your SSL certificate is currently invalid, which means visitors see scary security warnings. This can severely damage trust and prevent customers from accessing your site.

**Quick Temporary Fix (5 minutes):**
1. Set up Cloudflare's free SSL:
   - Sign up at cloudflare.com
   - Add your domain
   - Change your domain's nameservers to Cloudflare's
   - Enable "Universal SSL" (automatic)
   - This provides immediate SSL protection while you fix the main issue

🔍 **STEP 1: DIAGNOSE THE SPECIFIC PROBLEM**

Check exactly what's wrong:
1. Visit: https://www.ssllabs.com/ssltest/
2. Enter your domain name
3. Look for specific error messages:
   - "Certificate name mismatch"
   - "Certificate expired"
   - "Certificate not trusted"
   - "Incomplete certificate chain"

🔧 **STEP 2: FIX BY ERROR TYPE**

**ERROR: Certificate Name Mismatch**
Your certificate doesn't match your domain name.

*Solution:*
1. Check if certificate is for www.yourdomain.com but you're using yourdomain.com (or vice versa)
2. Get a wildcard SSL certificate (covers both) OR
3. Configure redirect to match certificate name

*If using cPanel:*
1. Go to SSL/TLS → Manage SSL sites
2. Re-install certificate for correct domain
3. Or get new certificate that covers both domain variations

**ERROR: Certificate Expired**
Your SSL certificate has passed its expiration date.

*Solution:*
1. Renew immediately through your hosting provider
2. If using Let's Encrypt: `sudo certbot renew --force-renewal`
3. Contact hosting support for emergency renewal

**ERROR: Certificate Not Trusted**
The certificate authority isn't recognized.

*Solution:*
1. Replace with certificate from trusted CA (Let's Encrypt is free and trusted)
2. Remove self-signed certificates
3. Install proper intermediate certificates

**ERROR: Incomplete Certificate Chain**
Missing intermediate certificates.

*Solution:*
1. Download complete certificate bundle from your SSL provider
2. Install full chain (root + intermediate + domain certificate)
3. For Apache: Use SSLCertificateChainFile directive
4. For Nginx: Concatenate certificates in correct order

🔧 **STEP 3: HOSTING PROVIDER SPECIFIC FIXES**

**cPanel Hosting:**
1. Log into cPanel
2. Go to SSL/TLS → SSL/TLS Status
3. Click "Run AutoSSL" for your domain
4. If that fails:
   - Go to SSL/TLS → Manage SSL sites
   - Click "Browse Certificates"
   - Install new certificate

**Shared Hosting (GoDaddy, Bluehost, etc.):**
1. Log into hosting account
2. Go to SSL certificate management
3. Re-install or purchase new SSL certificate
4. Follow provider's installation guide

**WordPress Managed Hosting:**
- WP Engine: Contact support for SSL re-installation
- SiteGround: Go to Site Tools → Security → SSL Manager → Force HTTPS
- Kinsta: SSL automatically managed, contact support if broken

**Cloud Hosting:**
- AWS: Use Certificate Manager (ACM) to provision new certificate
- Google Cloud: SSL certificates through Load Balancer
- DigitalOcean: Use their SSL certificate feature or Certbot

🔧 **STEP 4: MANUAL CERTIFICATE INSTALLATION**

**If you have a valid certificate file:**

*For Apache:*
1. Upload certificate files to server
2. Edit SSL configuration:
```apache
SSLCertificateFile /path/to/yourdomain.crt
SSLCertificateKeyFile /path/to/private.key
SSLCertificateChainFile /path/to/intermediate.crt
```
3. Restart Apache: `sudo systemctl restart apache2`

*For Nginx:*
1. Combine certificate and intermediate:
   `cat yourdomain.crt intermediate.crt > combined.crt`
2. Edit Nginx configuration:
```nginx
ssl_certificate /path/to/combined.crt;
ssl_certificate_key /path/to/private.key;
```
3. Restart Nginx: `sudo systemctl restart nginx`

🔧 **STEP 5: GET FREE SSL CERTIFICATE (RECOMMENDED)**

**Option A: Let's Encrypt (Free Forever)**
```bash
# Install Certbot
sudo apt install certbot python3-certbot-apache

# Get certificate for Apache
sudo certbot --apache -d yourdomain.com -d www.yourdomain.com

# Get certificate for Nginx
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Manual certificate (if above don't work)
sudo certbot certonly --manual -d yourdomain.com
```

**Option B: Cloudflare (Free Forever)**
1. Add domain to Cloudflare
2. Update nameservers at domain registrar
3. SSL automatically provided within 15 minutes
4. No server configuration needed

🔧 **VERIFICATION AFTER FIX:**
1. Clear browser cache completely
2. Visit https://yourdomain.com in incognito/private mode
3. Check for green lock icon
4. Test at: https://www.ssllabs.com/ssltest/
5. Should receive A or A+ rating
6. Test all subdomains and pages

🔧 **PREVENT FUTURE ISSUES:**
1. Enable auto-renewal for SSL certificates
2. Set up monitoring alerts for certificate expiry
3. Use Cloudflare as backup SSL provider
4. Document your SSL setup for team members

⚠️ **IF NOTHING WORKS:**
Contact your hosting provider with this message:
"Our SSL certificate is invalid/misconfigured and showing security warnings to visitors. Please immediately install a new SSL certificate for [yourdomain.com] and ensure it's properly configured. This is urgent as it's preventing customers from accessing our website."

Include these details:
- Domain name
- Error message from SSL Labs test
- When the issue started
- Request completion within 24 hours""",
                    business_value="Removes security warnings that prevent customers from accessing your site",
                    recurring_check=True
                )
                
        except Exception as e:
            self.set_check_result(result, "ssl_valid", None)
            logger.debug(f"SSL check failed: {str(e)}")

    def _check_security_headers(self, response: Response, result: dict) -> None:
        """Check for important security headers comprehensively using the headers service."""
        try:
            # Use the comprehensive security headers service
            headers_analysis = self.headers_service.analyze_security_headers(response, result)
            
            # Store the analysis results
            result["security_headers_analysis"] = headers_analysis
            
            # Add business issues for missing critical headers
            missing_headers = headers_analysis.get("missing_headers", [])
            invalid_headers = headers_analysis.get("invalid_headers", [])
            
            # Create business issues for missing headers
            for header_name in missing_headers:
                header_config = self.headers_service.security_headers[header_name]

                # Handle both old string format and new object format for difficulty
                difficulty = header_config["difficulty"]
                difficulty_level = difficulty["level"] if isinstance(difficulty, dict) else difficulty
                difficulty_description = difficulty.get("description") if isinstance(difficulty, dict) else None

                self.add_business_issue(
                    result,
                    title=header_config['title'],
                    impact=header_config["impact"],
                    priority=header_config["priority"],
                    fix_time=header_config["fix_time"],
                    difficulty=difficulty_level,
                    difficulty_description=difficulty_description,
                    category="security",
                    technical_details=f"Missing {header_name} security header",
                    fix_instructions=header_config["fix_instructions"],
                    business_value=f"Provides protection against {header_config['description'].lower()}",
                    recurring_check=True,
                    code_snippets=header_config.get("code_snippets", []),
                    testing_steps=header_config.get("testing_steps", [])
                )
            
            # Create business issues for invalid headers
            for header_name in invalid_headers:
                header_config = self.headers_service.security_headers[header_name]
                header_analysis = headers_analysis["headers_analysis"][header_name]

                # Handle both old string format and new object format for difficulty
                difficulty = header_config["difficulty"]
                difficulty_level = difficulty["level"] if isinstance(difficulty, dict) else difficulty
                difficulty_description = difficulty.get("description") if isinstance(difficulty, dict) else None

                self.add_business_issue(
                    result,
                    title=f"Invalid {header_config['title'].replace('Missing ', '')}",
                    impact=f"Header present but misconfigured: {header_analysis['validation_message']}",
                    priority=header_config["priority"],
                    fix_time=header_config["fix_time"],
                    difficulty=difficulty_level,
                    difficulty_description=difficulty_description,
                    category="security",
                    technical_details=f"Invalid {header_name} header: {header_analysis['value']}",
                    fix_instructions=header_config["fix_instructions"],
                    business_value=f"Ensures proper {header_config['description'].lower()}",
                    recurring_check=True,
                    code_snippets=header_config.get("code_snippets", [])
                )
            
            # Store individual header check results for backwards compatibility
            for header_name, header_analysis in headers_analysis["headers_analysis"].items():
                header_key = header_name.replace("-", "_") + "_present"
                self.set_check_result(result, header_key, header_analysis["present"])
                
                if header_analysis["present"]:
                    valid_key = header_name.replace("-", "_") + "_valid"
                    self.set_check_result(result, valid_key, header_analysis["valid"])

        except Exception as e:
            self.add_issue(result, f"Error checking security headers: {str(e)}", "warning", "security")

    def _check_mixed_content(self, soup: Optional[BeautifulSoup], result: dict) -> None:
        """Check for mixed content issues on HTTPS sites."""
        if not soup or not result.get("checks", {}).get("security_uses_https", False):
            self.set_check_result(result, "mixed_content_issues", 0)
            return
        
        try:
            mixed_content_count = 0
            
            # Check for HTTP resources in various tags
            http_resources = []
            
            # Images
            for img in soup.find_all("img", src=True):
                if img["src"].startswith("http://"):
                    http_resources.append(f"Image: {img['src']}")
                    mixed_content_count += 1
            
            # Scripts
            for script in soup.find_all("script", src=True):
                if script["src"].startswith("http://"):
                    http_resources.append(f"Script: {script['src']}")
                    mixed_content_count += 1
            
            # Stylesheets
            for link in soup.find_all("link", href=True):
                if link["href"].startswith("http://"):
                    http_resources.append(f"Stylesheet: {link['href']}")
                    mixed_content_count += 1
            
            self.set_check_result(result, "mixed_content_issues", mixed_content_count)
            
            if mixed_content_count > 0:
                self.add_business_issue(
                    result,
                    title="Fix mixed content warnings",
                    impact=f"Browsers show security warnings due to {mixed_content_count} insecure HTTP resources",
                    priority="should_fix",
                    fix_time=mixed_content_count * 5,
                    difficulty="easy",
                    category="security",
                    technical_details=f"Found {mixed_content_count} HTTP resources on HTTPS page",
                    fix_instructions="Change all HTTP:// links to HTTPS:// or use protocol-relative URLs (//)",
                    business_value="Removes browser security warnings and maintains visitor trust",
                    recurring_check=True,
                    code_snippets=[
                        {
                            "title": "Fix Mixed Content URLs",
                            "code": "<!-- Bad: HTTP on HTTPS page -->\n<img src=\"http://example.com/image.jpg\">\n\n<!-- Good: HTTPS -->\n<img src=\"https://example.com/image.jpg\">\n\n<!-- Good: Protocol relative -->\n<img src=\"//example.com/image.jpg\">",
                            "language": "html"
                        }
                    ]
                )
                
        except Exception as e:
            self.add_issue(result, f"Error checking mixed content: {str(e)}", "warning", "security")

    def _check_form_security(self, soup: Optional[BeautifulSoup], result: dict) -> None:
        """Check for insecure form submissions."""
        if not soup:
            self.set_check_result(result, "insecure_forms", 0)
            return
        
        try:
            insecure_forms = 0
            forms = soup.find_all("form")
            
            for form in forms:
                action = form.get("action", "")
                method = form.get("method", "GET").upper()
                
                # Check for forms submitting sensitive data over HTTP
                if action.startswith("http://") and method == "POST":
                    # Check if form contains password or sensitive fields
                    has_sensitive = any(
                        inp.get("type") in ["password", "email"] or 
                        "password" in inp.get("name", "").lower() or
                        "email" in inp.get("name", "").lower()
                        for inp in form.find_all("input")
                    )
                    
                    if has_sensitive:
                        insecure_forms += 1
            
            self.set_check_result(result, "insecure_forms", insecure_forms)
            
            if insecure_forms > 0:
                self.add_business_issue(
                    result,
                    title="Secure your forms",
                    impact=f"{insecure_forms} forms send sensitive data over insecure HTTP",
                    priority="must_fix",
                    fix_time=20,
                    difficulty="easy",
                    category="security",
                    technical_details="Forms with sensitive data submitting via HTTP",
                    fix_instructions="Change form action URLs from HTTP to HTTPS",
                    business_value="Protects customer passwords and personal information",
                    recurring_check=True,
                    code_snippets=[
                        {
                            "title": "Secure Form Action",
                            "code": "<!-- Bad: Insecure form -->\n<form method=\"POST\" action=\"http://example.com/login\">\n\n<!-- Good: Secure form -->\n<form method=\"POST\" action=\"https://example.com/login\">\n\n<!-- Good: Relative URL (inherits protocol) -->\n<form method=\"POST\" action=\"/login\">",
                            "language": "html"
                        }
                    ]
                )
                
        except Exception as e:
            self.add_issue(result, f"Error checking form security: {str(e)}", "warning", "security")

    def _check_cookie_security(self, response: Response, result: dict) -> None:
        """Check cookie security attributes."""
        try:
            insecure_cookies = 0
            total_cookies = 0
            
            # Check Set-Cookie headers
            set_cookies = response.headers.get_list("Set-Cookie") or []
            
            for cookie_header in set_cookies:
                total_cookies += 1
                cookie_lower = cookie_header.lower()
                
                # Check for missing security attributes
                has_secure = "secure" in cookie_lower
                has_httponly = "httponly" in cookie_lower
                has_samesite = "samesite" in cookie_lower
                
                # Only flag as insecure if missing critical attributes on HTTPS
                uses_https = result.get("checks", {}).get("security_uses_https", False)
                if uses_https and not has_secure:
                    insecure_cookies += 1
                elif not has_httponly and ("session" in cookie_lower or "auth" in cookie_lower):
                    insecure_cookies += 1
            
            self.set_check_result(result, "insecure_cookies", insecure_cookies)
            self.set_check_result(result, "total_cookies", total_cookies)
            
            if insecure_cookies > 0 and total_cookies > 0:
                self.add_business_issue(
                    result,
                    title="Secure your cookies",
                    impact=f"{insecure_cookies} cookies lack security attributes, risking session theft",
                    priority="nice_to_have",
                    fix_time=25,
                    difficulty="medium",
                    category="security",
                    technical_details="Cookies missing Secure, HttpOnly, or SameSite attributes",
                    fix_instructions="""HOW TO SECURE COOKIES WITH PROPER ATTRIBUTES:

🍪 **WHY COOKIE SECURITY MATTERS:**
Insecure cookies can be stolen by attackers, leading to account hijacking, session theft, and cross-site attacks. Proper cookie attributes are essential for user security.

🛡️ **STEP 1: UNDERSTAND COOKIE SECURITY ATTRIBUTES**

**Secure**: Cookie only sent over HTTPS (prevents man-in-the-middle attacks)
**HttpOnly**: Cookie not accessible via JavaScript (prevents XSS attacks)
**SameSite**: Controls cross-site cookie sending (prevents CSRF attacks)

🛡️ **STEP 2: FIX BY PLATFORM**

**PHP Applications:**
```php
// Set secure session cookies
ini_set('session.cookie_secure', 1);        // Secure
ini_set('session.cookie_httponly', 1);      // HttpOnly
ini_set('session.cookie_samesite', 'Strict'); // SameSite

// Or set individual cookies
setcookie('session_id', $value, [
    'expires' => time() + 3600,
    'path' => '/',
    'domain' => '.yourdomain.com',
    'secure' => true,      // Only over HTTPS
    'httponly' => true,    // No JavaScript access
    'samesite' => 'Strict' // Strict same-site policy
]);

// In php.ini file:
session.cookie_secure = 1
session.cookie_httponly = 1
session.cookie_samesite = "Strict"
```

**Node.js/Express Applications:**
```javascript
const session = require('express-session');

app.use(session({
  name: 'sessionId',
  secret: 'your-secret-key',
  cookie: {
    secure: true,        // Only over HTTPS
    httpOnly: true,      // No JavaScript access
    maxAge: 3600000,     // 1 hour
    sameSite: 'strict'   // Strict same-site policy
  },
  resave: false,
  saveUninitialized: false
}));

// For individual cookies
res.cookie('name', 'value', {
  secure: true,
  httpOnly: true,
  sameSite: 'strict'
});
```

**Django Applications (settings.py):**
```python
# Session cookie security
SESSION_COOKIE_SECURE = True        # Only over HTTPS
SESSION_COOKIE_HTTPONLY = True      # No JavaScript access
SESSION_COOKIE_SAMESITE = 'Strict'  # Strict same-site policy

# CSRF cookie security
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Strict'

# Additional security settings
SESSION_COOKIE_AGE = 3600  # 1 hour
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
```

**Java/Spring Applications:**
```java
// In application.properties
server.servlet.session.cookie.secure=true
server.servlet.session.cookie.http-only=true
server.servlet.session.cookie.same-site=strict

// Or programmatically
@Bean
public CookieSameSiteSupplier cookieSameSiteSupplier() {
    return CookieSameSiteSupplier.ofStrict();
}
```

**ASP.NET Applications:**
```csharp
// In web.config
<system.web>
  <httpCookies requireSSL="true" httpOnlyCookies="true" samesite="Strict" />
</system.web>

// Or programmatically
Response.Cookies.Add(new HttpCookie("sessionId", value) {
    Secure = true,
    HttpOnly = true,
    SameSite = SameSiteMode.Strict
});
```

🛡️ **STEP 3: WEB SERVER CONFIGURATION**

**Apache (.htaccess):**
```apache
# Set secure cookie headers
Header always edit Set-Cookie ^(.*)$ "$1; Secure; HttpOnly; SameSite=Strict"

# Alternative for specific cookies
Header always edit Set-Cookie ^(sessionid=.*)$ "$1; Secure; HttpOnly; SameSite=Strict"
```

**Nginx:**
```nginx
# Add to server block
location / {
    # Proxy to your application
    proxy_pass http://localhost:8000;

    # Modify cookie headers
    proxy_cookie_flags ~ secure httponly samesite=strict;
}

# Alternative method
add_header Set-Cookie "sessionid=value; Secure; HttpOnly; SameSite=Strict";
```

🛡️ **STEP 4: WORDPRESS SPECIFIC**

**WordPress Security Plugins:**
1. Install "Cookie Notice & Compliance" plugin
2. Go to Settings → Cookie Notice
3. Enable "Secure cookies"
4. Set SameSite to "Strict"

**WordPress Code (wp-config.php):**
```php
// Force secure cookies
ini_set('session.cookie_secure', 1);
ini_set('session.cookie_httponly', 1);

// Add to functions.php
add_action('init', function() {
    if (is_ssl()) {
        ini_set('session.cookie_secure', 1);
    }
});
```

🛡️ **STEP 5: CONTENT MANAGEMENT SYSTEMS**

**Drupal:**
```php
// In settings.php
$settings['session_cookie_secure'] = TRUE;
$settings['session_cookie_httponly'] = TRUE;
$settings['session_cookie_samesite'] = 'Strict';
```

**Magento:**
```php
// In app/etc/env.php
'session' => [
    'save' => 'files',
    'cookie_secure' => 1,
    'cookie_httponly' => 1,
    'cookie_samesite' => 'Strict'
]
```

🛡️ **STEP 6: CLOUD PLATFORM CONFIGURATION**

**Cloudflare:**
1. Log into Cloudflare dashboard
2. Go to Security → Bot Management
3. Enable "Cookie Security"
4. Set security level to "High"

**AWS CloudFront:**
```json
{
  "ViewerProtocolPolicy": "redirect-to-https",
  "CookiesForward": "whitelist",
  "CookieNames": ["session"],
  "Headers": {
    "Set-Cookie": "Secure; HttpOnly; SameSite=Strict"
  }
}
```

🛡️ **VERIFICATION STEPS:**

**Method 1: Browser Developer Tools**
1. Open website in Chrome/Firefox
2. Press F12 → Network tab
3. Look for Set-Cookie headers in responses
4. Verify cookies show: `Secure; HttpOnly; SameSite=Strict`

**Method 2: Command Line Testing**
```bash
# Check cookie headers
curl -I https://yourdomain.com

# Look for Set-Cookie headers with proper attributes
```

**Method 3: Online Security Scanners**
- https://securityheaders.com
- https://observatory.mozilla.org
- Check "Cookies" section for security rating

🛡️ **TROUBLESHOOTING COMMON ISSUES:**

**Problem: Login not working after changes**
- Check if you're accessing site via HTTP instead of HTTPS
- Ensure SSL certificate is properly installed
- Clear browser cookies and try again

**Problem: AJAX requests failing**
- Set SameSite to "Lax" instead of "Strict" for cross-origin requests
- Ensure proper CSRF token handling

**Problem: Third-party integrations broken**
- Use SameSite="None; Secure" for specific third-party cookies
- Test integrations after changes

🛡️ **BEST PRACTICES:**
1. Always use "Secure" flag for HTTPS sites
2. Use "HttpOnly" for session cookies (prevents XSS)
3. Use "SameSite=Strict" for highest security
4. Set reasonable expiration times
5. Implement proper session management
6. Regularly audit cookie usage

⚠️ **EMERGENCY ROLLBACK:**
If changes break your site:
1. Remove the cookie configuration changes
2. Restart your web server
3. Clear browser cookies
4. Re-implement gradually with testing""",
                    business_value="Protects user sessions from theft and cross-site attacks",
                    recurring_check=True,
                    code_snippets=[
                        {
                            "title": "Secure Cookie Attributes",
                            "code": "// PHP example\nsetcookie('session_id', $value, [\n    'secure' => true,      // HTTPS only\n    'httponly' => true,    // No JavaScript access\n    'samesite' => 'Strict' // CSRF protection\n]);",
                            "language": "php"
                        }
                    ]
                )
                
        except Exception as e:
            self.add_issue(result, f"Error checking cookie security: {str(e)}", "warning", "security")

    def _calculate_security_score(self, result: dict) -> None:
        """Calculate overall security score based on findings."""
        checks = result.get("checks", {})
        business_issues = result.get("business_issues", [])
        headers_analysis = result.get("security_headers_analysis", {})
        
        # Start with perfect score
        score = 100
        
        # Critical HTTPS penalty (reduced to industry standard)
        if not checks.get("security_uses_https", False):
            score -= 15  # Reduced from 40 to align with industry standards
        
        # SSL certificate issues (reduced penalties)
        if checks.get("security_ssl_valid", None) is False:
            score -= 10  # Reduced from 25
        elif checks.get("security_ssl_expires_soon", False):
            days = checks.get("security_ssl_days_until_expiry", 30)
            penalty = 8 if days <= 7 else 4  # Reduced from 20/10
            score -= penalty
        
        # Security headers penalty (reduced by 50%)
        if headers_analysis:
            score_impact = headers_analysis.get("security_score_impact", {})
            score_deduction = score_impact.get("score_deduction", 0)
            score -= int(score_deduction * 0.5)  # Reduce header penalty by 50%
            
        # Mixed content penalty (reduced)
        mixed_content = checks.get("security_mixed_content_issues", 0)
        if mixed_content > 0:
            score -= min(mixed_content * 2, 8)  # Reduced from 5 per issue, cap at 8
        
        # Insecure forms penalty (reduced)
        insecure_forms = checks.get("security_insecure_forms", 0)
        if insecure_forms > 0:
            score -= insecure_forms * 8  # Reduced from 15
        
        # Note: Business issues penalties are now handled by the frontend display
        # and the score breakdown API. This prevents double-counting of penalties.
        # The SecurityChecker now only handles critical infrastructure penalties
        # (HTTPS, SSL, headers, mixed content, forms) while business issues
        # are displayed separately in the frontend with their individual point values.
        
        # Apply positive scoring for excellent security practices
        bonus = 0
        if checks.get("security_uses_https", False) and checks.get("security_ssl_valid", False):
            bonus += 5  # HTTPS + Valid SSL combo bonus
        
        if checks.get("security_no_mixed_content", True):
            bonus += 3  # No mixed content bonus
        
        if checks.get("security_secure_forms", True):
            bonus += 2  # Secure forms bonus
        
        # Check if all major security headers are present
        if headers_analysis:
            missing_headers = headers_analysis.get("missing_headers", [])
            if len(missing_headers) == 0:
                bonus += 8  # All headers present bonus
        
        score = min(100, score + bonus)  # Apply bonus but cap at 100
        score = max(0, score)
        self.set_check_result(result, "security_score", score)
        result["security_score"] = score
        
        # Generate security summary
        result["security_summary"] = {
            "score": score,
            "level": self._get_security_level(score),
            "uses_https": checks.get("security_uses_https", False),
            "ssl_valid": checks.get("security_ssl_valid", False),
            "ssl_expires_in_days": checks.get("security_ssl_days_until_expiry"),
            "security_headers": {
                "total_checked": headers_analysis.get("total_headers_checked", 0),
                "present": headers_analysis.get("headers_present", 0),
                "valid": headers_analysis.get("headers_valid", 0),
                "missing": len(headers_analysis.get("missing_headers", [])),
                "invalid": len(headers_analysis.get("invalid_headers", []))
            } if headers_analysis else {},
            "mixed_content_issues": checks.get("security_mixed_content_issues", 0),
            "insecure_forms": checks.get("security_insecure_forms", 0),
            "issues_found": len(security_issues),
            "critical_issues": len([i for i in security_issues if i.get("priority", {}).get("order") == 1])
        }

    def _get_security_level(self, score: int) -> str:
        """Convert score to security level description."""
        if score >= 90:
            return "excellent"
        elif score >= 75:
            return "good"
        elif score >= 60:
            return "fair"
        else:
            return "poor"