"""
配置文件 - 系统设置和常量
"""

# 搜索引擎配置
SEARCH_ENGINE_CONFIG = {
    "baidu": {
        "search_url": "https://www.baidu.com/s",
        "params": {
            "wd": "",  # 搜索关键词
            "rn": 50,  # 每页结果数
        },
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
    },
    "sogou": {
        "search_url": "https://www.sogou.com/web",
        "params": {
            "query": "",  # 搜索关键词
        },
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
    }
}

# 报告生成配置
REPORT_CONFIG = {
    "max_search_results": 20,
    "max_content_length": 10000,
    "chart_types": ["bar", "scatter"],
    "default_outline": [
        "第一章 行业概述",
        "第二章 市场规模分析", 
        "第三章 竞争格局分析",
        "第四章 技术发展趋势",
        "第五章 市场机遇与挑战",
        "第六章 发展建议"
    ]
}

# 工作流状态定义
WORKFLOW_STATES = {
    "INITIAL": "initial",
    "SEARCHING": "searching", 
    "OUTLINE_GENERATED": "outline_generated",
    "OUTLINE_APPROVED": "outline_approved",
    "CONTENT_GENERATING": "content_generating",
    "CONTENT_APPROVED": "content_approved",
    "COMPILING": "compiling",
    "COMPLETED": "completed"
}

# 图表配置
CHART_CONFIG = {
    "bar_chart": {
        "width": 800,
        "height": 500,
        "template": "plotly_white"
    },
    "scatter_chart": {
        "width": 800, 
        "height": 500,
        "template": "plotly_white"
    }
}
