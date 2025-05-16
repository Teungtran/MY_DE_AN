import cloudscraper
import httpx  
import tempfile
import os
import traceback
from typing import Optional, Tuple,List
from markitdown import MarkItDown 
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import asyncio
from config.base_config import APP_CONFIG
from utils.logger.logger import get_logger
logger = get_logger(__name__)
DOCINTEL_ENDPOINT = APP_CONFIG.crawl_config.docintel_endpoint
BASE_URL = APP_CONFIG.crawl_config.base_url

class FPTCrawler:
    def __init__(self):
        """
        Initialize the FPTCrawler class for fetching and processing fpt data.
        
        Args:
            base_url: The base URL for resolving relative URLs.
            docintel_endpoint: The endpoint for the MarkItDown service.
            output_dir: Directory to save processed markdown files.
        """
        self.base_url = BASE_URL
        self.docintel_endpoint = DOCINTEL_ENDPOINT
        self.output_dir = "markdown_dir"

    async def fetch_html(self, url: str) -> Optional[str]:
        """
        Fetches HTML content by running both httpx and cloudscraper methods concurrently.
        Returns the result from whichever method completes successfully first.
        """
        httpx_task = asyncio.create_task(self.fetch_html_httpx(url))
        cloudscraper_task = asyncio.create_task(self.fetch_html_cloudscraper(url))

        
        pending_tasks = {httpx_task, cloudscraper_task}
        html_content = None
        while pending_tasks and html_content is None:
            done_tasks, pending_tasks = await asyncio.wait(
                pending_tasks, 
                return_when=asyncio.FIRST_COMPLETED
            )
            
            for task in done_tasks:
                try:
                    result, method = task.result()
                    if result is not None:
                        html_content = result
                        print(f"[Success] Got content using {method}")
                        for pending_task in pending_tasks:
                            pending_task.cancel()
                        break
                except Exception as e:
                    print(f"[Error] Task failed: {e}")
        
        if html_content is None:
            print("[Error] Unable to fetch content from URL using any method.")
            
        return html_content
    
    def fetch_raw_html_from_url(self, url: str) -> Optional[str]:
        """
        Fetches raw HTML content from a URL using cloudscraper.
        Returns HTML string or None if there's an error.
        """
        try:
            scraper = cloudscraper.create_scraper(
                browser={ 
                    'browser': 'chrome',
                    'platform': 'windows',
                    'mobile': False
                }
            )
            response = scraper.get(url, timeout=3)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"[cloudscraper] Failed to fetch: {e}")
            return None

    async def fetch_html_httpx(self, url: str) -> Tuple[Optional[str], str]:
        """
        Fetches HTML content using httpx async client.
        Returns tuple of (HTML string or None if there's an error, method name).
        """
        method_name = "httpx"
        try:
            async with httpx.AsyncClient(timeout=3, limits=httpx.Limits(max_connections=5)) as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.text, method_name
        except Exception as e:
            print(f"[{method_name}] Failed to fetch: {e}")
            return None, method_name

    async def fetch_html_cloudscraper(self, url: str) -> Tuple[Optional[str], str]:
        """
        Fetches HTML content using cloudscraper in an executor to not block the event loop.
        Returns tuple of (HTML string or None if there's an error, method name).
        """
        method_name = "cloudscraper"
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self.fetch_raw_html_from_url, url)
            return result, method_name
        except Exception as e:
            print(f"[{method_name}] Failed to fetch: {e}")
            return None, method_name

    def clean_html_content(self, html_content: str) -> Tuple[str, List[str]]:
        """
        Cleans HTML content by removing headers, navs, footers, etc.,
        extracts og:image meta tags and processes tables into Markdown.
        Returns (cleaned_html, extracted_images).
        """
        soup = BeautifulSoup(html_content, 'html.parser')

        elements_to_remove = [
            "header", "nav", ".header", ".header--wrapper", ".navbar", 
            "footer", ".footer", ".footer--container", 
            ".navigation", ".nav-bar", ".menu", ".main-menu",
            ".sidebar", ".ads", ".advertisement", ".cookie-notice", 
            ".social-media", ".share-buttons", ".comments",
            # FPTShop specific selectors
            ".logo-wrapper", ".logo", ".cart-wrapper", ".main-categories",
            "a[href*='gio-hang']",  # Remove cart link
            # Hot-key div with search suggestions
            ".hot-key"
        ]
        for selector in elements_to_remove:
            if selector.startswith('.'):
                class_name = selector[1:]
                for element in soup.find_all(class_=lambda x: x and class_name in x.split()):
                    element.decompose()
            else:
                for element in soup.find_all(selector):
                    element.decompose()

        extracted_images = []
        seen_image_srcs = set()
        for tag in soup.find_all("meta", property="og:image"):
            src = tag.get("content", "")
            if (src.endswith(".png") or src.endswith(".jpg")) and src not in seen_image_srcs:
                full_url = urljoin(self.base_url, src)
                seen_image_srcs.add(full_url)
                extracted_images.append(f"![Images]({full_url})")

        # Add extraction for all img tags
        for img_tag in soup.find_all("img"):
            src = img_tag.get("src", "")
            if (src.endswith(".png") or src.endswith(".jpg")) and src not in seen_image_srcs:
                full_url = urljoin(self.base_url, src)
                seen_image_srcs.add(full_url)
                extracted_images.append(f"![Images]({full_url})")

        for a_tag in soup.find_all('a'):
            if a_tag.has_attr('href') and not a_tag['href'].startswith(('http://', 'https://', 'data:', '#', 'javascript:')):
                a_tag['href'] = urljoin(self.base_url, a_tag['href'])

        return str(soup), extracted_images

    def format_markdown_content(self, markdown_text: str, extracted_images: List[str]) -> str:
        """
        Formats the markdown content by removing duplicates and formatting.
        
        Args:
            markdown_text: The raw markdown text.
            extracted_images: List of extracted image URLs formatted as markdown.
            
        Returns:
            Formatted markdown content.
        """
        seen = set()
        result_lines = []

        for line in markdown_text.splitlines():
            stripped = line.strip()
            if stripped.lower().startswith("loading") or not stripped:
                continue
            if stripped not in seen:
                seen.add(stripped)
                result_lines.append(line)

        # Add main content
        content = "### CONTENT\n" + "\n".join(result_lines)

        # Append extracted images
        if extracted_images:
            content += "\n\n### IMAGE\n" + "\n".join(extracted_images)

        return content

    async def get_converted_document(self, url: str) -> Optional[Tuple[str, str]]:
        """
        Converts HTML content from URL to Markdown after cleaning the HTML.
        Uses concurrent fetching to get the fastest successful response.
        
        Args:
            url: The URL to fetch and convert.
            
        Returns:
            Tuple of (formatted_markdown, url) or None if failed.
        """
        temp_html_file_path = None

        try:
            html_content = await self.fetch_html(url)
            
            if html_content is None:
                print("[Error] Unable to fetch content from URL.")
                return None
            
            cleaned_html, extracted_images = self.clean_html_content(html_content)
            
            with tempfile.NamedTemporaryFile(mode='w+', suffix='.html', delete=False, encoding='utf-8') as temp_f:
                temp_f.write(cleaned_html)
                temp_html_file_path = temp_f.name
                print(f"Saved cleaned HTML to temporary file: {temp_html_file_path}")

            md = MarkItDown(docintel_endpoint=self.docintel_endpoint)
            result = md.convert(temp_html_file_path)
            
            formatted_markdown = self.format_markdown_content(result.markdown, extracted_images)
            
            os.makedirs(self.output_dir, exist_ok=True)
            safe_filename = re.sub(r'\W+', '_', url.strip())[:50] + ".md"
            output_path = os.path.join(self.output_dir, safe_filename)

            with open(output_path, 'w', encoding='utf-8') as f_out:
                f_out.write(formatted_markdown)

            print(f"Successfully converted to Markdown and saved to {output_path}")
            return formatted_markdown, url

        except Exception as e:
            print(f"An error occurred during conversion: {e}")
            traceback.print_exc()
            return None
        finally:
            if temp_html_file_path and os.path.exists(temp_html_file_path):
                try:
                    os.remove(temp_html_file_path)
                    print(f"Deleted temporary file: {temp_html_file_path}")
                except OSError as e:
                    print(f"Error when deleting temporary file {temp_html_file_path}: {e}")