"""
数据处理器 - 处理和分析从搜索引擎获取的数据
"""

import re
import json
from typing import List, Dict, Any, Tuple
from collections import Counter
import jieba
import jieba.analyse


class DataProcessor:
    """数据处理器类"""
    
    def __init__(self):
        # 初始化jieba分词
        jieba.initialize()
        
        # 行业分析常用关键词
        self.industry_keywords = {
            "市场规模": ["规模", "市场", "容量", "产值", "营收"],
            "竞争格局": ["竞争", "对手", "格局", "份额", "集中度"],
            "发展趋势": ["趋势", "发展", "前景", "未来", "方向"],
            "技术分析": ["技术", "创新", "研发", "专利", "突破"],
            "政策环境": ["政策", "法规", "监管", "支持", "规划"],
            "用户需求": ["需求", "用户", "消费者", "偏好", "行为"]
        }
    
    def process_search_results(self, search_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        处理搜索结果，提取关键信息
        
        Args:
            search_results: 搜索结果列表
            
        Returns:
            处理后的数据字典
        """
        processed_data = {
            "summary": {},
            "keywords": [],
            "entities": {},
            "sentiment": {},
            "trends": [],
            "statistics": {}
        }
        
        # 提取文本内容
        all_text = self._extract_all_text(search_results)
        
        # 分析关键词
        processed_data["keywords"] = self._extract_keywords(all_text)
        
        # 提取实体信息
        processed_data["entities"] = self._extract_entities(all_text)
        
        # 情感分析
        processed_data["sentiment"] = self._analyze_sentiment(all_text)
        
        # 趋势分析
        processed_data["trends"] = self._analyze_trends(search_results)
        
        # 统计信息
        processed_data["statistics"] = self._calculate_statistics(search_results)
        
        # 生成摘要
        processed_data["summary"] = self._generate_summary(processed_data)
        
        return processed_data
    
    def _extract_all_text(self, search_results: List[Dict[str, Any]]) -> str:
        """提取所有文本内容"""
        all_text = ""
        for result in search_results:
            title = result.get('title', '')
            abstract = result.get('abstract', '')
            all_text += f"{title} {abstract} "
        return all_text.strip()
    
    def _extract_keywords(self, text: str, top_k: int = 20) -> List[Tuple[str, float]]:
        """提取关键词"""
        try:
            # 使用jieba提取关键词
            keywords = jieba.analyse.extract_tags(
                text, 
                topK=top_k, 
                withWeight=True,
                allowPOS=('n', 'nr', 'ns', 'nt', 'nz', 'v', 'a')
            )
            return keywords
        except Exception as e:
            print(f"关键词提取失败: {e}")
            return self._fallback_keyword_extraction(text, top_k)
    
    def _fallback_keyword_extraction(self, text: str, top_k: int) -> List[Tuple[str, float]]:
        """备用的关键词提取方法"""
        # 使用简单的词频统计
        words = jieba.cut(text)
        word_freq = Counter()
        
        for word in words:
            if len(word) >= 2 and not word.isspace():
                word_freq[word] += 1
        
        # 计算权重（基于频率）
        total_words = sum(word_freq.values())
        keywords = []
        for word, freq in word_freq.most_common(top_k):
            weight = freq / total_words
            keywords.append((word, weight))
        
        return keywords
    
    def _extract_entities(self, text: str) -> Dict[str, List[str]]:
        """提取实体信息"""
        entities = {
            "companies": [],
            "products": [],
            "technologies": [],
            "locations": [],
            "dates": []
        }
        
        # 简单的规则匹配（实际应用中可以使用更复杂的NLP模型）
        words = jieba.cut(text)
        
        for word in words:
            if len(word) >= 2:
                # 公司识别（包含"公司"、"集团"等）
                if any(keyword in word for keyword in ["公司", "集团", "企业", "科技", "股份"]):
                    if word not in entities["companies"]:
                        entities["companies"].append(word)
                
                # 产品识别
                elif any(keyword in word for keyword in ["系统", "平台", "软件", "应用", "产品"]):
                    if word not in entities["products"]:
                        entities["products"].append(word)
                
                # 技术识别
                elif any(keyword in word for keyword in ["技术", "算法", "模型", "智能", "数字"]):
                    if word not in entities["technologies"]:
                        entities["technologies"].append(word)
                
                # 地点识别（简单的省市名称匹配）
                elif re.search(r'[省市县区]', word):
                    if word not in entities["locations"]:
                        entities["locations"].append(word)
        
        # 日期提取
        date_patterns = [
            r'\d{4}年',
            r'\d{4}-\d{2}',
            r'\d{4}.\d{2}',
            r'\d{4}年度'
        ]
        
        for pattern in date_patterns:
            dates = re.findall(pattern, text)
            entities["dates"].extend(dates)
        
        # 去重
        for key in entities:
            entities[key] = list(set(entities[key]))[:10]  # 限制数量
        
        return entities
    
    def _analyze_sentiment(self, text: str) -> Dict[str, float]:
        """情感分析（简化版）"""
        # 情感词典（简化版）
        positive_words = {
            "增长", "发展", "提升", "创新", "突破", "领先", "优势", "成功", 
            "进步", "改善", "提升", "优秀", "良好", "积极", "乐观", "前景"
        }
        
        negative_words = {
            "下降", "衰退", "困难", "挑战", "问题", "风险", "压力", "竞争",
            "下滑", "亏损", "困境", "危机", "负面", "悲观", "担忧", "压力"
        }
        
        words = set(jieba.cut(text))
        
        positive_count = len(words & positive_words)
        negative_count = len(words & negative_words)
        total_sentiment_words = positive_count + negative_count
        
        if total_sentiment_words == 0:
            return {"positive": 0.5, "negative": 0.5, "neutral": 1.0}
        
        positive_score = positive_count / total_sentiment_words
        negative_score = negative_count / total_sentiment_words
        neutral_score = 1.0 - (positive_score + negative_score)
        
        return {
            "positive": round(positive_score, 3),
            "negative": round(negative_score, 3),
            "neutral": round(neutral_score, 3)
        }
    
    def _analyze_trends(self, search_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """分析趋势"""
        trends = []
        
        # 基于搜索结果的时间分布分析趋势
        time_keywords = {
            "近期": ["2024", "2023", "最新", "当前", "现在"],
            "中期": ["2022", "2021", "过去两年", "近期发展"],
            "长期": ["2020", "2019", "历史", "传统", "未来发展"]
        }
        
        for period, keywords in time_keywords.items():
            count = sum(1 for result in search_results 
                       if any(keyword in result.get('title', '') or 
                              keyword in result.get('abstract', '') 
                              for keyword in keywords))
            
            if count > 0:
                trends.append({
                    "period": period,
                    "count": count,
                    "intensity": count / len(search_results)
                })
        
        # 技术趋势分析
        tech_trends = self._analyze_tech_trends(search_results)
        trends.extend(tech_trends)
        
        return sorted(trends, key=lambda x: x["intensity"], reverse=True)
    
    def _analyze_tech_trends(self, search_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """分析技术趋势"""
        tech_keywords = {
            "人工智能": ["AI", "人工智能", "机器学习", "深度学习", "神经网络"],
            "大数据": ["大数据", "数据挖掘", "数据分析", "数据科学"],
            "云计算": ["云计算", "云服务", "云平台", "云端"],
            "物联网": ["物联网", "IoT", "智能设备", "传感器"],
            "区块链": ["区块链", "比特币", "数字货币", "分布式账本"]
        }
        
        trends = []
        for tech, keywords in tech_keywords.items():
            count = sum(1 for result in search_results 
                       if any(keyword in result.get('title', '') or 
                              keyword in result.get('abstract', '') 
                              for keyword in keywords))
            
            if count > 0:
                trends.append({
                    "technology": tech,
                    "count": count,
                    "intensity": count / len(search_results)
                })
        
        return trends
    
    def _calculate_statistics(self, search_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """计算统计信息"""
        if not search_results:
            return {}
        
        # 来源统计
        sources = [result.get('source', 'unknown') for result in search_results]
        source_stats = Counter(sources)
        
        # 搜索引擎统计
        engines = [result.get('engine', 'unknown') for result in search_results]
        engine_stats = Counter(engines)
        
        # 时间统计（基于搜索结果的时间戳）
        timestamps = [result.get('timestamp', 0) for result in search_results]
        if timestamps:
            min_time = min(timestamps)
            max_time = max(timestamps)
        else:
            min_time = max_time = 0
        
        return {
            "total_results": len(search_results),
            "unique_sources": len(source_stats),
            "source_distribution": dict(source_stats.most_common(5)),
            "engine_distribution": dict(engine_stats),
            "time_range": {
                "min": min_time,
                "max": max_time
            },
            "avg_title_length": sum(len(result.get('title', '')) for result in search_results) / len(search_results),
            "avg_abstract_length": sum(len(result.get('abstract', '')) for result in search_results) / len(search_results)
        }
    
    def _generate_summary(self, processed_data: Dict[str, Any]) -> Dict[str, Any]:
        """生成数据摘要"""
        summary = {
            "key_insights": [],
            "main_topics": [],
            "data_quality": {},
            "recommendations": []
        }
        
        # 关键洞察
        keywords = processed_data.get("keywords", [])
        if keywords:
            top_keywords = [kw[0] for kw in keywords[:5]]
            summary["key_insights"].append(f"核心关键词: {', '.join(top_keywords)}")
        
        # 主要话题
        entities = processed_data.get("entities", {})
        if entities.get("companies"):
            summary["main_topics"].append(f"涉及企业: {', '.join(entities['companies'][:3])}")
        if entities.get("technologies"):
            summary["main_topics"].append(f"技术领域: {', '.join(entities['technologies'][:3])}")
        
        # 数据质量评估
        stats = processed_data.get("statistics", {})
        summary["data_quality"] = {
            "coverage": "良好" if stats.get("total_results", 0) > 10 else "一般",
            "diversity": "丰富" if stats.get("unique_sources", 0) > 3 else "有限",
            "relevance": "高" if len(keywords) > 5 else "中"
        }
        
        # 分析建议
        sentiment = processed_data.get("sentiment", {})
        if sentiment.get("positive", 0) > 0.6:
            summary["recommendations"].append("行业呈现积极发展态势")
        elif sentiment.get("negative", 0) > 0.6:
            summary["recommendations"].append("行业面临挑战，需要关注风险")
        else:
            summary["recommendations"].append("行业处于平稳发展阶段")
        
        trends = processed_data.get("trends", [])
        if trends:
            main_trend = trends[0]
            summary["recommendations"].append(f"主要趋势: {main_trend.get('technology', main_trend.get('period', '未知'))}")
        
        return summary
    
    def extract_numerical_data(self, text: str) -> Dict[str, List[float]]:
        """从文本中提取数值数据"""
        numerical_data = {}
        
        # 匹配各种数值模式
        patterns = {
            "percentages": r'(\d+(?:\.\d+)?)%',
            "years": r'(\d{4})年',
            "money": r'(\d+(?:\.\d+)?)[亿万]?元',
            "numbers": r'(\d+(?:\.\d+)?)'
        }
        
        for key, pattern in patterns.items():
            matches = re.findall(pattern, text)
            if matches:
                numerical_data[key] = [float(match) for match in matches if match.replace('.', '').isdigit()]
        
        return numerical_data
    
    def analyze_competition(self, search_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """竞争分析"""
        competition_data = {
            "competitors": [],
            "market_share": {},
            "competitive_landscape": {}
        }
        
        # 提取竞争对手信息
        all_text = self._extract_all_text(search_results)
        entities = self._extract_entities(all_text)
        
        competition_data["competitors"] = entities.get("companies", [])[:10]
        
        # 简单的市场份额估算（基于提及频率）
        if competition_data["competitors"]:
            total_mentions = sum(1 for result in search_results 
                               if any(company in result.get('title', '') or 
                                      company in result.get('abstract', '') 
                                      for company in competition_data["competitors"]))
            
            for company in competition_data["competitors"]:
                mentions = sum(1 for result in search_results 
                             if company in result.get('title', '') or 
                                company in result.get('abstract', ''))
                
                if total_mentions > 0:
                    share = (mentions / total_mentions) * 100
                    competition_data["market_share"][company] = round(share, 1)
        
        # 竞争格局分析
        if competition_data["market_share"]:
            sorted_shares = sorted(competition_data["market_share"].items(), 
                                 key=lambda x: x[1], reverse=True)
            
            if len(sorted_shares) >= 3:
                competition_data["competitive_landscape"] = {
                    "leader": sorted_shares[0][0],
                    "challengers": [company for company, _ in sorted_shares[1:3]],
                    "followers": [company for company, _ in sorted_shares[3:]]
                }
        
        return competition_data
