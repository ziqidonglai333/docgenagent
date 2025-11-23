"""
搜狗搜索器 - 使用搜狗搜索引擎获取行业数据
"""

import requests
from bs4 import BeautifulSoup
import time
import random
from typing import List, Dict, Any
import re
import urllib.parse

from config.settings import SEARCH_ENGINE_CONFIG


class SogouSearcher:
    """搜狗搜索引擎接口"""
    
    def __init__(self):
        self.config = SEARCH_ENGINE_CONFIG["sogou"]
        self.session = requests.Session()
        self.session.headers.update(self.config["headers"])
    
    def search(self, topic: str, keywords: List[str] = None) -> List[Dict[str, Any]]:
        """
        使用搜狗搜索主题和关键词
        
        Args:
            topic: 搜索主题
            keywords: 相关关键词列表
            
        Returns:
            搜索结果列表
        """
        search_terms = self._build_search_terms(topic, keywords)
        all_results = []
        
        for term in search_terms:
            try:
                results = self._perform_search(term)
                all_results.extend(results)
                # 添加随机延迟避免被封
                time.sleep(random.uniform(1, 3))
            except Exception as e:
                print(f"搜狗搜索错误: {e}")
                continue
        
        # 去重和排序
        return self._deduplicate_results(all_results)
    
    def _build_search_terms(self, topic: str, keywords: List[str]) -> List[str]:
        """构建搜索词列表"""
        base_terms = [
            f"{topic} 行业分析报告",
            f"{topic} 市场调研",
            f"{topic} 发展现状",
            f"{topic} 前景预测",
            f"{topic} 政策环境"
        ]
        
        if keywords:
            for keyword in keywords:
                base_terms.extend([
                    f"{topic} {keyword} 分析",
                    f"{keyword} 行业报告"
                ])
        
        return base_terms
    
    def _perform_search(self, search_term: str) -> List[Dict[str, Any]]:
        """执行单次搜索"""
        params = self.config["params"].copy()
        params["query"] = search_term
        
        try:
            response = self.session.get(
                self.config["search_url"],
                params=params,
                timeout=10
            )
            response.raise_for_status()
            
            return self._parse_search_results(response.text, search_term)
            
        except requests.RequestException as e:
            print(f"搜狗搜索请求失败: {e}")
            return []
    
    def _parse_search_results(self, html: str, search_term: str) -> List[Dict[str, Any]]:
        """解析搜狗搜索结果页面"""
        soup = BeautifulSoup(html, 'html.parser')
        results = []
        
        # 搜狗搜索结果通常包含在class为"vrwrap"或"rb"的div中
        result_divs = soup.find_all('div', class_=['vrwrap', 'rb'])
        
        for div in result_divs:
            try:
                result = self._extract_result_info(div, search_term)
                if result:
                    results.append(result)
            except Exception as e:
                print(f"解析搜索结果失败: {e}")
                continue
        
        return results
    
    def _extract_result_info(self, result_div, search_term: str) -> Dict[str, Any]:
        """提取单个搜索结果信息"""
        # 提取标题
        title_elem = result_div.find('h3') or result_div.find('a')
        if not title_elem:
            return None
        
        title = title_elem.get_text().strip()
        
        # 提取链接
        link_elem = result_div.find('a')
        if not link_elem or not link_elem.get('href'):
            return None
        
        url = link_elem['href']
        
        # 搜狗链接处理
        if url.startswith('/'):
            url = 'https://www.sogou.com' + url
        elif not url.startswith('http'):
            return None
        
        # 解析真实URL
        real_url = self._resolve_sogou_url(url)
        if not real_url:
            return None
        
        # 提取摘要
        abstract_elem = result_div.find('p', class_='str-pd-info') or result_div
        abstract = abstract_elem.get_text().strip()[:200]  # 限制长度
        
        # 提取来源网站
        source = self._extract_source(real_url)
        
        return {
            "title": title,
            "url": real_url,
            "abstract": abstract,
            "source": source,
            "search_term": search_term,
            "engine": "sogou",
            "timestamp": time.time()
        }
    
    def _resolve_sogou_url(self, url: str) -> str:
        """解析搜狗重定向URL"""
        if not url.startswith('http'):
            return None
        
        try:
            # 搜狗可能使用重定向，我们需要获取真实URL
            if 'sogou.com' in url:
                # 如果是搜狗自己的链接，可能需要特殊处理
                response = self.session.head(url, allow_redirects=True, timeout=5)
                return response.url
            else:
                return url
        except:
            return url
    
    def _extract_source(self, url: str) -> str:
        """从URL提取来源网站"""
        try:
            # 简单的域名提取
            domain = re.search(r'https?://([^/]+)', url)
            if domain:
                return domain.group(1)
            return "unknown"
        except:
            return "unknown"
    
    def _deduplicate_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """去重搜索结果"""
        seen_urls = set()
        unique_results = []
        
        for result in results:
            if result["url"] not in seen_urls:
                seen_urls.add(result["url"])
                unique_results.append(result)
        
        # 按相关性排序
        return sorted(unique_results, key=lambda x: len(x["title"]), reverse=True)
    
    def get_content_from_url(self, url: str) -> str:
        """从URL获取页面内容"""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 移除脚本和样式标签
            for script in soup(["script", "style"]):
                script.decompose()
            
            # 提取正文内容 - 针对中文网站优化
            # 尝试找到主要内容区域
            content_selectors = [
                '.article-content',
                '.content',
                '.main-content',
                '.article',
                '.post-content',
                '.news-content',
                '#content',
                '#article',
                '.text'
            ]
            
            content_elem = None
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    break
            
            if content_elem:
                text = content_elem.get_text()
            else:
                text = soup.get_text()
            
            # 清理文本
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            return text[:5000]  # 限制长度
            
        except Exception as e:
            print(f"获取页面内容失败 {url}: {e}")
            return ""
