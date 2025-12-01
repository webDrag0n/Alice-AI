import httpx
from bs4 import BeautifulSoup
from typing import Dict, Any, List
from .base import Action
import urllib.parse

class BrowseWeb(Action):
    def __init__(self):
        super().__init__(
            name="browse_web",
            description="浏览网页或搜索信息。当需要获取外部实时信息时使用。",
            parameters={
                "url": "目标网址 (如果为空则必须提供 query)",
                "query": "搜索关键词 (如果提供了 url 则忽略此项)",
                "engine": "搜索引擎 ('bing')"
            },
            category="web"
        )

    async def execute(self, context: Dict[str, Any], url: str = "", query: str = "", engine: str = "bing", **kwargs) -> Dict[str, Any]:
        agent_name = context.get("agent_name", "Alice")
        target_url = url
        is_search = False

        if not target_url and query:
            is_search = True
            target_url = f"https://www.bing.com/search?q={urllib.parse.quote(query)}"
        
        if not target_url:
            return {"error": "Must provide either url or query"}

        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            
            async with httpx.AsyncClient(follow_redirects=True, timeout=15.0) as client:
                try:
                    response = await client.get(target_url, headers=headers)
                    response.raise_for_status()
                except httpx.ConnectTimeout:
                     # Fallback to Bing if direct URL fails or timeout
                     if not is_search:
                         return {
                            "event": "web_browse_error",
                            "message": f"访问网页超时: {target_url}",
                            "data": {"url": target_url, "error": "Connection Timeout"}
                        }
                     # If it was a search, try Bing
                     target_url = f"https://www.bing.com/search?q={urllib.parse.quote(query)}"
                     response = await client.get(target_url, headers=headers)
                     response.raise_for_status()

                html_content = response.text

            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()

            # Extract info
            title = soup.title.string if soup.title else "No Title"
            text = soup.get_text(separator=' ', strip=True)
            
            # Simple stats
            word_count = len(text.split())
            links = soup.find_all('a', href=True)
            link_count = len(links)
            
            # Extract some links for context (especially if search)
            extracted_links = []
            for link in links[:10]: # Top 10 links
                href = link['href']
                if href.startswith('http'):
                    extracted_links.append({"text": link.get_text(strip=True)[:50], "url": href})

            # Truncate text for context window
            content_preview = text[:2000] + "..." if len(text) > 2000 else text

            return {
                "event": "web_browse",
                "message": f"{agent_name} 正在浏览: {title}",
                "data": {
                    "url": target_url,
                    "title": title,
                    "is_search": is_search,
                    "stats": {
                        "word_count": word_count,
                        "link_count": link_count,
                        "content_length": len(text)
                    },
                    "extracted_links": extracted_links,
                    "content": content_preview # This goes to LLM context
                }
            }

        except Exception as e:
            return {
                "event": "web_browse_error",
                "message": f"浏览网页出错: {str(e)}",
                "data": {"error": str(e)}
            }

class VisitPage(Action):
    def __init__(self):
        super().__init__(
            name="visit_page",
            description="直接访问指定的URL链接。用于读取网页内容。",
            parameters={
                "url": "目标网址"
            },
            category="web"
        )

    async def execute(self, context: Dict[str, Any], url: str, **kwargs) -> Dict[str, Any]:
        # Reuse BrowseWeb logic or implement simple fetch
        # For simplicity and consistency, we can delegate to BrowseWeb logic or reimplement
        # Let's reimplement cleanly using httpx
        agent_name = context.get("agent_name", "Alice")
        
        if not url:
            return {"error": "URL is required"}

        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            
            async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                html_content = response.text

            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()

            # Extract info
            title = soup.title.string if soup.title else "No Title"
            text = soup.get_text(separator=' ', strip=True)
            
            # Simple stats
            word_count = len(text.split())
            links = soup.find_all('a', href=True)
            link_count = len(links)
            
            # Extract links
            extracted_links = []
            for link in links[:20]: # More links for direct visit
                href = link['href']
                if href.startswith('http'):
                    extracted_links.append({"text": link.get_text(strip=True)[:50], "url": href})

            # Truncate text
            content_preview = text[:3000] + "..." if len(text) > 3000 else text

            return {
                "event": "visit_page",
                "message": f"{agent_name} 访问了链接: {url}",
                "data": {
                    "url": url,
                    "title": title,
                    "stats": {
                        "word_count": word_count,
                        "link_count": link_count
                    },
                    "extracted_links": extracted_links,
                    "content": content_preview
                }
            }

        except Exception as e:
            return {
                "event": "visit_page_error",
                "message": f"访问链接失败: {str(e)}",
                "data": {"url": url, "error": str(e)}
            }
