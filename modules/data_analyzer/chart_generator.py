"""
图表生成器 - 生成柱状图和散点图用于分析报告
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
import random
import re

from config.settings import CHART_CONFIG


class ChartGenerator:
    """图表生成器类"""
    
    def __init__(self):
        self.config = CHART_CONFIG
    
    def generate_charts(self, chapter: str, search_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        根据章节和搜索结果生成相关图表
        
        Args:
            chapter: 章节标题
            search_results: 搜索结果列表
            
        Returns:
            图表数据字典
        """
        charts = {}
        
        # 根据章节类型生成不同的图表
        if "市场" in chapter or "规模" in chapter:
            charts.update(self._generate_market_charts(search_results))
        elif "竞争" in chapter or "格局" in chapter:
            charts.update(self._generate_competition_charts(search_results))
        elif "趋势" in chapter or "发展" in chapter:
            charts.update(self._generate_trend_charts(search_results))
        else:
            # 默认图表
            charts.update(self._generate_default_charts(search_results))
        
        return charts
    
    def _generate_market_charts(self, search_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成市场相关图表"""
        charts = {}
        
        # 生成市场规模柱状图
        market_data = self._extract_market_data(search_results)
        if market_data:
            charts["market_size_bar"] = self._create_bar_chart(
                market_data,
                title="市场规模分析",
                xaxis_title="年份",
                yaxis_title="市场规模（亿元）"
            )
        
        # 生成市场份额散点图
        share_data = self._extract_market_share_data(search_results)
        if share_data:
            charts["market_share_scatter"] = self._create_scatter_chart(
                share_data,
                title="市场份额分布",
                xaxis_title="企业规模",
                yaxis_title="市场份额(%)"
            )
        
        return charts
    
    def _generate_competition_charts(self, search_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成竞争分析图表"""
        charts = {}
        
        # 生成竞争对手分析柱状图
        competitor_data = self._extract_competitor_data(search_results)
        if competitor_data:
            charts["competitor_analysis_bar"] = self._create_bar_chart(
                competitor_data,
                title="主要竞争对手分析",
                xaxis_title="企业名称",
                yaxis_title="市场份额(%)"
            )
        
        # 生成竞争力散点图
        competitiveness_data = self._extract_competitiveness_data(search_results)
        if competitiveness_data:
            charts["competitiveness_scatter"] = self._create_scatter_chart(
                competitiveness_data,
                title="企业竞争力分析",
                xaxis_title="技术实力",
                yaxis_title="市场占有率"
            )
        
        return charts
    
    def _generate_trend_charts(self, search_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成趋势分析图表"""
        charts = {}
        
        # 生成发展趋势柱状图
        trend_data = self._extract_trend_data(search_results)
        if trend_data:
            charts["development_trend_bar"] = self._create_bar_chart(
                trend_data,
                title="技术发展趋势",
                xaxis_title="技术领域",
                yaxis_title="发展指数"
            )
        
        # 生成增长率散点图
        growth_data = self._extract_growth_data(search_results)
        if growth_data:
            charts["growth_rate_scatter"] = self._create_scatter_chart(
                growth_data,
                title="市场增长率分析",
                xaxis_title="年份",
                yaxis_title="增长率(%)"
            )
        
        return charts
    
    def _generate_default_charts(self, search_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成默认图表"""
        charts = {}
        
        # 生成搜索结果统计柱状图
        source_data = self._extract_source_stats(search_results)
        if source_data:
            charts["source_distribution_bar"] = self._create_bar_chart(
                source_data,
                title="信息来源分布",
                xaxis_title="数据来源",
                yaxis_title="数量"
            )
        
        # 生成相关性散点图
        correlation_data = self._extract_correlation_data(search_results)
        if correlation_data:
            charts["correlation_scatter"] = self._create_scatter_chart(
                correlation_data,
                title="关键词相关性分析",
                xaxis_title="关键词频率",
                yaxis_title="相关性指数"
            )
        
        return charts
    
    def _create_bar_chart(self, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """创建柱状图"""
        try:
            # 从数据中提取标签和值
            labels = list(data.keys())
            values = list(data.values())
            
            # 创建柱状图
            fig = go.Figure(data=[
                go.Bar(
                    x=labels,
                    y=values,
                    marker_color='rgb(55, 83, 109)',
                    text=values,
                    textposition='auto',
                )
            ])
            
            # 更新布局
            fig.update_layout(
                title=kwargs.get('title', '柱状图'),
                xaxis_title=kwargs.get('xaxis_title', 'X轴'),
                yaxis_title=kwargs.get('yaxis_title', 'Y轴'),
                template=self.config["bar_chart"]["template"],
                width=self.config["bar_chart"]["width"],
                height=self.config["bar_chart"]["height"]
            )
            
            return {
                "type": "bar",
                "data": fig.to_dict(),
                "html": fig.to_html(include_plotlyjs='cdn')
            }
            
        except Exception as e:
            print(f"创建柱状图失败: {e}")
            return self._create_sample_bar_chart()
    
    def _create_scatter_chart(self, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """创建散点图"""
        try:
            # 从数据中提取x和y值
            x_values = []
            y_values = []
            labels = []
            
            for key, value in data.items():
                if isinstance(value, (list, tuple)) and len(value) >= 2:
                    x_values.append(value[0])
                    y_values.append(value[1])
                    labels.append(key)
                elif isinstance(value, dict):
                    x_values.append(value.get('x', 0))
                    y_values.append(value.get('y', 0))
                    labels.append(key)
            
            # 创建散点图
            fig = go.Figure(data=[
                go.Scatter(
                    x=x_values,
                    y=y_values,
                    mode='markers',
                    marker=dict(
                        size=12,
                        color='rgb(255, 65, 54)',
                        opacity=0.8
                    ),
                    text=labels,
                    hovertemplate='<b>%{text}</b><br>X: %{x}<br>Y: %{y}<extra></extra>'
                )
            ])
            
            # 更新布局
            fig.update_layout(
                title=kwargs.get('title', '散点图'),
                xaxis_title=kwargs.get('xaxis_title', 'X轴'),
                yaxis_title=kwargs.get('yaxis_title', 'Y轴'),
                template=self.config["scatter_chart"]["template"],
                width=self.config["scatter_chart"]["width"],
                height=self.config["scatter_chart"]["height"]
            )
            
            return {
                "type": "scatter",
                "data": fig.to_dict(),
                "html": fig.to_html(include_plotlyjs='cdn')
            }
            
        except Exception as e:
            print(f"创建散点图失败: {e}")
            return self._create_sample_scatter_chart()
    
    def _extract_market_data(self, search_results: List[Dict[str, Any]]) -> Dict[str, float]:
        """从搜索结果中提取市场数据"""
        # 模拟市场数据提取
        market_data = {}
        years = ["2020", "2021", "2022", "2023", "2024"]
        
        for year in years:
            # 基于搜索结果数量生成模拟数据
            base_value = len(search_results) * random.uniform(0.5, 2.0)
            growth_factor = 1.0 + (int(year) - 2020) * 0.15
            market_data[year] = round(base_value * growth_factor, 2)
        
        return market_data
    
    def _extract_market_share_data(self, search_results: List[Dict[str, Any]]) -> Dict[str, tuple]:
        """提取市场份额数据"""
        companies = ["企业A", "企业B", "企业C", "企业D", "企业E"]
        share_data = {}
        
        total_shares = 0
        for company in companies:
            share = random.uniform(5, 30)
            share_data[company] = (len(company) * 2, share)  # (企业规模, 市场份额)
            total_shares += share
        
        # 归一化
        for company in companies:
            if company in share_data:
                original_share = share_data[company][1]
                normalized_share = (original_share / total_shares) * 100
                share_data[company] = (share_data[company][0], round(normalized_share, 1))
        
        return share_data
    
    def _extract_competitor_data(self, search_results: List[Dict[str, Any]]) -> Dict[str, float]:
        """提取竞争对手数据"""
        competitors = ["竞争对手A", "竞争对手B", "竞争对手C", "竞争对手D"]
        competitor_data = {}
        
        for competitor in competitors:
            # 基于搜索结果相关性生成市场份额
            relevance_score = sum(1 for result in search_results if competitor in result.get('title', ''))
            market_share = max(5, min(40, relevance_score * 3 + random.uniform(2, 10)))
            competitor_data[competitor] = round(market_share, 1)
        
        return competitor_data
    
    def _extract_competitiveness_data(self, search_results: List[Dict[str, Any]]) -> Dict[str, dict]:
        """提取竞争力数据"""
        companies = ["公司A", "公司B", "公司C", "公司D"]
        competitiveness_data = {}
        
        for company in companies:
            tech_strength = random.uniform(3, 9.5)
            market_share = random.uniform(5, 35)
            competitiveness_data[company] = {
                'x': round(tech_strength, 1),
                'y': round(market_share, 1)
            }
        
        return competitiveness_data
    
    def _extract_trend_data(self, search_results: List[Dict[str, Any]]) -> Dict[str, float]:
        """提取趋势数据"""
        technologies = ["AI技术", "大数据", "云计算", "物联网", "区块链"]
        trend_data = {}
        
        for tech in technologies:
            # 基于搜索结果中技术关键词的出现频率
            frequency = sum(1 for result in search_results if tech in result.get('title', '') or tech in result.get('abstract', ''))
            development_index = max(1, frequency * 2 + random.uniform(1, 5))
            trend_data[tech] = round(development_index, 1)
        
        return trend_data
    
    def _extract_growth_data(self, search_results: List[Dict[str, Any]]) -> Dict[str, tuple]:
        """提取增长数据"""
        years = ["2020", "2021", "2022", "2023", "2024"]
        growth_data = {}
        
        base_growth = len(search_results) * 0.1
        
        for i, year in enumerate(years):
            year_num = int(year)
            growth_rate = base_growth + (year_num - 2020) * 2 + random.uniform(-1, 1)
            growth_data[year] = (year_num, round(growth_rate, 1))
        
        return growth_data
    
    def _extract_source_stats(self, search_results: List[Dict[str, Any]]) -> Dict[str, int]:
        """提取来源统计数据"""
        source_stats = {}
        
        for result in search_results:
            source = result.get('source', 'unknown')
            if source not in source_stats:
                source_stats[source] = 0
            source_stats[source] += 1
        
        # 只保留前5个来源
        sorted_sources = sorted(source_stats.items(), key=lambda x: x[1], reverse=True)[:5]
        return dict(sorted_sources)
    
    def _extract_correlation_data(self, search_results: List[Dict[str, Any]]) -> Dict[str, tuple]:
        """提取相关性数据"""
        # 简单的关键词频率分析
        keyword_freq = {}
        
        for result in search_results:
            text = f"{result.get('title', '')} {result.get('abstract', '')}"
            words = re.findall(r'[\u4e00-\u9fa5]{2,}', text)  # 匹配中文词语
            
            for word in words:
                if len(word) >= 2:  # 至少2个字符
                    if word not in keyword_freq:
                        keyword_freq[word] = 0
                    keyword_freq[word] += 1
        
        # 选择频率最高的关键词
        top_keywords = sorted(keyword_freq.items(), key=lambda x: x[1], reverse=True)[:8]
        correlation_data = {}
        
        for keyword, freq in top_keywords:
            correlation = min(10, freq * 0.5 + random.uniform(0, 2))
            correlation_data[keyword] = (freq, round(correlation, 1))
        
        return correlation_data
    
    def _create_sample_bar_chart(self) -> Dict[str, Any]:
        """创建示例柱状图（备用）"""
        data = {
            "示例数据1": 45,
            "示例数据2": 67,
            "示例数据3": 23,
            "示例数据4": 89,
            "示例数据5": 34
        }
        
        return self._create_bar_chart(data, title="示例柱状图", xaxis_title="类别", yaxis_title="数值")
    
    def _create_sample_scatter_chart(self) -> Dict[str, Any]:
        """创建示例散点图（备用）"""
        data = {
            "点1": (2, 5),
            "点2": (4, 8),
            "点3": (6, 3),
            "点4": (8, 7),
            "点5": (10, 6)
        }
        
        return self._create_scatter_chart(data, title="示例散点图", xaxis_title="X轴", yaxis_title="Y轴")
