#!/usr/bin/env python3
"""
自动分析报告生成程序 - 主程序入口
基于Streamlit + LangGraph + 国内搜索引擎
"""

import streamlit as st
import sys
import os

# 添加项目路径到系统路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.ui.streamlit_app import AnalysisReportApp

def main():
    """主程序入口"""
    st.set_page_config(
        page_title="自动分析报告生成系统",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # 创建应用实例
    app = AnalysisReportApp()
    app.run()
# 增加主文件入口
if __name__ == "__main__":
    main()
