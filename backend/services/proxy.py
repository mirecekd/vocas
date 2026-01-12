import httpx
from bs4 import BeautifulSoup
import logging
from urllib.parse import urljoin, urlparse

logger = logging.getLogger(__name__)

class ProxyService:
    def __init__(self):
        self.client = httpx.AsyncClient(
            follow_redirects=True,
            timeout=30.0,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
        )

    def rewrite_links(self, soup: BeautifulSoup, original_url: str, base_host: str) -> None:
        """
        Rewrite all <a href> links to go through the proxy.
        
        Args:
            soup: BeautifulSoup object
            original_url: Original page URL
            base_host: Vocas server URL (e.g., http://localhost:5000)
        """
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            
            # Skip anchors, javascript, data URLs, and mailto
            if (href.startswith('#') or 
                href.startswith('javascript:') or 
                href.startswith('data:') or 
                href.startswith('mailto:')):
                continue
            
            # Convert relative URLs to absolute using the original page URL
            absolute_url = urljoin(original_url, href)
            
            # Rewrite to proxy URL with absolute path including Vocas server URL
            a_tag['href'] = f"{base_host}/read/{absolute_url}"

    async def fetch_and_process(self, url: str, base_host: str) -> str:
        """
        Fetches the URL, injects overlay, and returns modified HTML.
        """
        if not url.startswith('http'):
            url = 'https://' + url

        try:
            response = await self.client.get(url)
            response.raise_for_status()
            
            # Detect encoding
            encoding = response.encoding or 'utf-8'
            
            soup = BeautifulSoup(response.content, 'html.parser', from_encoding=encoding)
            
            # 1. Inject <base> tag so relative links/images work
            head = soup.find('head')
            if not head:
                head = soup.new_tag('head')
                soup.insert(0, head)
            
            # Remove existing base if any
            existing_base = head.find('base')
            if existing_base:
                existing_base.decompose()
                
            new_base = soup.new_tag('base', href=url)
            head.insert(0, new_base)

            # Add referrer policy to help load assets
            meta_referrer = soup.new_tag('meta', attrs={'name': 'referrer', 'content': 'no-referrer'})
            head.insert(0, meta_referrer)
            
            # Remove CSP meta tags
            for meta in soup.find_all('meta', attrs={'http-equiv': 'Content-Security-Policy'}):
                meta.decompose()

            # 2. Inject Vocas Overlay (CSS + JS)
            # We inject relative paths to our server
            
            # CSS
            css_link = soup.new_tag('link', rel='stylesheet', href=f"{base_host}/static/vocas-overlay.css")
            head.append(css_link)
            
            # Readability JS (CDN for now, or bundled)
            readability_script = soup.new_tag('script', src="https://unpkg.com/@mozilla/readability@0.4.4/Readability.js")
            
            # Vocas Configuration (API URL)
            config_script = soup.new_tag('script')
            config_script.string = f'window.VOCAS_API_URL = "{base_host}/api/process";'

            # Vocas JS
            vocas_script = soup.new_tag('script', src=f"{base_host}/static/vocas-overlay.js")
            
            body = soup.find('body')
            if body:
                body.append(config_script)
                body.append(readability_script)
                body.append(vocas_script)
            else:
                # Fallback if no body
                soup.append(config_script)
                soup.append(readability_script)
                soup.append(vocas_script)

            # 3. Rewrite all links to go through proxy
            self.rewrite_links(soup, url, base_host)

            return str(soup)

        except Exception as e:
            logger.error(f"Proxy error for {url}: {e}")
            return f"<h1>Error loading page: {e}</h1>"

    async def close(self):
        await self.client.aclose()
