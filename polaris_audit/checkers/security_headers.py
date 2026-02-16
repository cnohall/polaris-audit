from typing import Dict, Any, List, Tuple
from requests import Response


class SecurityHeadersService:
    """Comprehensive security headers analysis service."""
    
    def __init__(self):
        # Define all critical security headers with their expected values and validation
        self.security_headers = {
            "strict-transport-security": {
                "title": "Missing Strict-Transport-Security (HSTS)",
                "description": "Your website doesn't force browsers to use secure HTTPS connections, allowing potential security risks",
                "expected_values": ["max-age="],
                "validation": self._validate_hsts,
                "priority": "must_fix",
                "fix_time": 15,
                "difficulty": {"level": "easy", "description": "Simple hosting configuration"},
                "impact": "Visitors could accidentally use the insecure HTTP version of your site, making their data vulnerable to interception",
                "fix_instructions": """STEP-BY-STEP GUIDE TO ADD STRICT-TRANSPORT-SECURITY (HSTS):

1. FIRST, ENSURE YOUR WEBSITE HAS HTTPS:
   - Your website must have an SSL certificate installed
   - The website should load with https:// (not http://)
   - If you don't have HTTPS, contact your hosting provider first

2. FOR WORDPRESS USERS (Easiest):
   - Install "Really Simple SSL" or "Security Headers" plugin
   - Go to plugin settings
   - Enable "Strict Transport Security" or "HSTS"
   - The plugin will automatically add the security header

3. FOR SHARED HOSTING (.htaccess method):
   - Log into your hosting control panel
   - Go to File Manager
   - Navigate to your website's root folder (usually public_html)
   - Open or create .htaccess file
   - Add this line:
     Header always set Strict-Transport-Security "max-age=31536000; includeSubDomains"
   - Save the file

4. FOR ADVANCED USERS:
   - Apache: Add to .htaccess or httpd.conf
   - Nginx: Add to server block
   - Use code snippets below

5. TEST YOUR CHANGES:
   - Visit your website using http:// (not https://)
   - Your browser should automatically redirect to https://
   - Check that all pages load correctly with https://

6. VERIFY IT'S WORKING:
   - Use securityheaders.com to check
   - Look for "Strict-Transport-Security" in the results
   - Run another Polaris Audit scan

IMPORTANT: Once you add this header, browsers will remember to use HTTPS for 1 year. Make sure your HTTPS is working properly before adding this!""",
                "code_snippets": [
                    {
                        "title": "Apache (.htaccess)",
                        "code": "Header always set Strict-Transport-Security \"max-age=31536000; includeSubDomains\"",
                        "language": "apache"
                    },
                    {
                        "title": "Nginx",
                        "code": "add_header Strict-Transport-Security \"max-age=31536000; includeSubDomains\" always;",
                        "language": "nginx"
                    },
                    {
                        "title": "Express.js (Node.js)",
                        "code": "app.use((req, res, next) => {\n  res.setHeader('Strict-Transport-Security', 'max-age=31536000; includeSubDomains');\n  next();\n});",
                        "language": "javascript"
                    },
                    {
                        "title": "PHP",
                        "code": "<?php\nheader('Strict-Transport-Security: max-age=31536000; includeSubDomains');\n?>",
                        "language": "php"
                    }
                ],
                "testing_steps": [
                    "Open your website in a browser",
                    "Press F12 to open Developer Tools",
                    "Go to Network tab and refresh the page",
                    "Click on any request and look for 'Strict-Transport-Security' in Response Headers",
                    "Use online tools like securityheaders.com to verify"
                ]
            },
            "content-security-policy": {
                "title": "Add Website Security Policy (CSP)",
                "description": "Think of this as a 'bouncer' for your website that decides what code can run and what external resources can load. Without it, malicious hackers can inject harmful code that steals passwords, credit card info, or redirects visitors to scam sites.",
                "expected_values": ["default-src", "script-src", "style-src"],
                "validation": self._validate_csp,
                "priority": "must_fix",
                "fix_time": 30,
                "difficulty": {"level": "medium", "description": "Technical setup required, but step-by-step instructions provided"},
                "impact": "Without CSP, hackers can easily inject malicious code that steals user passwords, payment details, or personal information. Real example: British Airways was fined £20 million after hackers injected code that harvested 400,000 customers' payment details - CSP would have blocked this attack.",
                "fix_instructions": """🛡️ WHAT IS CONTENT SECURITY POLICY (CSP)?

CSP is like a security guard for your website. It tells browsers:
- "Only run code from trusted sources"
- "Block any suspicious scripts that hackers try to inject"
- "Don't load images/videos from unknown websites"

Real example: In 2022, over 60% of website hacks involved injected scripts that CSP would have blocked.

📋 STEP-BY-STEP FIX GUIDE:

🔧 METHOD 1: WORDPRESS USERS (EASIEST - 5 MINUTES)
1. Install "Security Headers" plugin from WordPress admin
2. Go to Settings → Security Headers
3. Enable "Content Security Policy"
4. Choose "Basic Protection" (safe starting point)
5. Click "Save" and test your website
6. If everything works, upgrade to "Enhanced Protection"

🔧 METHOD 2: SHARED HOSTING (.htaccess file - 10 MINUTES)
1. Login to your hosting control panel (cPanel, etc.)
2. Open "File Manager"
3. Navigate to your website's main folder (public_html)
4. Find or create file named ".htaccess"
5. Add the security header code (see code snippets below)
6. Save file and test your website

🔧 METHOD 3: CLOUD/VPS HOSTING (ADVANCED - 15 MINUTES)
1. Access your server configuration
2. Add CSP headers to your web server config
3. Use the appropriate code for Apache/Nginx (see snippets)
4. Restart web server and test

🔧 METHOD 4: STATIC HOSTING PLATFORMS (Netlify, Vercel, GitHub Pages - 10 MINUTES)
⚠️ COMMON ISSUE: If your site uses React/Vue/static hosting, traditional .htaccess won't work!

FOR NETLIFY (Choose one method):
METHOD A - _headers file (for simple sites):
1. Create file named "_headers" in your public/static folder
2. Add the header configuration (see "Netlify Headers" code snippet below)
3. Deploy your site - Netlify will automatically apply the headers

METHOD B - netlify.toml (for build configurations):
1. Create or edit "netlify.toml" in your project root
2. Add headers section (see "Netlify TOML" code snippet below)
3. Deploy your changes - this method works with build processes

FOR VERCEL:
1. Create or edit "vercel.json" in your project root
2. Add headers configuration (see "Vercel Config" code snippet)
3. Deploy your changes

FOR GITHUB PAGES:
1. GitHub Pages has limited header support
2. Consider moving to Netlify/Vercel for better security header support
3. Or use Cloudflare as a proxy to add security headers

⚠️ IMPORTANT: Start with the "Basic" security policy first, then strengthen it after testing!

✅ HOW TO TEST IF IT'S WORKING:
1. Visit your website - everything should still work normally
2. Go to securityheaders.com and enter your website URL
3. Look for "Content-Security-Policy" in the results
4. If you see a green checkmark, you're protected!

🔧 IF SOMETHING BREAKS (Don't panic!):
- Your website's features (forms, videos, etc.) might stop working
- This means the security policy is too strict
- Use the troubleshooting guide below to fix specific issues
- You can always remove the policy and start over with a more permissive one""",
                "code_snippets": [
                    {
                        "title": "🚀 Basic Protection (.htaccess) - Start Here!",
                        "description": "Safe starting point - allows most normal website features to work",
                        "code": "# Add this to your .htaccess file\nHeader always set Content-Security-Policy \"default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:;\"",
                        "language": "apache"
                    },
                    {
                        "title": "🛡️ Enhanced Protection - After Testing Basic",
                        "description": "Stronger security - test this after the basic version works",
                        "code": "# Enhanced security policy\nHeader always set Content-Security-Policy \"default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self'; frame-ancestors 'none';\"",
                        "language": "apache"
                    },
                    {
                        "title": "📊 With Google Analytics/Marketing Tools",
                        "description": "If you use Google Analytics, Facebook Pixel, or other tracking",
                        "code": "# Policy that allows common marketing tools\nHeader always set Content-Security-Policy \"default-src 'self'; script-src 'self' 'unsafe-inline' https://www.googletagmanager.com https://www.google-analytics.com https://connect.facebook.net; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:;\"",
                        "language": "apache"
                    },
                    {
                        "title": "🖥️ For Nginx Servers",
                        "description": "If your website runs on Nginx instead of Apache",
                        "code": "# Add to your Nginx server configuration\nadd_header Content-Security-Policy \"default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:;\" always;",
                        "language": "nginx"
                    },
                    {
                        "title": "🌐 Netlify Headers File",
                        "description": "For React/Vue/static sites hosted on Netlify (Method A)",
                        "code": "# Create file: public/_headers\n\n/*\n  Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:;\n  X-Frame-Options: DENY\n  X-Content-Type-Options: nosniff\n  X-XSS-Protection: 1; mode=block",
                        "language": "text"
                    },
                    {
                        "title": "🔧 Netlify TOML Configuration",
                        "description": "For projects with build processes (Method B) - works better with complex builds",
                        "code": "# Create or edit: netlify.toml in project root\n\n[[headers]]\n  for = \"/*\"\n  [headers.values]\n    Content-Security-Policy = \"default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:;\"\n    X-Frame-Options = \"DENY\"\n    X-Content-Type-Options = \"nosniff\"\n    X-XSS-Protection = \"1; mode=block\"\n    Referrer-Policy = \"strict-origin-when-cross-origin\"",
                        "language": "toml"
                    },
                    {
                        "title": "⚡ Vercel Configuration",
                        "description": "For Next.js/React apps hosted on Vercel",
                        "code": "{\n  \"headers\": [\n    {\n      \"source\": \"/(.*)\",\n      \"headers\": [\n        {\n          \"key\": \"Content-Security-Policy\",\n          \"value\": \"default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:;\"\n        },\n        {\n          \"key\": \"X-Frame-Options\",\n          \"value\": \"DENY\"\n        }\n      ]\n    }\n  ]\n}",
                        "language": "json"
                    }
                ],
                "testing_steps": [
                    {
                        "step": "1. Apply the CSP Policy",
                        "action": "Add the Content-Security-Policy header using one of the methods above",
                        "expected": "File should be saved without errors"
                    },
                    {
                        "step": "2. Test Your Website",
                        "action": "Visit every important page of your website (homepage, contact, shop, etc.)",
                        "expected": "Everything should look and work normally"
                    },
                    {
                        "step": "3. Check for Errors",
                        "action": "Press F12 to open browser developer tools, go to Console tab",
                        "expected": "No red CSP violation errors should appear"
                    },
                    {
                        "step": "4. Test Interactive Features",
                        "action": "Try contact forms, search boxes, shopping cart, login, etc.",
                        "expected": "All features should work as before"
                    },
                    {
                        "step": "5. For Static Hosting: Wait for Deployment",
                        "action": "If using Netlify/Vercel, wait 2-5 minutes after deployment for headers to take effect. CDN cache may need to clear.",
                        "expected": "Headers should propagate across CDN nodes"
                    },
                    {
                        "step": "6. Verify CSP is Active",
                        "action": "Go to securityheaders.com and enter your website URL",
                        "expected": "Should show Content-Security-Policy with a green grade"
                    },
                    {
                        "step": "7. Run Another Scan",
                        "action": "Use Polaris Audit to scan your website again",
                        "expected": "CSP issue should be marked as fixed"
                    }
                ],
                "troubleshooting": [
                    {
                        "problem": "🚫 Website looks broken / no styling",
                        "solution": "Your CSS is being blocked. Add 'unsafe-inline' to style-src in your CSP policy.",
                        "code": "style-src 'self' 'unsafe-inline';"
                    },
                    {
                        "problem": "🚫 JavaScript features stopped working",
                        "solution": "Your scripts are being blocked. Add 'unsafe-inline' to script-src (temporary fix).",
                        "code": "script-src 'self' 'unsafe-inline';"
                    },
                    {
                        "problem": "🚫 Google Analytics / Facebook Pixel not working",
                        "solution": "External tracking tools are blocked. Add their domains to script-src.",
                        "code": "script-src 'self' https://www.google-analytics.com https://connect.facebook.net;"
                    },
                    {
                        "problem": "🚫 Images not loading",
                        "solution": "Image sources are restricted. Allow data URLs and HTTPS images.",
                        "code": "img-src 'self' data: https:;"
                    },
                    {
                        "problem": "🚫 Contact forms not submitting",
                        "solution": "Form submissions are blocked. Allow your domain and any form services.",
                        "code": "connect-src 'self' https://your-form-service.com;"
                    },
                    {
                        "problem": "🚫 Fonts not loading (Google Fonts, etc.)",
                        "solution": "External fonts are blocked. Allow font sources.",
                        "code": "font-src 'self' https://fonts.gstatic.com;"
                    },
                    {
                        "problem": "🚫 Embedded videos/maps not showing",
                        "solution": "Embedded content is blocked. Allow iframe sources.",
                        "code": "frame-src 'self' https://www.youtube.com https://maps.google.com;"
                    },
                    {
                        "problem": "🌐 Headers not working on Netlify/Vercel",
                        "solution": "Check file is in correct location. For Netlify: try both public/_headers OR netlify.toml in root. For Vercel: vercel.json in root. Redeploy after changes.",
                        "code": "Netlify Method A: /public/_headers\nNetlify Method B: /netlify.toml (project root)\nVercel: /vercel.json (project root)"
                    },
                    {
                        "problem": "⏰ Headers not appearing immediately after deployment",
                        "solution": "CDN cache needs time to update. Wait 5-10 minutes, then hard refresh browser (Ctrl+F5) and test again.",
                        "code": "curl -I https://yoursite.com | grep -i content-security-policy"
                    },
                    {
                        "problem": "⚠️ Still getting CSP errors in browser console",
                        "solution": "Open browser developer tools (F12), go to Console tab, and look for CSP violation messages. They'll tell you exactly what to allow.",
                        "code": "Look for messages like: 'Refused to load... because it violates the CSP directive'"
                    }
                ],
                "resources": [
                    {
                        "label": "Security Policy Tester - Check if your policy works",
                        "url": "https://csp-evaluator.withgoogle.com/"
                    },
                    {
                        "label": "Security Policy Generator - Create policies easily",
                        "url": "https://report-uri.com/home/generate"
                    },
                    {
                        "label": "Complete Guide to Website Security Policies",
                        "url": "https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP"
                    }
                ]
            },
            "x-frame-options": {
                "title": "Stop Clickjacking Attacks (X-Frame-Options)",
                "description": "Think of this as preventing your website from being 'kidnapped' and hidden inside malicious websites. Without this protection, scammers can invisibly embed your site and trick users into clicking buttons they can't see - like transferring money or changing passwords.",
                "expected_values": ["DENY", "SAMEORIGIN"],
                "validation": self._validate_frame_options,
                "priority": "must_fix",
                "fix_time": 5,
                "difficulty": {"level": "easy", "description": "Simple one-line addition to website settings"},
                "impact": "Without X-Frame-Options, attackers can create 'invisible overlay' scams where users think they're clicking on a harmless website but are actually performing actions on your site. Real example: Banking sites without this protection have seen customers unknowingly transfer money through clickjacking attacks.",
                "fix_instructions": """🛡️ WHAT IS CLICKJACKING?

Imagine someone puts an invisible glass sheet over your front door with a fake doorbell button. When visitors think they're ringing your doorbell, they're actually pressing something else entirely. That's exactly what clickjacking does to websites.

Real attack example: Scammers overlay your banking login page on a fake "Win $1000!" button. Users think they're entering a contest, but they're actually logging into their bank account and transferring money.

X-Frame-Options is like a security system that says "No invisible glass sheets allowed!"

📋 STEP-BY-STEP FIX GUIDE (5 MINUTES):

🔧 METHOD 1: WORDPRESS USERS (EASIEST - 2 MINUTES)
1. Go to Plugins → Add New
2. Search for "Security Headers" or "Wordfence"
3. Install and activate the plugin
4. Go to plugin settings → Security Headers
5. Enable "X-Frame-Options"
6. Choose "DENY" (recommended - blocks all embedding)
7. Save settings - you're protected!

🔧 METHOD 2: SHARED HOSTING (.htaccess - 3 MINUTES)
1. Login to your hosting control panel (cPanel, etc.)
2. Open "File Manager"
3. Go to your website's main folder (public_html)
4. Find or create file named ".htaccess"
5. Add this single line: Header always set X-Frame-Options "DENY"
6. Save file - protection activated!

🔧 METHOD 3: CLOUD/VPS HOSTING (ADVANCED - 5 MINUTES)
1. Access your server configuration files
2. Add X-Frame-Options header (see code snippets below)
3. Restart web server
4. Test your website

⚠️ IMPORTANT: Choose Your Protection Level:
- DENY = Maximum security (blocks ALL embedding) - RECOMMENDED
- SAMEORIGIN = Allow your own site to embed pages (if needed)

✅ HOW TO TEST IF IT'S WORKING:
1. Go to any iframe testing website (search "iframe test tool")
2. Try to embed your website URL
3. If it says "Refused to display" or shows an error - SUCCESS!
4. Your website should still work normally for visitors

🔧 INSTANT VERIFICATION:
1. Visit securityheaders.com
2. Enter your website URL
3. Look for "X-Frame-Options" with a green checkmark
4. Run another Polaris Audit scan to confirm the fix""",
                "code_snippets": [
                    {
                        "title": "🚀 Shared Hosting (.htaccess) - Most Common",
                        "description": "Add this line to your .htaccess file for maximum protection",
                        "code": "# Prevent clickjacking attacks\nHeader always set X-Frame-Options \"DENY\"",
                        "language": "apache"
                    },
                    {
                        "title": "🌐 Allow Own Site Embedding (.htaccess)",
                        "description": "Use this if you need to embed your own pages within your site",
                        "code": "# Allow same-origin embedding only\nHeader always set X-Frame-Options \"SAMEORIGIN\"",
                        "language": "apache"
                    },
                    {
                        "title": "🖥️ Nginx Servers",
                        "description": "Add to your Nginx server configuration",
                        "code": "# Add to server block in nginx.conf\nadd_header X-Frame-Options \"DENY\" always;",
                        "language": "nginx"
                    },
                    {
                        "title": "⚙️ Node.js / Express Applications",
                        "description": "Add this middleware to your Express app",
                        "code": "// Prevent clickjacking in Express.js\napp.use((req, res, next) => {\n  res.setHeader('X-Frame-Options', 'DENY');\n  next();\n});",
                        "language": "javascript"
                    },
                    {
                        "title": "🐘 PHP Applications",
                        "description": "Add to the top of your PHP files or in a common header file",
                        "code": "<?php\n// Prevent clickjacking attacks\nheader('X-Frame-Options: DENY');\n?>",
                        "language": "php"
                    }
                ],
                "testing_steps": [
                    {
                        "step": "1. Apply the Protection",
                        "action": "Add the X-Frame-Options header using one of the methods above",
                        "expected": "File should be saved without errors"
                    },
                    {
                        "step": "2. Check Your Website Works",
                        "action": "Visit your website normally in a browser",
                        "expected": "Everything should look and work exactly as before"
                    },
                    {
                        "step": "3. Test the Header is Present",
                        "action": "Press F12 → Network tab → Refresh page → Click your site's request → Look for 'X-Frame-Options' in Response Headers",
                        "expected": "Should show 'X-Frame-Options: DENY' or 'X-Frame-Options: SAMEORIGIN'"
                    },
                    {
                        "step": "4. Test Clickjacking Protection",
                        "action": "Go to any 'iframe test' website (Google 'iframe test tool') and try to embed your website URL",
                        "expected": "Should show 'Refused to display' or 'X-Frame-Options denied' error - this means you're protected!"
                    },
                    {
                        "step": "5. Verify with Security Tools",
                        "action": "Visit securityheaders.com and scan your website",
                        "expected": "Should show X-Frame-Options with a green grade"
                    },
                    {
                        "step": "6. Confirm Fix",
                        "action": "Run another Polaris Audit scan on your website",
                        "expected": "X-Frame-Options issue should be marked as resolved"
                    }
                ]
            },
            "x-content-type-options": {
                "title": "Missing X-Content-Type-Options Header (MIME Sniffing Protection)",
                "description": "Your website is missing protection against MIME type confusion attacks. This security header prevents browsers from 'guessing' what type of files you're serving, which could lead to security vulnerabilities.",
                "expected_values": ["nosniff"],
                "validation": self._validate_content_type_options,
                "priority": "should_fix",
                "fix_time": 5,
                "difficulty": {"level": "easy", "description": "Simple server header configuration"},
                "impact": "Without this protection, malicious users could upload files that browsers interpret differently than intended (e.g., a text file that gets executed as JavaScript), potentially leading to code execution attacks or data theft.",
                "fix_instructions": """WHAT IS X-CONTENT-TYPE-OPTIONS?

Think of it like a strict librarian: When you tell browsers 'this is a PDF file,' this header makes sure they treat it as EXACTLY that - no guessing, no assumptions. Without it, browsers might say 'this looks like JavaScript to me' even when you said it's a text file, which creates security holes.

REAL-WORLD EXAMPLE:
- Attacker uploads 'harmless.txt' containing malicious JavaScript
- Without X-Content-Type-Options: Browser might execute it as code
- With X-Content-Type-Options: Browser treats it strictly as text (safe)

STEP-BY-STEP IMPLEMENTATION GUIDE:

🔧 METHOD 1: WORDPRESS (EASIEST - 2 MINUTES)
1. Install 'Security Headers' plugin from your WordPress admin
2. Go to Settings → Security Headers
3. Find 'X-Content-Type-Options' section
4. Set it to 'nosniff'
5. Save changes
✅ Done! The plugin automatically adds the security header.

🔧 METHOD 2: SHARED HOSTING (.HTACCESS - 5 MINUTES)
1. Access your hosting control panel (cPanel, DirectAdmin, etc.)
2. Open File Manager
3. Navigate to your website's root folder (usually 'public_html' or 'www')
4. Find the '.htaccess' file (or create it if it doesn't exist)
5. Add this exact line at the top:

   Header always set X-Content-Type-Options "nosniff"

6. Save the file
✅ The header will now be sent with every response from your server.

🔧 METHOD 3: DJANGO/PYTHON APPLICATIONS
If you're using Django, add this to your middleware or views:

   response['X-Content-Type-Options'] = 'nosniff'

Or in your Django settings middleware, ensure you have proper security middleware configured.

🔧 METHOD 4: OTHER PLATFORMS
- Node.js: Use helmet.js middleware
- ASP.NET: Add to web.config or use code
- PHP: Use header() function in your scripts

TESTING YOUR IMPLEMENTATION:

1. 🧪 QUICK TEST (Browser):
   - Open your website
   - Right-click → Inspect → Network tab
   - Refresh the page
   - Click on any request to your domain
   - Look for 'X-Content-Type-Options: nosniff' in Response Headers

2. 🧪 COMPREHENSIVE TEST:
   - Visit https://securityheaders.com
   - Enter your website URL
   - Look for 'X-Content-Type-Options' in the results
   - Should show green checkmark with 'nosniff' value

3. 🧪 DEVELOPER TEST:
   Use curl command: curl -I https://yourwebsite.com
   Look for: X-Content-Type-Options: nosniff

TROUBLESHOOTING COMMON ISSUES:

❌ "Header not showing up"
→ Clear your browser cache and try again
→ Make sure you added the header to the correct .htaccess file
→ Contact your hosting provider if you can't modify headers

❌ "Website breaks after adding header"
→ This is very rare - the header only affects MIME type detection
→ If images/files stop loading, check your server's MIME type configuration
→ Remove the header temporarily and contact support

❌ "Security scanner still shows issue"
→ Wait 24-48 hours for DNS/cache propagation
→ Test with multiple online tools to confirm
→ Ensure the header is added to ALL pages, not just the homepage

WHY THIS MATTERS:
This protection prevents a class of attacks called 'MIME confusion' or 'content sniffing attacks.' It's like putting a lock on your file types - ensuring browsers can't be tricked into treating your innocent files as dangerous code.""",
                "code_snippets": [
                    {
                        "title": "Apache (.htaccess) - Add to root folder",
                        "code": "# Add X-Content-Type-Options header for MIME sniffing protection\nHeader always set X-Content-Type-Options \"nosniff\"",
                        "language": "apache"
                    },
                    {
                        "title": "Nginx (server block) - Add to nginx.conf",
                        "code": "# Prevent MIME type sniffing\nadd_header X-Content-Type-Options \"nosniff\" always;",
                        "language": "nginx"
                    },
                    {
                        "title": "Django Middleware - Add to views/middleware",
                        "code": "# In your Django view or middleware\nresponse['X-Content-Type-Options'] = 'nosniff'\n\n# Or in settings.py middleware configuration\n'django.middleware.security.SecurityMiddleware',",
                        "language": "python"
                    },
                    {
                        "title": "PHP - Add to your main PHP files",
                        "code": "<?php\n// Add MIME sniffing protection\nheader('X-Content-Type-Options: nosniff');\n?>",
                        "language": "php"
                    },
                    {
                        "title": "Node.js with Express - Using helmet middleware",
                        "code": "const helmet = require('helmet');\n\n// Enable nosniff protection\napp.use(helmet.noSniff());",
                        "language": "javascript"
                    }
                ],
                "testing_steps": [
                    "Implement the header using one of the code snippets above",
                    "Clear your browser cache completely",
                    "Visit your website and verify all content loads correctly",
                    "Open browser Developer Tools (F12) → Network tab",
                    "Refresh the page and check Response Headers for 'X-Content-Type-Options: nosniff'",
                    "Test with online scanner: https://securityheaders.com",
                    "Run another Polaris Audit scan to confirm the issue is resolved"
                ],
                "troubleshooting": {
                    "common_issues": [
                        {
                            "problem": "Header not appearing in tests",
                            "solution": "Ensure you've added the header to the correct configuration file and restart your web server"
                        },
                        {
                            "problem": "Files not loading after implementing",
                            "solution": "This is extremely rare. Check your server's MIME type configuration and ensure proper Content-Type headers are set"
                        },
                        {
                            "problem": "Security scanner still shows the issue",
                            "solution": "Wait 24-48 hours for cache propagation. Test multiple pages, not just the homepage"
                        }
                    ],
                    "verification_commands": [
                        "curl -I https://yourwebsite.com | grep -i x-content-type",
                        "Online test: securityheaders.com",
                        "Browser DevTools: Network tab → Response Headers"
                    ]
                }
            },
            "x-xss-protection": {
                "title": "Missing X-XSS-Protection Header",
                "description": "Your website doesn't enable the browser's built-in protection against malicious script injection",
                "expected_values": ["1", "1; mode=block"],
                "validation": self._validate_xss_protection,
                "priority": "nice_to_have",
                "fix_time": 5,
                "difficulty": {"level": "easy", "description": "Quick plugin configuration"},
                "impact": "Visitors using older browsers have less protection against malicious scripts that could steal their data",
                "fix_instructions": """STEP-BY-STEP GUIDE TO ADD X-XSS-PROTECTION HEADER:

1. FOR WORDPRESS USERS (Easiest):
   - Install "Security Headers" or "Wordfence" plugin
   - Go to plugin settings
   - Enable "X-XSS-Protection" or "Browser XSS Protection"
   - Save settings

2. FOR SHARED HOSTING (.htaccess method):
   - Log into your hosting control panel
   - Go to File Manager
   - Navigate to your website's root folder (usually public_html)
   - Open or create .htaccess file
   - Add this line:
     Header always set X-XSS-Protection "1; mode=block"
   - Save the file

3. FOR ADVANCED USERS:
   - Apache: Add to .htaccess or httpd.conf
   - Nginx: Add to server block
   - Use code snippets below

4. TEST YOUR CHANGES:
   - Visit your website to make sure everything still works
   - This protection works automatically in the background

5. VERIFY IT'S WORKING:
   - Use securityheaders.com to check
   - Run another Polaris Audit scan

NOTE: This protection mainly helps users with older browsers. Modern browsers have built-in protection, but this adds an extra layer of security.""",
                "code_snippets": [
                    {
                        "title": "Apache (.htaccess)",
                        "code": "Header always set X-XSS-Protection \"1; mode=block\"",
                        "language": "apache"
                    },
                    {
                        "title": "Nginx (nginx.conf)",
                        "code": "add_header X-XSS-Protection \"1; mode=block\" always;",
                        "language": "nginx"
                    },
                    {
                        "title": "PHP (header function)",
                        "code": "header('X-XSS-Protection: 1; mode=block');",
                        "language": "php"
                    }
                ],
                "testing_steps": [
                    "Add the header to your server configuration",
                    "Visit your website to ensure everything still works",
                    "Test with older browsers if possible",
                    "Use securityheaders.com to verify the header is present"
                ],
                "troubleshooting": "This header is mainly for older browsers. Modern browsers have built-in XSS protection, but this provides an extra layer of security."
            },
            "referrer-policy": {
                "title": "Missing Referrer-Policy Header",
                "description": "Your website doesn't control what information is shared when visitors click links to other sites",
                "expected_values": ["strict-origin-when-cross-origin", "no-referrer", "strict-origin"],
                "validation": self._validate_referrer_policy,
                "priority": "nice_to_have",
                "fix_time": 10,
                "difficulty": {"level": "easy", "description": "Basic privacy header setup"},
                "impact": "When visitors click links to other websites, those sites might receive sensitive information about your pages",
                "fix_instructions": """STEP-BY-STEP GUIDE TO ADD REFERRER-POLICY HEADER:

1. FOR WORDPRESS USERS (Easiest):
   - Install "Security Headers" or "Wordfence" plugin
   - Go to plugin settings
   - Enable "Referrer Policy" or "Privacy Protection"
   - Choose "strict-origin-when-cross-origin" (recommended)
   - Save settings

2. FOR SHARED HOSTING (.htaccess method):
   - Log into your hosting control panel
   - Go to File Manager
   - Navigate to your website's root folder (usually public_html)
   - Open or create .htaccess file
   - Add this line:
     Header always set Referrer-Policy "strict-origin-when-cross-origin"
   - Save the file

3. FOR ADVANCED USERS:
   - Apache: Add to .htaccess or httpd.conf
   - Nginx: Add to server block
   - Use code snippets below

4. TEST YOUR CHANGES:
   - Visit your website to make sure everything still works
   - This protection works automatically in the background

5. VERIFY IT'S WORKING:
   - Use securityheaders.com to check
   - Run another Polaris Audit scan

WHAT THIS DOES: When visitors click links to other websites, this prevents those sites from seeing the full URL of your page, protecting your visitors' privacy.""",
                "code_snippets": [
                    {
                        "title": "Apache (.htaccess)",
                        "code": "Header always set Referrer-Policy \"strict-origin-when-cross-origin\"",
                        "language": "apache"
                    },
                    {
                        "title": "Nginx (nginx.conf)",
                        "code": "add_header Referrer-Policy \"strict-origin-when-cross-origin\" always;",
                        "language": "nginx"
                    },
                    {
                        "title": "PHP (header function)",
                        "code": "header('Referrer-Policy: strict-origin-when-cross-origin');",
                        "language": "php"
                    },
                    {
                        "title": "HTML Meta Tag (alternative)",
                        "code": "<meta name=\"referrer\" content=\"strict-origin-when-cross-origin\">",
                        "language": "html"
                    }
                ],
                "testing_steps": [
                    "Add the header to your server configuration",
                    "Visit your website to ensure everything still works",
                    "Test by clicking external links and checking what referrer information is sent",
                    "Use securityheaders.com to verify the header is present"
                ],
                "troubleshooting": "This header works automatically in the background. Test by clicking external links and checking browser developer tools to see what referrer information is sent."
            },
            "permissions-policy": {
                "title": "Missing Permissions Policy Header (Feature Access Control)",
                "description": "Your website lacks controls over browser features like camera, microphone, geolocation, and other device capabilities. This security header prevents malicious scripts from secretly accessing sensitive device features without user permission.",
                "expected_values": ["geolocation", "camera", "microphone", "fullscreen", "payment"],
                "validation": self._validate_permissions_policy,
                "priority": "nice_to_have",
                "fix_time": 15,
                "difficulty": {"level": "medium", "description": "Requires understanding of browser features"},
                "impact": "Without this protection, malicious third-party scripts could potentially access device features like camera, microphone, or location without explicit user consent, creating privacy and security risks.",
                "fix_instructions": """WHAT IS PERMISSIONS POLICY?

Think of it like a security guard at a building: The Permissions Policy header tells browsers exactly which device features your website is allowed to use. It's like having a checklist that says "This website can use the camera: NO, microphone: NO, location: NO" - protecting users from unwanted access.

REAL-WORLD EXAMPLE:
- **Without Permissions Policy**: A malicious ad script could secretly access your camera
- **With Permissions Policy**: Browser blocks unauthorized access, user stays protected
- **Result**: Users feel safer, compliance with privacy regulations

WHY THIS MATTERS FOR YOUR BUSINESS:
- **Privacy Compliance**: Helps meet GDPR, CCPA, and other privacy regulations
- **User Trust**: Shows commitment to protecting user privacy and security
- **Security Defense**: Prevents supply chain attacks through third-party scripts
- **Performance**: Can improve site speed by blocking unnecessary feature requests

STEP-BY-STEP IMPLEMENTATION GUIDE:

🔒 METHOD 1: BASIC PROTECTION (RECOMMENDED - 5 MINUTES)

**WordPress Users**:
1. Install "Security Headers" or "Really Simple SSL" plugin
2. Go to Security Settings → Headers
3. Find "Permissions Policy" section
4. Enable these basic restrictions:
   - Geolocation: Disabled
   - Camera: Disabled
   - Microphone: Disabled
   - Payment: Self only
5. Save settings
✅ Your site now blocks unauthorized feature access

**Manual Implementation**:
Add this to your server configuration:
```
Permissions-Policy: geolocation=(), camera=(), microphone=(), payment=(self)
```

🔒 METHOD 2: ADVANCED CONFIGURATION (10-15 MINUTES)

**Full Feature Control**:
```
Permissions-Policy:
  geolocation=(),
  camera=(),
  microphone=(),
  fullscreen=(self),
  payment=(self),
  usb=(),
  magnetometer=(),
  accelerometer=(),
  gyroscope=(),
  bluetooth=(),
  ambient-light-sensor=(),
  autoplay=(self),
  encrypted-media=(self),
  picture-in-picture=(self)
```

**Explanation of Common Directives**:
- `geolocation=()` → Block all location access
- `camera=()` → Block all camera access
- `microphone=()` → Block all microphone access
- `payment=(self)` → Only your domain can use payment APIs
- `fullscreen=(self)` → Only your domain can use fullscreen
- `autoplay=(self)` → Control video autoplay policies

🔒 METHOD 3: PLATFORM-SPECIFIC IMPLEMENTATION

**Django (Your Platform)**:
```python
# In your middleware or views
response['Permissions-Policy'] = 'geolocation=(), camera=(), microphone=(), fullscreen=(self)'

# Or in Django settings middleware
'django.middleware.security.SecurityMiddleware',
```

**Apache (.htaccess)**:
```apache
# Add comprehensive permissions policy
Header always set Permissions-Policy "geolocation=(), camera=(), microphone=(), payment=(self), fullscreen=(self)"
```

**Nginx**:
```nginx
# Restrict browser features
add_header Permissions-Policy "geolocation=(), camera=(), microphone=(), payment=(self)" always;
```

**Node.js with Express**:
```javascript
app.use((req, res, next) => {
  res.setHeader('Permissions-Policy', 'geolocation=(), camera=(), microphone=(), payment=(self)');
  next();
});
```

TESTING YOUR IMPLEMENTATION:

1. 🧪 **BROWSER TEST**:
   - Open your website
   - Press F12 → Console tab
   - Try: `navigator.geolocation.getCurrentPosition()`
   - Should see: "Permission denied" or similar error

2. 🧪 **HEADER VERIFICATION**:
   - Right-click → Inspect → Network tab
   - Refresh page, click on your domain request
   - Look for "Permissions-Policy" in Response Headers

3. 🧪 **ONLINE TOOLS**:
   - Visit https://securityheaders.com
   - Enter your website URL
   - Look for "Permissions-Policy" in results
   - Should show green checkmark

4. 🧪 **DEVELOPER TEST**:
   ```bash
   curl -I https://yourwebsite.com | grep -i permissions-policy
   ```

TROUBLESHOOTING COMMON ISSUES:

❌ **"Feature still works after restriction"**
→ Some features might be cached by browser
→ Clear browser cache and test in incognito mode
→ Verify header is actually present in response

❌ **"Website functionality breaks"**
→ You might have blocked a feature your site needs
→ Use `(self)` instead of `()` for features you need
→ Test thoroughly before applying to production

❌ **"Payment/Maps not working"**
→ Add your domain to allowed list: `payment=(self "yoursite.com")`
→ For maps: `geolocation=(self "maps.googleapis.com")`
→ Check third-party integration documentation

❌ **"Header not showing up"**
→ Ensure you're testing the correct domain
→ Some development environments might cache headers
→ Contact hosting provider if you can't modify headers

COMMON PERMISSION POLICY CONFIGURATIONS:

**Blog/Content Sites**:
```
Permissions-Policy: geolocation=(), camera=(), microphone=(), payment=()
```

**E-commerce Sites**:
```
Permissions-Policy: geolocation=(), camera=(), microphone=(), payment=(self), fullscreen=(self)
```

**Media/Entertainment Sites**:
```
Permissions-Policy: geolocation=(), camera=(), microphone=(), fullscreen=(self), autoplay=(self), picture-in-picture=(self)
```

**Business/Corporate Sites**:
```
Permissions-Policy: geolocation=(), camera=(), microphone=(), payment=(), usb=(), bluetooth=()
```

ADVANCED SECURITY CONSIDERATIONS:

1. **Third-Party Integrations**:
   - Review all embedded widgets and services
   - Only allow necessary features for trusted domains
   - Regularly audit and update permissions

2. **Mobile Considerations**:
   - Mobile browsers have different permission models
   - Test thoroughly on iOS Safari and Android Chrome
   - Consider progressive enhancement approaches

3. **Compliance Benefits**:
   - Demonstrates privacy-by-design principles
   - Helps with GDPR Article 25 (Data Protection by Design)
   - Shows proactive security measures to auditors

WHY THIS PROTECTS YOUR USERS:
This header acts like a digital bouncer, checking IDs and keeping unwanted guests (malicious scripts) from accessing your users' private information. It's especially important in today's world where privacy breaches can destroy trust and cost businesses millions in fines and lost customers.""",
                "code_snippets": [
                    {
                        "title": "Basic protection (recommended for most sites)",
                        "code": "# Block common privacy-invasive features\nPermissions-Policy: geolocation=(), camera=(), microphone=(), payment=()",
                        "language": "http"
                    },
                    {
                        "title": "E-commerce site configuration",
                        "code": "# Allow payment features for your domain only\nPermissions-Policy: geolocation=(), camera=(), microphone=(), payment=(self), fullscreen=(self)",
                        "language": "http"
                    },
                    {
                        "title": "Django middleware implementation",
                        "code": "# In your Django middleware or views\ndef process_response(self, request, response):\n    response['Permissions-Policy'] = 'geolocation=(), camera=(), microphone=(), fullscreen=(self)'\n    return response",
                        "language": "python"
                    },
                    {
                        "title": "Apache .htaccess configuration",
                        "code": "# Add to your .htaccess file\nHeader always set Permissions-Policy \"geolocation=(), camera=(), microphone=(), payment=(self)\"",
                        "language": "apache"
                    },
                    {
                        "title": "Nginx server block configuration",
                        "code": "# Add to your nginx server block\nadd_header Permissions-Policy \"geolocation=(), camera=(), microphone=(), payment=(self)\" always;",
                        "language": "nginx"
                    },
                    {
                        "title": "Comprehensive policy for security-focused sites",
                        "code": "# Maximum protection - blocks most device features\nPermissions-Policy: geolocation=(), camera=(), microphone=(), usb=(), bluetooth=(), accelerometer=(), gyroscope=(), magnetometer=(), ambient-light-sensor=(), payment=(), fullscreen=()",
                        "language": "http"
                    }
                ],
                "testing_steps": [
                    "Implement the Permissions-Policy header using one of the code snippets above",
                    "Clear your browser cache and restart your browser",
                    "Visit your website and open browser Developer Tools (F12)",
                    "Go to Network tab, refresh the page, and check Response Headers for 'Permissions-Policy'",
                    "Test browser feature blocking: In Console tab, try 'navigator.geolocation.getCurrentPosition()' - should be blocked",
                    "Test with online scanner: https://securityheaders.com to verify header presence",
                    "Run another Polaris Audit scan to confirm the issue is resolved"
                ],
                "troubleshooting": {
                    "common_issues": [
                        {
                            "problem": "Website features stop working after implementation",
                            "solution": "Review which features your site actually needs and use '(self)' instead of '()' for required features"
                        },
                        {
                            "problem": "Third-party integrations break (maps, payments, etc.)",
                            "solution": "Add specific domains to allowlist: 'geolocation=(self \"maps.googleapis.com\")' or 'payment=(self \"checkout.stripe.com\")'"
                        },
                        {
                            "problem": "Header not appearing in tests",
                            "solution": "Ensure server configuration is correct and restart web server. Test with curl command to verify header delivery"
                        },
                        {
                            "problem": "Mobile apps or embedded content not working",
                            "solution": "Consider using more permissive policies for specific features your integrations require"
                        }
                    ],
                    "verification_commands": [
                        "curl -I https://yourwebsite.com | grep -i permissions-policy",
                        "Online test: securityheaders.com",
                        "Browser DevTools: Network tab → Response Headers → Permissions-Policy"
                    ]
                }
            }
        }

    def analyze_security_headers(self, response: Response, result: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze all security headers comprehensively."""
        try:
            headers = {k.lower(): v for k, v in response.headers.items()}
            analysis_results = {}
            missing_headers = []
            invalid_headers = []
            
            # Check each security header
            for header_name, header_config in self.security_headers.items():
                header_present = header_name in headers
                header_value = headers.get(header_name, "")
                
                # Validate header if present
                is_valid = False
                validation_message = ""
                if header_present:
                    is_valid, validation_message = header_config["validation"](header_value)
                
                # Store analysis results
                analysis_results[header_name] = {
                    "present": header_present,
                    "value": header_value,
                    "valid": is_valid,
                    "validation_message": validation_message,
                    "config": header_config
                }
                
                # Track missing and invalid headers
                if not header_present:
                    missing_headers.append(header_name)
                elif not is_valid:
                    invalid_headers.append(header_name)
            
            return {
                "headers_analysis": analysis_results,
                "missing_headers": missing_headers,
                "invalid_headers": invalid_headers,
                "total_headers_checked": len(self.security_headers),
                "headers_present": len(self.security_headers) - len(missing_headers),
                "headers_valid": len(self.security_headers) - len(missing_headers) - len(invalid_headers),
                "security_score_impact": self._calculate_header_score_impact(missing_headers, invalid_headers)
            }
            
        except Exception as e:
            return {
                "error": f"Error analyzing security headers: {str(e)}",
                "headers_analysis": {},
                "missing_headers": [],
                "invalid_headers": []
            }

    def _validate_hsts(self, value: str) -> Tuple[bool, str]:
        """Validate HSTS header value."""
        if not value:
            return False, "Empty HSTS header"
        
        value_lower = value.lower()
        if "max-age=" not in value_lower:
            return False, "Missing max-age directive"
        
        # Check for reasonable max-age value
        try:
            if "max-age=" in value_lower:
                max_age_part = value_lower.split("max-age=")[1].split(";")[0]
                max_age = int(max_age_part)
                if max_age < 300:  # Less than 5 minutes
                    return False, f"Max-age too low: {max_age} seconds"
                if max_age > 31536000:  # More than 1 year
                    return False, f"Max-age too high: {max_age} seconds"
        except (ValueError, IndexError):
            return False, "Invalid max-age value"
        
        return True, "Valid HSTS header"

    def _validate_csp(self, value: str) -> Tuple[bool, str]:
        """Validate Content Security Policy header."""
        if not value:
            return False, "Empty CSP header"
        
        # Basic CSP validation - check for common directives
        value_lower = value.lower()
        if "default-src" in value_lower or "script-src" in value_lower:
            return True, "Valid CSP header"
        else:
            return False, "Missing essential CSP directives"

    def _validate_frame_options(self, value: str) -> Tuple[bool, str]:
        """Validate X-Frame-Options header."""
        if not value:
            return False, "Empty X-Frame-Options header"
        
        valid_values = ["DENY", "SAMEORIGIN"]
        if value.upper() in valid_values:
            return True, "Valid X-Frame-Options header"
        else:
            return False, f"Invalid value: {value}. Must be DENY or SAMEORIGIN"

    def _validate_content_type_options(self, value: str) -> Tuple[bool, str]:
        """Validate X-Content-Type-Options header."""
        if not value:
            return False, "Empty X-Content-Type-Options header"
        
        if value.lower() == "nosniff":
            return True, "Valid X-Content-Type-Options header"
        else:
            return False, f"Invalid value: {value}. Must be 'nosniff'"

    def _validate_xss_protection(self, value: str) -> Tuple[bool, str]:
        """Validate X-XSS-Protection header."""
        if not value:
            return False, "Empty X-XSS-Protection header"
        
        valid_values = ["0", "1", "1; mode=block"]
        if value in valid_values:
            return True, "Valid X-XSS-Protection header"
        else:
            return False, f"Invalid value: {value}. Must be 0, 1, or 1; mode=block"

    def _validate_referrer_policy(self, value: str) -> Tuple[bool, str]:
        """Validate Referrer-Policy header."""
        if not value:
            return False, "Empty Referrer-Policy header"
        
        valid_values = [
            "no-referrer", "no-referrer-when-downgrade", "origin", 
            "origin-when-cross-origin", "same-origin", "strict-origin",
            "strict-origin-when-cross-origin", "unsafe-url"
        ]
        
        if value.lower() in valid_values:
            return True, "Valid Referrer-Policy header"
        else:
            return False, f"Invalid value: {value}"

    def _validate_permissions_policy(self, value: str) -> Tuple[bool, str]:
        """Validate Permissions-Policy header."""
        if not value:
            return False, "Empty Permissions-Policy header"
        
        # Basic validation - check for common features
        value_lower = value.lower()
        if "geolocation" in value_lower or "camera" in value_lower or "microphone" in value_lower:
            return True, "Valid Permissions-Policy header"
        else:
            return False, "Missing essential feature restrictions"

    def _calculate_header_score_impact(self, missing_headers: List[str], invalid_headers: List[str]) -> Dict[str, int]:
        """Calculate how missing/invalid headers affect security score."""
        score_deduction = 0
        
        # Calculate deductions based on header priority
        for header_name in missing_headers:
            config = self.security_headers[header_name]
            if config["priority"] == "should_fix":
                score_deduction += 15
            elif config["priority"] == "nice_to_have":
                score_deduction += 5
        
        # Invalid headers get smaller deductions
        for header_name in invalid_headers:
            config = self.security_headers[header_name]
            if config["priority"] == "should_fix":
                score_deduction += 10
            elif config["priority"] == "nice_to_have":
                score_deduction += 3
        
        return {
            "score_deduction": score_deduction,
            "max_possible_score": 100,
            "headers_impact": f"Missing/invalid headers reduce security score by {score_deduction} points"
        }
