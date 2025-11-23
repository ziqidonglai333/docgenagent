"""
Streamlit用户界面 - 自动分析报告生成系统
"""

import streamlit as st
import sys
import os
import json
import tempfile
from pathlib import Path

# 添加项目路径到系统路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.workflow_orchestrator import WorkflowOrchestrator
from modules.report_generator.html_generator import HTMLGenerator
from config.settings import REPORT_CONFIG


class AnalysisReportApp:
    """分析报告生成应用类"""
    
    def __init__(self):
        self.workflow = WorkflowOrchestrator()
        self.html_generator = HTMLGenerator()
        self._initialize_session_state()
    
    def _initialize_session_state(self):
        """初始化会话状态"""
        if 'current_step' not in st.session_state:
            st.session_state.current_step = 1
        if 'report_title' not in st.session_state:
            st.session_state.report_title = ""
        if 'search_keywords' not in st.session_state:
            st.session_state.search_keywords = ""
        if 'toc_generated' not in st.session_state:
            st.session_state.toc_generated = False
        if 'toc_data' not in st.session_state:
            st.session_state.toc_data = []
        if 'chapters_data' not in st.session_state:
            st.session_state.chapters_data = {}
        if 'charts_data' not in st.session_state:
            st.session_state.charts_data = {}
        if 'current_chapter_index' not in st.session_state:
            st.session_state.current_chapter_index = 0
        if 'report_generated' not in st.session_state:
            st.session_state.report_generated = False
        if 'report_path' not in st.session_state:
            st.session_state.report_path = ""
    
    def run(self):
        """运行应用"""
        st.title("📊 自动分析报告生成系统")
        st.markdown("---")
        
        # 显示进度条
        self._show_progress()
        
        # 根据当前步骤显示相应界面
        if st.session_state.current_step == 1:
            self._step1_generate_toc()
        elif st.session_state.current_step == 2:
            self._step2_generate_chapters()
        elif st.session_state.current_step == 3:
            self._step3_generate_final_report()
    
    def _show_progress(self):
        """显示进度条"""
        steps = ["生成目录", "生成章节", "合稿报告"]
        current_step = st.session_state.current_step
        
        # 创建进度条
        progress = current_step / 3.0
        st.progress(progress)
        
        # 显示步骤标签
        cols = st.columns(3)
        for i, step in enumerate(steps):
            with cols[i]:
                if i + 1 == current_step:
                    st.markdown(f"**🔵 {step}**")
                elif i + 1 < current_step:
                    st.markdown(f"✅ {step}")
                else:
                    st.markdown(f"⚪ {step}")
    
    def _step1_generate_toc(self):
        """步骤1：生成目录"""
        st.header("第一步：生成报告目录")
        
        # 输入表单
        with st.form("report_config"):
            col1, col2 = st.columns(2)
            
            with col1:
                report_title = st.text_input(
                    "报告标题",
                    value=st.session_state.report_title,
                    placeholder="请输入分析报告标题，如：人工智能行业分析报告"
                )
            
            with col2:
                search_keywords = st.text_input(
                    "搜索关键词",
                    value=st.session_state.search_keywords,
                    placeholder="请输入搜索关键词，用逗号分隔"
                )
            
            # 报告类型选择
            report_type = st.selectbox(
                "报告类型",
                options=["行业分析", "市场研究", "技术评估", "竞争分析", "综合报告"],
                index=0
            )
            
            # 搜索深度
            search_depth = st.slider(
                "搜索深度",
                min_value=1,
                max_value=5,
                value=3,
                help="控制搜索结果的深度和数量"
            )
            
            submitted = st.form_submit_button("生成目录")
        
        if submitted:
            if not report_title or not search_keywords:
                st.error("请填写报告标题和搜索关键词")
                return
            
            # 保存到会话状态
            st.session_state.report_title = report_title
            st.session_state.search_keywords = search_keywords
            
            # 生成目录
            with st.spinner("正在生成目录结构..."):
                try:
                    toc_data = self.workflow.generate_table_of_contents(
                        report_title,
                        search_keywords,
                        report_type,
                        search_depth
                    )
                    
                    if toc_data:
                        st.session_state.toc_data = toc_data
                        st.session_state.toc_generated = True
                        st.success("目录生成成功！")
                    else:
                        st.error("目录生成失败，请重试")
                        
                except Exception as e:
                    st.error(f"生成目录时出错: {str(e)}")
        
        # 显示生成的目录
        if st.session_state.toc_generated:
            st.subheader("生成的目录结构")
            
            for i, chapter in enumerate(st.session_state.toc_data):
                with st.expander(f"第{i+1}章: {chapter.get('title', '')}", expanded=True):
                    st.write(chapter.get('description', ''))
                    
                    # 显示子章节
                    subsections = chapter.get('subsections', [])
                    if subsections:
                        st.write("**子章节:**")
                        for j, subsection in enumerate(subsections):
                            st.write(f"  {j+1}. {subsection}")
            
            # 目录确认和编辑
            st.subheader("目录确认")
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("✅ 确认目录，进入下一步", type="primary"):
                    st.session_state.current_step = 2
                    st.rerun()
            
            with col2:
                if st.button("🔄 重新生成目录"):
                    st.session_state.toc_generated = False
                    st.rerun()
    
    def _step2_generate_chapters(self):
        """步骤2：生成各章节内容"""
        st.header("第二步：生成章节内容")
        
        if not st.session_state.toc_data:
            st.error("请先完成第一步生成目录")
            return
        
        total_chapters = len(st.session_state.toc_data)
        current_idx = st.session_state.current_chapter_index
        
        if current_idx >= total_chapters:
            st.session_state.current_step = 3
            st.rerun()
            return
        
        current_chapter = st.session_state.toc_data[current_idx]
        
        st.subheader(f"第{current_idx + 1}章: {current_chapter.get('title', '')}")
        st.write(f"**章节描述:** {current_chapter.get('description', '')}")
        
        # 显示进度
        progress = (current_idx + 1) / total_chapters
        st.progress(progress)
        st.write(f"进度: {current_idx + 1}/{total_chapters}")
        
        # 检查是否已生成该章节
        chapter_key = f"chapter_{current_idx}"
        
        if chapter_key not in st.session_state.chapters_data:
            # 生成章节内容
            if st.button(f"生成第{current_idx + 1}章内容", type="primary"):
                with st.spinner(f"正在生成第{current_idx + 1}章内容..."):
                    try:
                        # 搜索和分析数据
                        search_results = self.workflow.search_engine.search(
                            st.session_state.search_keywords,
                            chapter_title=current_chapter.get('title', ''),
                            max_results=10
                        )
                        
                        # 处理数据
                        processed_data = self.workflow.data_processor.process_search_results(search_results)
                        
                        # 生成图表
                        charts = self.workflow.chart_generator.generate_charts(
                            current_chapter.get('title', ''),
                            search_results
                        )
                        
                        # 生成章节内容
                        chapter_content = self.workflow.generate_chapter_content(
                            current_chapter,
                            processed_data,
                            search_results
                        )
                        
                        # 保存到会话状态
                        st.session_state.chapters_data[chapter_key] = {
                            'title': current_chapter.get('title', ''),
                            'content': chapter_content,
                            'data': processed_data
                        }
                        st.session_state.charts_data[chapter_key] = charts
                        
                        st.success(f"第{current_idx + 1}章内容生成成功！")
                        
                    except Exception as e:
                        st.error(f"生成章节内容时出错: {str(e)}")
        else:
            # 显示已生成的章节内容
            chapter_data = st.session_state.chapters_data[chapter_key]
            charts_data = st.session_state.charts_data[chapter_key]
            
            st.subheader("章节内容")
            st.write(chapter_data['content'])
            
            # 显示图表
            if charts_data:
                st.subheader("数据图表")
                for chart_name, chart_data in charts_data.items():
                    if chart_data and 'html' in chart_data:
                        st.components.v1.html(chart_data['html'], height=400)
            
            # 章节操作按钮
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("✅ 确认本章节", type="primary"):
                    st.session_state.current_chapter_index += 1
                    st.rerun()
            
            with col2:
                if st.button("🔄 重新生成本章"):
                    del st.session_state.chapters_data[chapter_key]
                    if chapter_key in st.session_state.charts_data:
                        del st.session_state.charts_data[chapter_key]
                    st.rerun()
            
            with col3:
                if st.button("⏮️ 返回上一步"):
                    st.session_state.current_step = 1
                    st.rerun()
    
    def _step3_generate_final_report(self):
        """步骤3：生成最终报告"""
        st.header("第三步：生成最终报告")
        
        if not st.session_state.chapters_data:
            st.error("请先完成所有章节的生成")
            return
        
        # 准备报告数据
        report_data = {
            "title": st.session_state.report_title,
            "summary": self._generate_report_summary(),
            "chapters": []
        }
        
        charts_data = {}
        
        # 整理章节数据
        for i in range(len(st.session_state.toc_data)):
            chapter_key = f"chapter_{i}"
            if chapter_key in st.session_state.chapters_data:
                chapter_data = st.session_state.chapters_data[chapter_key]
                report_data["chapters"].append(chapter_data)
                
                if chapter_key in st.session_state.charts_data:
                    charts_data[chapter_data['title']] = st.session_state.charts_data[chapter_key]
        
        # 生成最终报告
        if not st.session_state.report_generated:
            if st.button("📄 生成最终报告", type="primary"):
                with st.spinner("正在生成最终报告..."):
                    try:
                        report_path = self.html_generator.generate_report(report_data, charts_data)
                        st.session_state.report_path = report_path
                        st.session_state.report_generated = True
                        st.success("报告生成成功！")
                    except Exception as e:
                        st.error(f"生成报告时出错: {str(e)}")
        
        # 显示报告预览和下载
        if st.session_state.report_generated and st.session_state.report_path:
            st.subheader("报告预览")
            
            # 在iframe中显示报告
            try:
                with open(st.session_state.report_path, 'r', encoding='utf-8') as f:
                    report_html = f.read()
                
                st.components.v1.html(report_html, height=800, scrolling=True)
            except Exception as e:
                st.error(f"显示报告预览时出错: {str(e)}")
            
            # 下载按钮
            st.subheader("下载报告")
            with open(st.session_state.report_path, 'r', encoding='utf-8') as f:
                report_content = f.read()
            
            st.download_button(
                label="📥 下载HTML报告",
                data=report_content,
                file_name=os.path.basename(st.session_state.report_path),
                mime="text/html"
            )
        
        # 重置和重新开始按钮
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 重新开始", type="secondary"):
                self._reset_application()
                st.rerun()
        
        with col2:
            if st.button("⏮️ 返回上一步"):
                st.session_state.current_step = 2
                st.session_state.current_chapter_index = len(st.session_state.toc_data) - 1
                st.rerun()
    
    def _generate_report_summary(self):
        """生成报告摘要"""
        summary = {
            "key_insights": [],
            "main_topics": [],
            "data_quality": {
                "coverage": "良好",
                "diversity": "丰富", 
                "relevance": "高"
            },
            "recommendations": [
                "基于数据分析，行业呈现积极发展态势",
                "建议关注技术发展趋势和市场变化",
                "持续优化分析模型以提高预测准确性"
            ]
        }
        
        # 从各章节数据中提取关键洞察
        for i in range(len(st.session_state.toc_data)):
            chapter_key = f"chapter_{i}"
            if chapter_key in st.session_state.chapters_data:
                chapter_data = st.session_state.chapters_data[chapter_key]
                summary["key_insights"].append(
                    f"{chapter_data['title']}: 已完成分析"
                )
                summary["main_topics"].append(chapter_data['title'])
        
        return summary
    
    def _reset_application(self):
        """重置应用程序状态"""
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        self._initialize_session_state()


def main():
    """主函数"""
    app = AnalysisReportApp()
    app.run()


if __name__ == "__main__":
    main()
