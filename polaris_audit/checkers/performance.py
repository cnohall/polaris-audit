"""
Performance Checker
Basic performance analysis for website optimization recommendations.
"""

import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from bs4 import BeautifulSoup
from requests import Response
from .base import BaseChecker

logger = logging.getLogger(__name__)


class PerformanceChecker(BaseChecker):
    """
    Basic performance checker focusing on essential optimization opportunities.
    """

    @property
    def name(self) -> str:
        return "performance"

    def check(self, response: Response, soup: Optional[BeautifulSoup], result: dict) -> None:
        """Perform basic performance checks."""
        if soup:
            # Core performance checks
            self._check_image_optimization(soup, result)
            self._check_caching_headers(response, result)
            self._check_compression(response, result)
            self._check_javascript_optimization(soup, result)
            self._check_css_optimization(soup, result)
            self._check_page_size(response, result)
            self._check_resource_loading(soup, result)
        else:
            self._set_default_values(result)
            
        # Score calculation is now handled by UnifiedScoringService
        # self._calculate_performance_score(result)
        logger.info(f"Performance checker completed: {len(result.get('business_issues', []))} issues found")

    def _set_default_values(self, result: dict) -> None:
        """Set default values when HTML parsing fails."""
        self.set_check_result(result, "performance_score", 0)
        result["performance_summary"] = "Unable to analyze performance - HTML parsing failed"

    def _check_image_optimization(self, soup: BeautifulSoup, result: dict) -> None:
        """Check for image optimization opportunities."""
        try:
            images = soup.find_all('img')
            total_images = len(images)
            unoptimized_images = []
            large_images = []
            
            for img in images:
                src = img.get('src', '')
                if not src:
                    continue
                
                # Check for common unoptimized formats
                if src.lower().endswith(('.png', '.jpg', '.jpeg')) and not any(
                    ext in src.lower() for ext in ['.webp', '.avif', 'minified', 'optimized']
                ):
                    unoptimized_images.append(src)
                
                # Check for large image files (basic heuristic)
                if any(keyword in src.lower() for keyword in ['large', 'big', 'huge', 'original']):
                    large_images.append(src)
            
            # Check for missing alt attributes (affects performance indirectly)
            images_without_alt = [img for img in images if not img.get('alt')]
            
            # Report issues
            if unoptimized_images:
                self.add_business_issue(
                    result,
                    f"Found {len(unoptimized_images)} images that could be optimized with modern formats (WebP/AVIF)",
                    "Slow loading images increase bounce rate and hurt SEO rankings",
                    "should_fix",
                    15,  # 15 minutes to fix
                    "easy",
                    "performance",
                    count=len(unoptimized_images),
                    examples=unoptimized_images[:3],  # Show first 3 examples
                    total_images=total_images
                )
            
            if large_images:
                self.add_business_issue(
                    result,
                    f"Found {len(large_images)} potentially large images that may slow loading",
                    "Large images cause slow page loads, increasing bounce rate and reducing conversions",
                    "nice_to_have",
                    10,  # 10 minutes to fix
                    "easy",
                    "performance",
                    count=len(large_images),
                    examples=large_images[:3]
                )
            
            if images_without_alt:
                self.add_business_issue(
                    result,
                    f"Found {len(images_without_alt)} images without alt attributes (affects accessibility and performance)",
                    "Missing alt attributes hurt SEO rankings and make site inaccessible to screen readers",
                    "should_fix",
                    5,  # 5 minutes to fix
                    "easy",
                    "performance",
                    count=len(images_without_alt),
                    total_images=total_images
                )
            
            # Set check results
            self.set_check_result(result, "total_images", total_images)
            self.set_check_result(result, "unoptimized_images", len(unoptimized_images))
            self.set_check_result(result, "large_images", len(large_images))
            self.set_check_result(result, "images_without_alt", len(images_without_alt))
            
        except Exception as e:
            logger.error(f"Error checking image optimization: {str(e)}")
            self.add_business_issue(result, f"Error checking image optimization: {str(e)}", "Error occurred during analysis", "should_fix", 5, "easy", "performance")

    def _check_caching_headers(self, response: Response, result: dict) -> None:
        """Check for caching headers."""
        try:
            headers = response.headers
            
            # Check for common caching headers
            cache_control = headers.get('Cache-Control', '')
            expires = headers.get('Expires', '')
            etag = headers.get('ETag', '')
            last_modified = headers.get('Last-Modified', '')
            
            caching_issues = []
            
            if not cache_control:
                caching_issues.append("Missing Cache-Control header")
            elif 'no-cache' in cache_control.lower() and 'max-age' not in cache_control.lower():
                caching_issues.append("Cache-Control set to no-cache without max-age")
            
            if not expires and not cache_control:
                caching_issues.append("No caching headers found")
            
            if not etag and not last_modified:
                caching_issues.append("No validation headers (ETag or Last-Modified)")
            
            # Check for static resource caching
            content_type = headers.get('Content-Type', '').lower()
            is_static = any(static_type in content_type for static_type in [
                'image/', 'text/css', 'application/javascript', 'font/'
            ])
            
            if is_static and not cache_control:
                caching_issues.append("Static resources missing Cache-Control header")
            
            # Report issues
            if caching_issues:
                self.add_business_issue(
                    result,
                    f"Found {len(caching_issues)} caching issues: {', '.join(caching_issues)}",
                    "Missing caching headers force users to re-download content, increasing load times and server costs",
                    "must_fix",
                    30,  # 30 minutes to fix
                    "medium",
                    "performance",
                    issues=caching_issues,
                    cache_control=cache_control,
                    expires=expires,
                    etag=bool(etag),
                    last_modified=bool(last_modified)
                )
            
            # Set check results
            self.set_check_result(result, "cache_control_present", bool(cache_control))
            self.set_check_result(result, "expires_present", bool(expires))
            self.set_check_result(result, "etag_present", bool(etag))
            self.set_check_result(result, "last_modified_present", bool(last_modified))
            self.set_check_result(result, "caching_issues_count", len(caching_issues))
            
        except Exception as e:
            logger.error(f"Error checking caching headers: {str(e)}")
            self.add_business_issue(result, f"Error checking caching headers: {str(e)}", "Error occurred during analysis", "should_fix", 5, "easy", "performance")

    def _check_compression(self, response: Response, result: dict) -> None:
        """Check for compression headers."""
        try:
            headers = response.headers
            content_encoding = headers.get('Content-Encoding', '').lower()
            content_length = headers.get('Content-Length', '0')
            
            compression_issues = []
            
            if not content_encoding:
                compression_issues.append("No compression detected (missing Content-Encoding header)")
            elif content_encoding not in ['gzip', 'deflate', 'br']:
                compression_issues.append(f"Uncommon compression method: {content_encoding}")
            
            # Check content length for potential compression benefit
            try:
                content_size = int(content_length)
                if content_size > 1024 and not content_encoding:  # > 1KB without compression
                    compression_issues.append("Large content without compression")
            except ValueError:
                pass
            
            # Report issues
            if compression_issues:
                self.add_business_issue(
                    result,
                    f"Found {len(compression_issues)} compression issues: {', '.join(compression_issues)}",
                    "Missing compression wastes bandwidth and slows page loads, especially on mobile connections",
                    "must_fix",
                    20,  # 20 minutes to fix
                    "medium",
                    "performance",
                    issues=compression_issues,
                    content_encoding=content_encoding,
                    content_length=content_length
                )
            
            # Set check results
            self.set_check_result(result, "compression_enabled", bool(content_encoding))
            self.set_check_result(result, "compression_method", content_encoding)
            self.set_check_result(result, "content_length", content_length)
            self.set_check_result(result, "compression_issues_count", len(compression_issues))
            
        except Exception as e:
            logger.error(f"Error checking compression: {str(e)}")
            self.add_business_issue(result, f"Error checking compression: {str(e)}", "Error occurred during analysis", "should_fix", 5, "easy", "performance")

    def _check_javascript_optimization(self, soup: BeautifulSoup, result: dict) -> None:
        """Check for JavaScript optimization opportunities."""
        try:
            scripts = soup.find_all('script')
            total_scripts = len(scripts)
            external_scripts = []
            inline_scripts = []
            unminified_scripts = []
            
            for script in scripts:
                src = script.get('src', '')
                script_content = script.string or ''
                
                if src:
                    external_scripts.append(src)
                    # Check for unminified external scripts
                    src_lower = src.lower()

                    # Check if script appears to be minified
                    is_minified = any([
                        # Common minification indicators
                        '.min.js' in src_lower,
                        'minified' in src_lower,
                        'compressed' in src_lower,
                        # Modern build tools often use hashes (likely minified)
                        bool(re.search(r'-[a-f0-9]{8,}\.js$', src_lower)),  # Long hash pattern (Vite)
                        bool(re.search(r'\.[a-f0-9]{6,}\.js$', src_lower)),  # Short hash pattern (Webpack)
                        # Common CDN patterns (usually minified)
                        any(cdn in src_lower for cdn in ['cdn.', 'cdnjs.', 'unpkg.', 'jsdelivr']),
                        # Production build patterns - assets folder with any hash
                        '/assets/' in src_lower and any(c in src_lower for c in 'abcdef0123456789'),
                        '/static/' in src_lower and any(c in src_lower for c in 'abcdef0123456789'),
                        # Build tool outputs (likely minified in production)
                        any(pattern in src_lower for pattern in ['dist/', 'build/', 'public/assets/']),
                        # Third-party libraries are usually pre-minified
                        any(lib in src_lower for lib in ['react', 'vue', 'angular', 'jquery', 'bootstrap', 'lodash']),
                        # Vite specific patterns
                        bool(re.search(r'index-[a-zA-Z0-9]{8,}\.js', src_lower)),  # Vite index file pattern
                        bool(re.search(r'vendor-[a-zA-Z0-9]{8,}\.js', src_lower)),  # Vite vendor file pattern
                        bool(re.search(r'chunk-[a-zA-Z0-9]{8,}\.js', src_lower)),   # Vite chunk pattern
                    ])

                    if not is_minified:
                        unminified_scripts.append(src)
                else:
                    inline_scripts.append(script)
            
            # Check for async/defer attributes
            scripts_without_async_defer = []
            for script in soup.find_all('script', src=True):
                # Check for async/defer attributes (they can be boolean attributes with empty values)
                has_async = script.get('async') is not None
                has_defer = script.get('defer') is not None
                if not (has_async or has_defer):
                    src = script.get('src', '')
                    script_name = src.split('/')[-1] if '/' in src else src
                    if src.startswith('http'):
                        # External script - show domain + file
                        from urllib.parse import urlparse
                        parsed = urlparse(src)
                        display_src = f"{parsed.netloc}/{script_name}"
                    else:
                        # Local script - show path
                        display_src = src

                    scripts_without_async_defer.append(f"<script src='{display_src}'> - blocks page rendering")
            
            # Report issues
            if unminified_scripts:
                self.add_business_issue(
                    result,
                    f"Found {len(unminified_scripts)} unminified JavaScript files that could be optimized",
                    "Unminified scripts increase file size by 30-50%, slowing page loads and hurting SEO",
                    "nice_to_have",
                    25,  # 25 minutes to fix
                    "medium",
                    "performance",
                    count=len(unminified_scripts),
                    examples=unminified_scripts[:3],
                    total_elements=len(external_scripts),
                    element_type="JavaScript files",
                    technical_details=f"Found {len(unminified_scripts)} JavaScript files that appear to be unminified. Minification removes whitespace, shortens variable names, and optimizes code structure to reduce file size significantly.",
                    fix_instructions="""WHAT IS JAVASCRIPT MINIFICATION?

Think of minification like packing for a trip: You remove all unnecessary items (whitespace, comments), fold clothes efficiently (shorten variable names), and organize everything compactly (optimize code structure). The result is the same functionality in a much smaller package.

REAL-WORLD IMPACT:
- **Unminified JavaScript**: 150KB file, 500ms download on 3G
- **Minified JavaScript**: 75KB file, 250ms download on 3G
- **Result**: 50% smaller files, 2x faster page loads, better user experience

WHY THIS MATTERS FOR YOUR BUSINESS:
- **Page Speed**: Google's Core Web Vitals include JavaScript loading speed
- **Mobile Users**: 70% of web traffic is mobile with slower connections
- **Conversions**: Every 100ms delay reduces conversions by 1%
- **SEO Rankings**: Page speed is a confirmed Google ranking factor
- **Bandwidth Costs**: Smaller files reduce CDN and hosting costs

STEP-BY-STEP JAVASCRIPT OPTIMIZATION GUIDE:

⚡ METHOD 1: MODERN BUILD TOOLS (RECOMMENDED - 10 MINUTES)

**Vite (Your Current Setup)**:
Your JavaScript should already be minified! Verify your configuration:

```javascript
// vite.config.js
export default defineConfig({
  build: {
    minify: 'terser', // or 'esbuild' for faster builds
    terserOptions: {
      compress: {
        drop_console: true,     // Remove console.logs
        drop_debugger: true,    // Remove debugger statements
        pure_funcs: ['console.log', 'console.info']
      },
      mangle: {
        safari10: true          // Support Safari 10
      },
      format: {
        comments: false         // Remove comments
      }
    },
    target: ['es2020', 'edge88', 'firefox78', 'chrome87']
  }
})
```

**Webpack/Create React App**:
```javascript
// webpack.config.js
const TerserPlugin = require('terser-webpack-plugin');

module.exports = {
  optimization: {
    minimize: true,
    minimizer: [
      new TerserPlugin({
        terserOptions: {
          compress: {
            drop_console: true,
            drop_debugger: true
          },
          mangle: true,
          format: {
            comments: false
          }
        }
      })
    ]
  }
};
```

⚡ METHOD 2: MANUAL JAVASCRIPT OPTIMIZATION (20 MINUTES)

**Using Online Tools**:
1. **JSCompress**: Copy/paste for small files
2. **UglifyJS**: `npm install -g uglify-js`
3. **Terser**: `npm install -g terser`

**Command Line Minification**:
```bash
# Using Terser (recommended)
terser input.js -o output.min.js -c -m

# Using UglifyJS
uglifyjs input.js -o output.min.js -c -m

# Batch process multiple files
find src -name "*.js" -exec terser {} -o {}.min.js -c -m \\;
```

**WordPress Minification**:
```php
// functions.php
function minify_js_files() {
  if (!is_admin()) {
    // Dequeue unminified files
    wp_dequeue_script('custom-script');

    // Enqueue minified versions
    wp_enqueue_script('custom-script-min',
      get_template_directory_uri() . '/js/custom.min.js'
    );
  }
}
add_action('wp_enqueue_scripts', 'minify_js_files');
```

⚡ METHOD 3: ADVANCED OPTIMIZATION TECHNIQUES

**Tree Shaking (Remove Unused Code)**:
```javascript
// webpack.config.js
module.exports = {
  mode: 'production',
  optimization: {
    usedExports: true,
    sideEffects: false
  }
};

// package.json
{
  "sideEffects": false
}
```

**Code Splitting**:
```javascript
// Dynamic imports for code splitting
const LazyComponent = lazy(() => import('./LazyComponent'));

// Webpack magic comments
const utils = import(
  /* webpackChunkName: "utils" */
  './utils'
);
```

**Module Federation**:
```javascript
// Share common dependencies across apps
new ModuleFederationPlugin({
  shared: {
    'react': { singleton: true },
    'react-dom': { singleton: true }
  }
})
```

TESTING YOUR JAVASCRIPT OPTIMIZATION:

1. **File Size Verification**:
   ```bash
   # Check file sizes before/after
   ls -la build/static/js/

   # Verify minification worked
   file build/static/js/*.js
   ```

2. **Performance Testing**:
   - **Lighthouse**: Check "Reduce unused JavaScript" metric
   - **WebPageTest**: Monitor total JavaScript payload
   - **Chrome DevTools**: Coverage tab shows unused code

3. **Functionality Testing**:
   ```javascript
   // Test critical functionality
   console.log('App initialized');

   // Check all features work
   // - Form submissions
   // - Interactive elements
   // - Dynamic content loading
   ```

4. **Source Map Verification**:
   ```javascript
   // Ensure debugging still works in development
   // vite.config.js
   build: {
     sourcemap: process.env.NODE_ENV === 'development'
   }
   ```

COMMON JAVASCRIPT OPTIMIZATION MISTAKES:

❌ **Over-Aggressive Minification**:
```javascript
// Wrong: Breaking code with unsafe optimizations
terser --compress unsafe=true --mangle properties
```

✅ **Safe Minification**:
```javascript
// Right: Conservative but reliable optimization
terser --compress --mangle --format comments=false
```

❌ **Not Testing After Minification**:
```javascript
// Wrong: Deploy without verification
npm run build && npm run deploy
```

✅ **Proper Testing Pipeline**:
```javascript
// Right: Test before deployment
npm run build && npm run test && npm run e2e
```

❌ **Minifying Already Minified Code**:
```html
<!-- Wrong: Double minification -->
<script src="jquery.min.js"></script> <!-- Already minified -->
```

✅ **Check Before Minifying**:
```javascript
// Right: Only minify unminified sources
const isMinified = filename.includes('.min.') ||
                  isFromCDN(filename);
```

ADVANCED OPTIMIZATION STRATEGIES:

1. **Bundle Analysis**:
   ```bash
   # Analyze bundle composition
   npx webpack-bundle-analyzer build/static/js/*.js

   # Vite bundle analyzer
   npx vite-bundle-analyzer
   ```

2. **Preloading Critical Scripts**:
   ```html
   <link rel="preload" href="critical.js" as="script">
   <link rel="prefetch" href="non-critical.js">
   ```

3. **Service Worker Caching**:
   ```javascript
   // Cache minified scripts aggressively
   workbox.routing.registerRoute(
     /\.js$/,
     new workbox.strategies.CacheFirst({
       cacheName: 'js-cache',
       plugins: [{
         cacheKeyWillBeUsed: async ({ request }) => {
           return `${request.url}?v=${APP_VERSION}`;
         }
       }]
     })
   );
   ```

BUSINESS IMPACT METRICS:
After JavaScript optimization, expect to see:
- **30-50% reduction in JavaScript file sizes**
- **20-30% faster page load times**
- **Improved Lighthouse performance scores** (typically +10-20 points)
- **Better Core Web Vitals** (FCP, LCP, TTI improvements)
- **Reduced bandwidth costs** (significant for high-traffic sites)

MONITORING AND MAINTENANCE:

1. **Automated Optimization**:
   ```yaml
   # GitHub Actions example
   - name: Build and optimize
     run: |
       npm run build
       npm run analyze-bundle
   ```

2. **Performance Budgets**:
   ```javascript
   // webpack.config.js
   module.exports = {
     performance: {
       maxAssetSize: 250000,      // 250KB max per file
       maxEntrypointSize: 400000  // 400KB max entry point
     }
   };
   ```

WHY THIS PROTECTS YOUR USERS:
Minified JavaScript means faster page loads, especially on mobile devices with slower processors and connections. Users get a responsive experience, and you avoid the frustration that leads to high bounce rates.""",
                    business_value="Significantly reduces file sizes, improves page load speed, and enhances user experience - critical for mobile performance",
                    recurring_check=True,
                    code_snippets=[
                        {
                            "title": "Vite JavaScript Minification Config",
                            "code": "// vite.config.js\nexport default defineConfig({\n  build: {\n    minify: 'terser',\n    terserOptions: {\n      compress: {\n        drop_console: true,\n        drop_debugger: true,\n        pure_funcs: ['console.log']\n      },\n      mangle: { safari10: true },\n      format: { comments: false }\n    }\n  }\n})",
                            "language": "javascript"
                        },
                        {
                            "title": "Command Line Minification",
                            "code": "# Install Terser globally\nnpm install -g terser\n\n# Minify single file\nterser input.js -o output.min.js -c -m\n\n# Batch minify all JS files\nfind src -name \"*.js\" -exec terser {} -o {}.min.js -c -m \\;",
                            "language": "bash"
                        },
                        {
                            "title": "Webpack Minification Setup",
                            "code": "const TerserPlugin = require('terser-webpack-plugin');\n\nmodule.exports = {\n  optimization: {\n    minimize: true,\n    minimizer: [\n      new TerserPlugin({\n        terserOptions: {\n          compress: {\n            drop_console: true,\n            drop_debugger: true\n          },\n          mangle: true,\n          format: { comments: false }\n        }\n      })\n    ]\n  }\n};",
                            "language": "javascript"
                        },
                        {
                            "title": "WordPress JavaScript Optimization",
                            "code": "// functions.php\nfunction optimize_js_files() {\n  if (!is_admin()) {\n    // Dequeue unminified files\n    wp_dequeue_script('custom-script');\n    \n    // Enqueue minified versions\n    wp_enqueue_script('custom-script-min', \n      get_template_directory_uri() . '/js/custom.min.js',\n      array(), '1.0', true\n    );\n  }\n}\nadd_action('wp_enqueue_scripts', 'optimize_js_files');",
                            "language": "php"
                        }
                    ],
                    total_external_scripts=len(external_scripts)
                )
            
            if len(inline_scripts) > 3:
                self.add_business_issue(
                    result,
                    f"Found {len(inline_scripts)} inline scripts (consider moving to external files)",
                    "Inline scripts block page rendering and prevent browser caching, slowing load times",
                    "nice_to_have",
                    20,  # 20 minutes to fix
                    "medium",
                    "performance",
                    count=len(inline_scripts),
                    total_scripts=total_scripts
                )
            
            if scripts_without_async_defer:
                self.add_business_issue(
                    result,
                    f"Found {len(scripts_without_async_defer)} scripts without async/defer attributes",
                    "Scripts without async/defer block page rendering, creating poor user experience and hurting Core Web Vitals scores",
                    "should_fix",
                    15,  # 15 minutes to fix
                    "easy",
                    "performance",
                    count=len(scripts_without_async_defer),
                    examples=scripts_without_async_defer,
                    total_elements=len(external_scripts),
                    element_type="scripts",
                    technical_details=f"These scripts block HTML parsing and delay page rendering. When browsers encounter a script without async/defer, they must stop parsing HTML, download the script, execute it, then continue parsing.",
                    fix_instructions="""WHAT ARE ASYNC/DEFER ATTRIBUTES?

Think of webpage loading like reading a book while occasionally checking your phone:
- **No async/defer**: You stop reading completely every time you check your phone (blocking)
- **defer**: You bookmark your page, check your phone, then return to where you left off (non-blocking, executed in order)
- **async**: You quickly glance at your phone while continuing to read (non-blocking, executed immediately)

REAL-WORLD IMPACT:
- **Without optimization**: 3.2 second page load time
- **With async/defer**: 1.8 second page load time (40% faster!)
- **SEO Benefit**: Google ranks faster-loading sites higher
- **User Experience**: Users are 32% more likely to stay on fast-loading pages

STEP-BY-STEP IMPLEMENTATION GUIDE:

🚀 METHOD 1: HTML TEMPLATE FIXES (MOST COMMON)

1. **Identify Your Script Type**:
   - Analytics scripts (Google Analytics, Facebook Pixel) → Use `async`
   - UI frameworks (React, Vue) → Use `defer`
   - Critical functionality scripts → Keep as-is (no async/defer)

2. **WordPress Users**:
   - Install "Async JavaScript" or "WP Rocket" plugin
   - Go to plugin settings
   - Enable "Defer JavaScript" for theme scripts
   - Enable "Async" for tracking scripts
   ✅ The plugin automatically optimizes your scripts

3. **Manual HTML Editing**:
   Edit your theme files or HTML templates:

   BEFORE (blocking):
   <script src="analytics.js"></script>
   <script src="main.js"></script>

   AFTER (optimized):
   <script src="analytics.js" async></script>
   <script src="main.js" defer></script>

🚀 METHOD 2: JAVASCRIPT FRAMEWORKS

**React/Next.js**:
```jsx
// In your component or _document.js
<Script
  src="analytics.js"
  strategy="afterInteractive" // Similar to async
/>
<Script
  src="main.js"
  strategy="beforeInteractive" // Similar to defer
/>
```

**Vue.js**:
```vue
<!-- In your template -->
<script src="analytics.js" async></script>
<script src="main.js" defer></script>
```

🚀 METHOD 3: SERVER-SIDE OPTIMIZATION

**Apache (.htaccess)**:
```apache
# Add defer to all JS files automatically
<FilesMatch "\\.js$">
    Header append Content-Security-Policy "script-src 'self' 'defer'"
</FilesMatch>
```

**Nginx**:
```nginx
# Optimize script loading
location ~* \\.js$ {
    add_header Cache-Control "public, max-age=31536000";
    add_header X-Content-Type-Options "nosniff";
}
```

TESTING YOUR IMPLEMENTATION:

1. 🧪 **QUICK TEST** (Browser DevTools):
   - Open your website
   - Press F12 → Network tab
   - Refresh the page
   - Look at the "Waterfall" view
   - Scripts with async/defer should not block other resources

2. 🧪 **PERFORMANCE TEST**:
   - Visit https://pagespeed.web.dev
   - Enter your website URL
   - Look for "Eliminate render-blocking resources"
   - Should show improvement in Core Web Vitals

3. 🧪 **DEVELOPER TEST**:
   - View page source (Ctrl+U)
   - Search for `<script`
   - Verify async/defer attributes are present

TROUBLESHOOTING COMMON ISSUES:

❌ **"Scripts break after adding async/defer"**
→ Some scripts depend on others loading first
→ Use `defer` instead of `async` for dependent scripts
→ Keep critical scripts without async/defer

❌ **"Analytics not tracking properly"**
→ Analytics scripts usually work fine with `async`
→ Check your analytics dashboard after 24 hours
→ Consider using Google Tag Manager for better control

❌ **"Page elements not working"**
→ Move scripts that manipulate DOM to before closing `</body>` tag
→ Use `defer` for scripts that need full DOM access
→ Test thoroughly on different devices/browsers

❌ **"Third-party scripts (Cloudflare, etc.)"**
→ Scripts injected by CDNs/proxies can't be directly controlled
→ Contact your hosting provider or CDN support
→ These usually have minimal performance impact

ADVANCED OPTIMIZATION TIPS:

1. **Script Prioritization**:
   - Critical scripts: No async/defer
   - Important UI scripts: `defer`
   - Analytics/tracking: `async`
   - Social media widgets: `async`

2. **Load Order Matters**:
   ```html
   <!-- Load in this order -->
   <script src="critical-framework.js"></script>           <!-- Critical -->
   <script src="ui-components.js" defer></script>          <!-- UI -->
   <script src="analytics.js" async></script>              <!-- Tracking -->
   ```

3. **Resource Hints**:
   ```html
   <!-- Preload critical scripts -->
   <link rel="preload" href="critical.js" as="script">

   <!-- Preconnect to external script domains -->
   <link rel="preconnect" href="https://www.google-analytics.com">
   ```

WHY THIS MATTERS FOR YOUR BUSINESS:
- **SEO Impact**: Google's Page Experience signals include loading speed
- **Conversion Rate**: Every 1-second delay reduces conversions by 7%
- **User Retention**: 53% of mobile users abandon sites that take >3 seconds
- **Revenue**: Amazon found that 100ms delay costs them 1% in sales""",
                    code_snippets=[
                        {
                            "title": "Basic async/defer implementation",
                            "code": "<!-- Analytics and tracking scripts -->\n<script src=\"analytics.js\" async></script>\n<script src=\"facebook-pixel.js\" async></script>\n\n<!-- UI and application scripts -->\n<script src=\"main.js\" defer></script>\n<script src=\"components.js\" defer></script>\n\n<!-- Critical scripts (keep as-is) -->\n<script src=\"critical-polyfills.js\"></script>",
                            "language": "html"
                        },
                        {
                            "title": "React/Next.js optimization",
                            "code": "import Script from 'next/script'\n\n// In your component\n<Script\n  src=\"https://www.google-analytics.com/analytics.js\"\n  strategy=\"afterInteractive\"\n/>\n<Script\n  src=\"/js/main.js\"\n  strategy=\"beforeInteractive\"\n/>",
                            "language": "jsx"
                        },
                        {
                            "title": "WordPress plugin configuration",
                            "code": "// Using Async JavaScript plugin\n// 1. Install 'Async JavaScript' plugin\n// 2. Go to Settings → Async JavaScript\n// 3. Enable these settings:\n\n✅ Defer render-blocking JS\n✅ Async non-render-blocking JS\n❌ Exclude jQuery (keep checked)\n✅ Apply to inline scripts\n\n// Save settings and test your site",
                            "language": "javascript"
                        },
                        {
                            "title": "Manual HTML template fix",
                            "code": "<!-- BEFORE: Blocking scripts -->\n<script src=\"/js/analytics.js\"></script>\n<script src=\"/js/main.js\"></script>\n<script src=\"/js/widgets.js\"></script>\n\n<!-- AFTER: Optimized scripts -->\n<script src=\"/js/analytics.js\" async></script>     <!-- Tracking -->\n<script src=\"/js/main.js\" defer></script>         <!-- Main app -->\n<script src=\"/js/widgets.js\" defer></script>      <!-- UI widgets -->",
                            "language": "html"
                        }
                    ]
                )
            
            # Set check results
            self.set_check_result(result, "total_scripts", total_scripts)
            self.set_check_result(result, "external_scripts", len(external_scripts))
            self.set_check_result(result, "inline_scripts", len(inline_scripts))
            self.set_check_result(result, "unminified_scripts", len(unminified_scripts))
            self.set_check_result(result, "scripts_without_async_defer", len(scripts_without_async_defer))
            
        except Exception as e:
            logger.error(f"Error checking JavaScript optimization: {str(e)}")
            self.add_business_issue(result, f"Error checking JavaScript optimization: {str(e)}", "Error occurred during analysis", "should_fix", 5, "easy", "performance")

    def _check_css_optimization(self, soup: BeautifulSoup, result: dict) -> None:
        """Check for CSS optimization opportunities."""
        try:
            # Find all stylesheets
            stylesheets = soup.find_all('link', rel='stylesheet')
            inline_styles = soup.find_all('style')
            
            total_stylesheets = len(stylesheets)
            unminified_css = []
            large_inline_styles = []
            
            for stylesheet in stylesheets:
                href = stylesheet.get('href', '')
                if not href:
                    continue

                href_lower = href.lower()

                # Check if CSS appears to be minified using comprehensive logic
                is_minified = any([
                    # Common minification indicators
                    '.min.css' in href_lower,
                    'minified' in href_lower,
                    'compressed' in href_lower,
                    # Modern build tools often use hashes (likely minified)
                    bool(re.search(r'-[a-f0-9]{8,}\.css$', href_lower)),  # Long hash pattern (Vite)
                    bool(re.search(r'\.[a-f0-9]{6,}\.css$', href_lower)),  # Short hash pattern (Webpack)
                    # Common CDN patterns (usually minified)
                    any(cdn in href_lower for cdn in ['cdn.', 'cdnjs.', 'unpkg.', 'jsdelivr', 'fonts.googleapis.com']),
                    # Production build patterns - assets folder with any hash
                    '/assets/' in href_lower and any(c in href_lower for c in 'abcdef0123456789'),
                    '/static/' in href_lower and any(c in href_lower for c in 'abcdef0123456789'),
                    # Build tool outputs (likely minified in production)
                    any(pattern in href_lower for pattern in ['dist/', 'build/', 'public/assets/']),
                    # Third-party libraries and frameworks are usually pre-minified
                    any(lib in href_lower for lib in ['bootstrap', 'tailwind', 'foundation', 'bulma', 'materialize']),
                    # Vite specific patterns for CSS
                    bool(re.search(r'index-[a-zA-Z0-9]{8,}\.css', href_lower)),  # Vite index CSS pattern
                    bool(re.search(r'components-[a-zA-Z0-9]{8,}\.css', href_lower)),  # Vite components pattern
                    bool(re.search(r'vendor-[a-zA-Z0-9]{8,}\.css', href_lower)),  # Vite vendor CSS pattern
                    bool(re.search(r'chunk-[a-zA-Z0-9]{8,}\.css', href_lower)),   # Vite chunk pattern
                    # Google Fonts and other external CSS services (pre-minified)
                    'fonts.gstatic.com' in href_lower,
                    'fonts.googleapis.com' in href_lower,
                ])

                if not is_minified:
                    unminified_css.append(href)
            
            for style in inline_styles:
                content = style.string or ''
                if len(content) > 1000:  # Large inline styles
                    large_inline_styles.append(len(content))
            
            # Check for unused CSS (basic heuristic)
            css_files_count = len(stylesheets)
            if css_files_count > 5:
                # Collect CSS file names for specific guidance
                css_file_names = []
                for stylesheet in stylesheets:
                    href = stylesheet.get('href', '')
                    if href:
                        # Clean up the href for display
                        if href.startswith('http'):
                            from urllib.parse import urlparse
                            parsed = urlparse(href)
                            css_file_names.append(f"{parsed.netloc}{parsed.path}")
                        else:
                            css_file_names.append(href)

                self.add_business_issue(
                    result,
                    f"Found {css_files_count} stylesheet files (consider consolidating or removing unused CSS)",
                    "Multiple CSS files create extra HTTP requests, slowing page load and increasing server load",
                    "nice_to_have",
                    30,  # 30 minutes to fix
                    "medium",
                    "performance",
                    count=css_files_count,
                    examples=css_file_names[:5],  # Show first 5 files
                    total_elements=css_files_count,
                    element_type="CSS files",
                    technical_details=f"Found {css_files_count} separate CSS files. Each file requires a separate HTTP request, which can slow page loading. Modern bundlers can combine these into fewer files for better performance.",
                    fix_instructions="""WHAT ARE MULTIPLE CSS FILES DOING TO YOUR SITE?

Think of CSS files like ingredients for a recipe: Having to fetch {css_files_count}+ different ingredients from different stores (servers) takes much longer than getting everything from one well-stocked store. Each CSS file requires a separate HTTP request, creating a waterfall effect that delays rendering.

REAL-WORLD IMPACT:
- **{css_files_count} CSS files**: {css_files_count} separate requests, potential 200-600ms delay
- **1 optimized CSS file**: 1 request, ~50-100ms delay
- **Result**: 70% faster initial page render, better Core Web Vitals scores

WHY THIS MATTERS FOR YOUR BUSINESS:
- **Page Speed**: Google uses page speed as a ranking factor
- **User Experience**: 53% of mobile users abandon sites that take >3 seconds to load
- **Conversions**: 1-second delay = 7% reduction in conversions
- **Bandwidth Costs**: Fewer requests reduce server load and CDN costs

STEP-BY-STEP CSS OPTIMIZATION GUIDE:

🎨 METHOD 1: MODERN BUILD TOOLS (RECOMMENDED - 15 MINUTES)

**Vite (Your Current Setup)**:
Your CSS is likely already being optimized! Check your production build:

```javascript
// vite.config.js
export default defineConfig({
  build: {
    cssCodeSplit: false, // Combine all CSS into one file
    rollupOptions: {
      output: {
        assetFileNames: 'assets/[name]-[hash].[ext]',
        // This combines CSS automatically
      }
    }
  }
})
```

**Webpack/Create React App**:
```javascript
// webpack.config.js
module.exports = {
  optimization: {
    splitChunks: {
      cacheGroups: {
        styles: {
          name: 'styles',
          type: 'css/mini-extract',
          chunks: 'all',
          enforce: true,
        },
      },
    },
  },
};
```

🎨 METHOD 2: MANUAL CSS CONSOLIDATION (30 MINUTES)

**Identify Critical vs Non-Critical CSS**:
1. **Critical CSS**: Above-the-fold styles (header, hero section)
2. **Non-Critical CSS**: Below-the-fold styles (footer, modals, etc.)

**Consolidation Strategy**:
```html
<!-- BEFORE: Multiple files -->
<link rel="stylesheet" href="normalize.css">
<link rel="stylesheet" href="fonts.css">
<link rel="stylesheet" href="header.css">
<link rel="stylesheet" href="main.css">
<link rel="stylesheet" href="footer.css">
<link rel="stylesheet" href="responsive.css">

<!-- AFTER: Optimized loading -->
<style>
/* Inline critical CSS here (above-the-fold only) */
.header { background: #333; color: white; }
.hero { min-height: 100vh; display: flex; align-items: center; }
</style>

<!-- Load non-critical CSS asynchronously -->
<link rel="preload" href="main-combined.css" as="style" onload="this.onload=null;this.rel='stylesheet'">
<noscript><link rel="stylesheet" href="main-combined.css"></noscript>
```

🎨 METHOD 3: WORDPRESS OPTIMIZATION (10 MINUTES)

**Using Plugins**:
- **WP Rocket**: Automatically combines CSS files
- **Autoptimize**: Concatenates and minifies CSS
- **W3 Total Cache**: Advanced CSS optimization

**Manual WordPress**:
```php
// functions.php
function combine_css_files() {
  if (!is_admin()) {
    // Dequeue individual CSS files
    wp_dequeue_style('theme-style');
    wp_dequeue_style('bootstrap');

    // Enqueue combined file
    wp_enqueue_style('combined-css', get_template_directory_uri() . '/css/combined.min.css');
  }
}
add_action('wp_enqueue_scripts', 'combine_css_files');
```

🎨 METHOD 4: ADVANCED OPTIMIZATION TECHNIQUES

**Critical CSS Extraction**:
```bash
# Using Critical (npm package)
npm install -g critical

# Extract critical CSS
critical src/index.html --base=src --inline --css=src/css/main.css --target=dist/index.html --width=1200 --height=900
```

**CSS Purging (Remove Unused Styles)**:
```javascript
// tailwind.config.js or postcss.config.js
module.exports = {
  content: ['./src/**/*.{html,js,jsx,ts,tsx}'],
  plugins: [
    require('@fullhuman/postcss-purgecss')({
      content: ['./src/**/*.html', './src/**/*.jsx'],
      defaultExtractor: content => content.match(/[\w-/:]+(?<!:)/g) || []
    })
  ]
}
```

TESTING YOUR CSS OPTIMIZATION:

1. **Performance Test**:
   - Before: Check Lighthouse performance score
   - After: Re-run Lighthouse (should see improved LCP)
   - Monitor "Eliminate render-blocking resources" metric

2. **File Count Verification**:
   ```bash
   # Check CSS files in production build
   find build/static/css -name "*.css" | wc -l
   ```

3. **Size Comparison**:
   ```bash
   # Before optimization
   ls -la src/css/*.css

   # After optimization
   ls -la build/static/css/*.css
   ```

4. **Visual Regression Testing**:
   - Check all pages still look correct
   - Test responsive behavior
   - Verify animations work properly

COMMON CSS OPTIMIZATION MISTAKES:

❌ **Combining ALL CSS Blindly**:
```css
/* Wrong: Including unused framework CSS */
@import 'bootstrap.css'; /* 150KB */
@import 'custom.css';    /* 5KB */
```

✅ **Smart CSS Loading**:
```html
<!-- Right: Only load what you need -->
<link rel="stylesheet" href="bootstrap-grid-only.css"> <!-- 20KB -->
<link rel="stylesheet" href="custom.css">               <!-- 5KB -->
```

❌ **No Critical CSS Strategy**:
```html
<!-- Wrong: All CSS blocks rendering -->
<link rel="stylesheet" href="large-file.css">
```

✅ **Critical CSS First**:
```html
<!-- Right: Critical inline, rest async -->
<style>/* Critical CSS here */</style>
<link rel="preload" href="non-critical.css" as="style" onload="this.rel='stylesheet'">
```

ADVANCED PERFORMANCE TIPS:

1. **CSS Containment**:
   ```css
   .sidebar { contain: layout style; }
   .article { contain: layout; }
   ```

2. **Efficient Selectors**:
   ```css
   /* Slow */
   .header .nav ul li a { }

   /* Fast */
   .nav-link { }
   ```

3. **CSS Grid/Flexbox Over Float**:
   Modern layout methods are more performant than legacy techniques.

BUSINESS IMPACT METRICS:
After CSS optimization, expect to see:
- **20-40% faster page load times**
- **15-25% improvement in Lighthouse performance score**
- **Reduced bandwidth usage** (typically 30-50% smaller CSS payload)
- **Better Core Web Vitals** (improved LCP and CLS scores)

WHY THIS PROTECTS YOUR USERS:
Fast-loading CSS means your site looks good immediately, preventing the "flash of unstyled content" that drives users away. It's especially crucial for mobile users on slower connections.""".replace('{css_files_count}', str(css_files_count)),
                    business_value="Reduces HTTP requests, improves page load speed, and enhances user experience - particularly important for mobile users",
                    recurring_check=True,
                    code_snippets=[
                        {
                            "title": "Critical CSS Inline Loading",
                            "code": "<head>\n  <!-- Inline critical CSS -->\n  <style>\n    /* Only above-the-fold styles here */\n    .header { background: #333; color: white; }\n    .hero { min-height: 100vh; }\n  </style>\n\n  <!-- Load non-critical CSS asynchronously -->\n  <link rel=\"preload\" href=\"main.css\" as=\"style\" onload=\"this.onload=null;this.rel='stylesheet'\">\n  <noscript><link rel=\"stylesheet\" href=\"main.css\"></noscript>\n</head>",
                            "language": "html"
                        },
                        {
                            "title": "Vite CSS Optimization Config",
                            "code": "// vite.config.js\nexport default defineConfig({\n  build: {\n    cssCodeSplit: false, // Combine all CSS\n    rollupOptions: {\n      output: {\n        assetFileNames: 'assets/[name]-[hash].[ext]'\n      }\n    },\n    cssMinify: true\n  }\n})",
                            "language": "javascript"
                        },
                        {
                            "title": "WordPress CSS Combination",
                            "code": "// functions.php\nfunction combine_css_files() {\n  if (!is_admin()) {\n    // Dequeue individual files\n    wp_dequeue_style('theme-style');\n    wp_dequeue_style('bootstrap');\n    \n    // Enqueue combined file\n    wp_enqueue_style('combined-css', \n      get_template_directory_uri() . '/css/combined.min.css'\n    );\n  }\n}\nadd_action('wp_enqueue_scripts', 'combine_css_files');",
                            "language": "php"
                        },
                        {
                            "title": "CSS Purging with PostCSS",
                            "code": "// postcss.config.js\nmodule.exports = {\n  plugins: [\n    require('@fullhuman/postcss-purgecss')({\n      content: ['./src/**/*.html', './src/**/*.jsx'],\n      defaultExtractor: content => \n        content.match(/[\\w-/:]+(?<!:)/g) || []\n    })\n  ]\n}",
                            "language": "javascript"
                        }
                    ],
                    total_stylesheets=total_stylesheets
                )
            
            if unminified_css:
                self.add_business_issue(
                    result,
                    f"Found {len(unminified_css)} unminified CSS files that could be optimized",
                    "Unminified CSS increases file size by 20-40%, slowing page loads and wasting bandwidth",
                    "nice_to_have",
                    20,  # 20 minutes to fix
                    "medium",
                    "performance",
                    count=len(unminified_css),
                    examples=unminified_css[:3],
                    total_stylesheets=total_stylesheets
                )
            
            if large_inline_styles:
                self.add_business_issue(
                    result,
                    f"Found {len(large_inline_styles)} large inline style blocks (consider moving to external files)",
                    "Large inline styles increase page size and prevent browser caching, slowing repeat visits",
                    "nice_to_have",
                    15,  # 15 minutes to fix
                    "easy",
                    "performance",
                    count=len(large_inline_styles),
                    total_inline_styles=len(inline_styles)
                )
            
            # Set check results
            self.set_check_result(result, "total_stylesheets", total_stylesheets)
            self.set_check_result(result, "unminified_css", len(unminified_css))
            self.set_check_result(result, "large_inline_styles", len(large_inline_styles))
            self.set_check_result(result, "inline_styles", len(inline_styles))
            
        except Exception as e:
            logger.error(f"Error checking CSS optimization: {str(e)}")
            self.add_business_issue(result, f"Error checking CSS optimization: {str(e)}", "Error occurred during analysis", "should_fix", 5, "easy", "performance")

    def _check_page_size(self, response: Response, result: dict) -> None:
        """Check page size and provide recommendations."""
        try:
            content_length = response.headers.get('Content-Length', '0')
            content_size = int(content_length) if content_length.isdigit() else 0
            
            # Convert to KB
            size_kb = content_size / 1024
            
            size_issues = []
            
            if size_kb > 1000:  # > 1MB
                size_issues.append("Page size is very large (>1MB)")
            elif size_kb > 500:  # > 500KB
                size_issues.append("Page size is large (>500KB)")
            elif size_kb > 200:  # > 200KB
                size_issues.append("Page size could be optimized (>200KB)")
            
            # Check for potential size optimization
            if content_size > 0:
                content_type = response.headers.get('Content-Type', '').lower()
                if 'text/html' in content_type and size_kb > 100:
                    size_issues.append("HTML page size could be reduced")
            
            if size_issues:
                self.add_business_issue(
                    result,
                    f"Page size optimization opportunities: {', '.join(size_issues)}",
                    "Large page size increases bounce rate, especially on mobile, and hurts SEO rankings",
                    "should_fix" if size_kb > 500 else "nice_to_have",
                    45 if size_kb > 500 else 20,  # More time for larger pages
                    "medium",
                    "performance",
                    issues=size_issues,
                    size_kb=round(size_kb, 2),
                    size_bytes=content_size
                )
            
            # Set check results
            self.set_check_result(result, "page_size_kb", round(size_kb, 2))
            self.set_check_result(result, "page_size_bytes", content_size)
            self.set_check_result(result, "size_issues_count", len(size_issues))
            
        except Exception as e:
            logger.error(f"Error checking page size: {str(e)}")
            self.add_business_issue(result, f"Error checking page size: {str(e)}", "Error occurred during analysis", "should_fix", 5, "easy", "performance")

    def _check_resource_loading(self, soup: BeautifulSoup, result: dict) -> None:
        """Check for resource loading optimization opportunities."""
        try:
            # Check for preload hints
            preload_links = soup.find_all('link', rel='preload')
            prefetch_links = soup.find_all('link', rel='prefetch')
            dns_prefetch_links = soup.find_all('link', rel='dns-prefetch')
            
            # Check for critical resources that could benefit from preloading
            critical_resources = []
            
            # Look for critical CSS
            stylesheets = soup.find_all('link', rel='stylesheet')
            if stylesheets and not preload_links:
                critical_resources.append("Critical CSS could be preloaded")
            
            # Look for critical JavaScript
            scripts = soup.find_all('script', src=True)
            if scripts and not preload_links:
                critical_resources.append("Critical JavaScript could be preloaded")
            
            # Check for images above the fold
            images = soup.find_all('img')
            above_fold_images = [img for img in images if img.get('src')]
            if above_fold_images and not preload_links:
                critical_resources.append("Above-the-fold images could be preloaded")
            
            # Report optimization opportunities
            if critical_resources:
                self.add_business_issue(
                    result,
                    f"Resource loading optimization opportunities: {', '.join(critical_resources)}",
                    "Preloading critical resources improves perceived performance and user experience",
                    "nice_to_have",
                    25,  # 25 minutes to fix
                    "medium",
                    "performance",
                    opportunities=critical_resources,
                    preload_links=len(preload_links),
                    prefetch_links=len(prefetch_links),
                    dns_prefetch_links=len(dns_prefetch_links)
                )
            
            # Set check results
            self.set_check_result(result, "preload_links", len(preload_links))
            self.set_check_result(result, "prefetch_links", len(prefetch_links))
            self.set_check_result(result, "dns_prefetch_links", len(dns_prefetch_links))
            self.set_check_result(result, "critical_resources_opportunities", len(critical_resources))
            
        except Exception as e:
            logger.error(f"Error checking resource loading: {str(e)}")
            self.add_business_issue(result, f"Error checking resource loading: {str(e)}", "Error occurred during analysis", "should_fix", 5, "easy", "performance")

    def _calculate_performance_score(self, result: dict) -> None:
        """Calculate performance score based on issues found."""
        checks = result.get("checks", {})
        business_issues = result.get("business_issues", [])
        
        # Start with perfect score
        score = 100
        
        # Get performance issues
        performance_issues = [issue for issue in business_issues if issue["category"] == "performance"]
        
        # Apply penalties based on priority (aligned with ImprovedScoreCalculationService)
        for issue in performance_issues:
            priority_order = issue.get("priority", {}).get("order", 3)
            if priority_order == 1:  # must_fix
                score -= 15  # Aligned with ImprovedScoreCalculationService
            elif priority_order == 2:  # should_fix
                score -= 8   # Aligned with ImprovedScoreCalculationService
            else:  # nice_to_have
                score -= 3   # Aligned with ImprovedScoreCalculationService
        
        # Additional penalties for specific issues
        if checks.get("unoptimized_images", 0) > 5:
            score -= 10
        elif checks.get("unoptimized_images", 0) > 0:
            score -= 5
        
        if checks.get("caching_issues_count", 0) > 0:
            score -= 8
        
        if checks.get("compression_issues_count", 0) > 0:
            score -= 10
        
        if checks.get("page_size_kb", 0) > 1000:
            score -= 15
        elif checks.get("page_size_kb", 0) > 500:
            score -= 8
        elif checks.get("page_size_kb", 0) > 200:
            score -= 3
        
        # Apply bonuses for good practices
        bonus = 0
        if checks.get("compression_enabled", False):
            bonus += 5
        if checks.get("cache_control_present", False):
            bonus += 5
        if checks.get("preload_links", 0) > 0:
            bonus += 3
        if checks.get("unoptimized_images", 0) == 0 and checks.get("total_images", 0) > 0:
            bonus += 5
        
        score = min(100, score + bonus)
        score = max(0, score)
        
        # Set results
        self.set_check_result(result, "performance_score", score)
        result["performance_score"] = score
        
        # Create summary
        total_issues = len(performance_issues)
        if total_issues == 0:
            result["performance_summary"] = "Excellent performance - no optimization issues found"
        elif total_issues <= 2:
            result["performance_summary"] = f"Good performance with {total_issues} minor optimization opportunities"
        elif total_issues <= 5:
            result["performance_summary"] = f"Performance could be improved - {total_issues} optimization opportunities found"
        else:
            result["performance_summary"] = f"Performance needs attention - {total_issues} optimization opportunities found"
        
        # Add optimization recommendations
        recommendations = []
        if checks.get("unoptimized_images", 0) > 0:
            recommendations.append("Optimize images with modern formats (WebP/AVIF)")
        if checks.get("caching_issues_count", 0) > 0:
            recommendations.append("Implement proper caching headers")
        if checks.get("compression_issues_count", 0) > 0:
            recommendations.append("Enable compression (gzip/brotli)")
        if checks.get("page_size_kb", 0) > 200:
            recommendations.append("Reduce page size")
        if checks.get("scripts_without_async_defer", 0) > 0:
            recommendations.append("Add async/defer to JavaScript files")
        
        if recommendations:
            result["performance_recommendations"] = recommendations
