"""
HTML报告生成器 - 生成包含图表的HTML分析报告
"""

import os
import datetime
from typing import Dict, Any, List
import json


class HTMLGenerator:
    """HTML报告生成器类"""
    
    def __init__(self):
        self.template_dir = "templates"
        self.output_dir = "output"
        self._ensure_directories()
    
    def _ensure_directories(self):
        """确保必要的目录存在"""
        os.makedirs(self.template_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
    
    def generate_report(self, 
                       report_data: Dict[str, Any], 
                       charts_data: Dict[str, Any],
                       output_path: str = None) -> str:
        """
        生成完整的HTML分析报告
        
        Args:
            report_data: 报告数据
            charts_data: 图表数据
            output_path: 输出路径
            
        Returns:
            生成的HTML文件路径
        """
        if output_path is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(self.output_dir, f"analysis_report_{timestamp}.html")
        
        # 生成HTML内容
        html_content = self._build_html_content(report_data, charts_data)
        
        # 保存文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return output_path
    
    def _build_html_content(self, report_data: Dict[str, Any], charts_data: Dict[str, Any]) -> str:
        """构建HTML内容"""
        html_template = self._get_html_template()
        
        # 替换模板变量
        html_content = html_template.replace("{{TITLE}}", report_data.get("title", "行业分析报告"))
        html_content = html_content.replace("{{GENERATED_DATE}}", datetime.datetime.now().strftime("%Y年%m月%d日"))
        html_content = html_content.replace("{{SUMMARY}}", self._generate_summary_section(report_data))
        html_content = html_content.replace("{{CONTENT}}", self._generate_content_sections(report_data, charts_data))
        html_content = html_content.replace("{{CHARTS}}", self._generate_charts_section(charts_data))
        html_content = html_content.replace("{{CONCLUSION}}", self._generate_conclusion_section(report_data))
        
        return html_content
    
    def _get_html_template(self) -> str:
        """获取HTML模板"""
        return """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{TITLE}}</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Microsoft YaHei', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f8f9fa;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 40px;
            box-shadow: 0 0 20px rgba(0,0,0,0.1);
            border-radius: 8px;
        }
        
        .header {
            text-align: center;
            margin-bottom: 40px;
            border-bottom: 2px solid #2c3e50;
            padding-bottom: 20px;
        }
        
        .header h1 {
            color: #2c3e50;
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .header .subtitle {
            color: #7f8c8d;
            font-size: 1.2em;
        }
        
        .section {
            margin-bottom: 40px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 6px;
            border-left: 4px solid #3498db;
        }
        
        .section h2 {
            color: #2c3e50;
            margin-bottom: 15px;
            font-size: 1.8em;
        }
        
        .section h3 {
            color: #34495e;
            margin: 20px 0 10px 0;
            font-size: 1.4em;
        }
        
        .chart-container {
            margin: 20px 0;
            padding: 15px;
            background: white;
            border-radius: 6px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .chart-row {
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
            margin: 20px 0;
        }
        
        .chart-item {
            flex: 1 1 calc(50% - 20px);
            min-width: 300px;
        }
        
        .summary-box {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 25px;
            border-radius: 8px;
            margin: 20px 0;
        }
        
        .summary-box h3 {
            color: white;
            margin-bottom: 15px;
        }
        
        .key-points {
            list-style: none;
            padding: 0;
        }
        
        .key-points li {
            padding: 8px 0;
            border-bottom: 1px solid rgba(255,255,255,0.2);
        }
        
        .key-points li:last-child {
            border-bottom: none;
        }
        
        .data-table {
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
            background: white;
        }
        
        .data-table th,
        .data-table td {
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        
        .data-table th {
            background-color: #34495e;
            color: white;
        }
        
        .data-table tr:hover {
            background-color: #f5f5f5;
        }
        
        .conclusion {
            background: #2ecc71;
            color: white;
            padding: 25px;
            border-radius: 8px;
            margin: 30px 0;
        }
        
        .conclusion h2 {
            color: white;
        }
        
        .footer {
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            color: #7f8c8d;
        }
        
        @media (max-width: 768px) {
            .container {
                padding: 20px;
            }
            
            .chart-item {
                flex: 1 1 100%;
            }
            
            .header h1 {
                font-size: 2em;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{{TITLE}}</h1>
            <div class="subtitle">生成日期：{{GENERATED_DATE}}</div>
        </div>
        
        <div class="section">
            <h2>报告摘要</h2>
            {{SUMMARY}}
        </div>
        
        <div class="section">
            <h2>详细分析</h2>
            {{CONTENT}}
        </div>
        
        <div class="section">
            <h2>数据图表</h2>
            {{CHARTS}}
        </div>
        
        <div class="conclusion">
            <h2>结论与建议</h2>
            {{CONCLUSION}}
        </div>
        
        <div class="footer">
            <p>本报告由自动分析系统生成 | 数据来源：百度搜索、搜狗搜索</p>
        </div>
    </div>
</body>
</html>
        """
    
    def _generate_summary_section(self, report_data: Dict[str, Any]) -> str:
        """生成摘要部分"""
        summary = report_data.get("summary", {})
        key_insights = summary.get("key_insights", [])
        main_topics = summary.get("main_topics", [])
        recommendations = summary.get("recommendations", [])
        
        html = """
        <div class="summary-box">
            <h3>核心洞察</h3>
            <ul class="key-points">
        """
        
        for insight in key_insights[:5]:
            html += f"<li>{insight}</li>"
        
        html += """
            </ul>
        </div>
        
        <div class="chart-row">
            <div class="chart-item">
                <h3>主要话题</h3>
                <ul class="key-points">
        """
        
        for topic in main_topics[:3]:
            html += f"<li>{topic}</li>"
        
        html += """
                </ul>
            </div>
            
            <div class="chart-item">
                <h3>初步建议</h3>
                <ul class="key-points">
        """
        
        for rec in recommendations[:3]:
            html += f"<li>{rec}</li>"
        
        html += """
                </ul>
            </div>
        </div>
        """
        
        return html
    
    def _generate_content_sections(self, report_data: Dict[str, Any], charts_data: Dict[str, Any]) -> str:
        """生成内容部分"""
        chapters = report_data.get("chapters", [])
        html = ""
        
        for i, chapter in enumerate(chapters, 1):
            chapter_title = chapter.get("title", f"章节 {i}")
            chapter_content = chapter.get("content", "")
            chapter_data = chapter.get("data", {})
            
            html += f"""
            <div class="section">
                <h3>{i}. {chapter_title}</h3>
                <p>{chapter_content}</p>
            """
            
            # 添加章节特定的数据表格
            if chapter_data:
                html += self._generate_data_table(chapter_data, chapter_title)
            
            html += "</div>"
        
        return html
    
    def _generate_data_table(self, data: Dict[str, Any], title: str) -> str:
        """生成数据表格"""
        if not data:
            return ""
        
        html = f"""
        <h4>{title} - 数据概览</h4>
        <table class="data-table">
            <thead>
                <tr>
                    <th>指标</th>
                    <th>数值</th>
                    <th>说明</th>
                </tr>
            </thead>
            <tbody>
        """
        
        for key, value in data.items():
            if isinstance(value, (int, float, str)):
                html += f"""
                <tr>
                    <td>{key}</td>
                    <td>{value}</td>
                    <td>-</td>
                </tr>
                """
            elif isinstance(value, dict):
                description = value.get('description', '-')
                actual_value = value.get('value', value)
                html += f"""
                <tr>
                    <td>{key}</td>
                    <td>{actual_value}</td>
                    <td>{description}</td>
                </tr>
                """
        
        html += """
            </tbody>
        </table>
        """
        
        return html
    
    def _generate_charts_section(self, charts_data: Dict[str, Any]) -> str:
        """生成图表部分"""
        html = ""
        
        for chapter_name, chapter_charts in charts_data.items():
            if not chapter_charts:
                continue
                
            html += f"""
            <div class="section">
                <h3>{chapter_name} - 可视化分析</h3>
                <div class="chart-row">
            """
            
            for chart_name, chart_data in chapter_charts.items():
                if chart_data and "html" in chart_data:
                    html += f"""
                    <div class="chart-item">
                        <div class="chart-container">
                            {chart_data["html"]}
                        </div>
                    </div>
                    """
            
            html += """
                </div>
            </div>
            """
        
        return html
    
    def _generate_conclusion_section(self, report_data: Dict[str, Any]) -> str:
        """生成结论部分"""
        summary = report_data.get("summary", {})
        recommendations = summary.get("recommendations", [])
        data_quality = summary.get("data_quality", {})
        
        html = """
        <div class="summary-box">
            <h3>主要发现</h3>
            <ul class="key-points">
        """
        
        for rec in recommendations:
            html += f"<li>{rec}</li>"
        
        html += """
            </ul>
        </div>
        
        <div class="chart-row">
            <div class="chart-item">
                <h3>数据质量评估</h3>
                <table class="data-table">
                    <tbody>
        """
        
        for metric, value in data_quality.items():
            html += f"""
                    <tr>
                        <td>{metric}</td>
                        <td>{value}</td>
                    </tr>
            """
        
        html += """
                    </tbody>
                </table>
            </div>
            
            <div class="chart-item">
                <h3>后续建议</h3>
                <ul class="key-points">
                    <li>持续关注行业动态和政策变化</li>
                    <li>定期更新数据分析模型</li>
                    <li>扩展数据来源提高分析准确性</li>
                    <li>结合实际业务场景验证分析结果</li>
                </ul>
            </div>
        </div>
        """
        
        return html
    
    def generate_chapter_preview(self, chapter_data: Dict[str, Any], charts: Dict[str, Any]) -> str:
        """
        生成章节预览HTML
        
        Args:
            chapter_data: 章节数据
            charts: 章节图表
            
        Returns:
            预览HTML内容
        """
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>章节预览 - {chapter_data.get('title', '未知章节')}</title>
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
            <style>
                body {{ font-family: Arial, sans-serif; padding: 20px; }}
                .chapter {{ margin-bottom: 30px; }}
                .chart {{ margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="chapter">
                <h1>{chapter_data.get('title', '未知章节')}</h1>
                <p>{chapter_data.get('content', '')}</p>
            </div>
        """
        
        for chart_name, chart_data in charts.items():
            if chart_data and "html" in chart_data:
                html += f"""
                <div class="chart">
                    {chart_data["html"]}
                </div>
                """
        
        html += """
        </body>
        </html>
        """
        
        return html
    
    def save_chapter_preview(self, chapter_data: Dict[str, Any], charts: Dict[str, Any], filename: str) -> str:
        """
        保存章节预览
        
        Args:
            chapter_data: 章节数据
            charts: 章节图表
            filename: 文件名
            
        Returns:
            保存的文件路径
        """
        preview_html = self.generate_chapter_preview(chapter_data, charts)
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(preview_html)
        
        return filepath
