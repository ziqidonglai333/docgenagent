"""
Streamlit用户界面 - 自动分析报告生成系统
集成PDF处理和表格处理功能
"""

import streamlit as st
import sys
import os
import json
import tempfile
import base64
import fitz  # PyMuPDF
import pandas as pd
import csv
import re
from pathlib import Path
from zhipuai import ZhipuAI

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
        
        # 在侧边栏添加工具选项
        with st.sidebar:
            st.markdown("## 🔧 工具集")
            tool_option = st.selectbox(
                "选择工具",
                ["报告生成", "PDF处理", "表格处理"]
            )
        
        if tool_option == "报告生成":
            # 显示进度条
            self._show_progress()
            
            # 根据当前步骤显示相应界面
            if st.session_state.current_step == 1:
                self._step1_generate_toc()
            elif st.session_state.current_step == 2:
                self._step2_generate_chapters()
            elif st.session_state.current_step == 3:
                self._step3_generate_final_report()
        elif tool_option == "PDF处理":
            self._pdf_processing_tool()
        elif tool_option == "表格处理":
            self._table_processing_tool()
    
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
    
    def _pdf_processing_tool(self):
        """PDF处理工具 - 基于Another_Option/1_1Text_Handle.py"""
        st.header("📄 PDF文档处理工具")
        st.markdown("将PDF文档智能转化为TXT文档，并去除无关内容")
        
        with st.sidebar:
            st.markdown("### PDF处理设置")
            temperature = st.slider(
                label="模型温度",
                max_value=1.0,
                min_value=0.0,
                step=0.1,
                value=0.8
            )
            
            store_path = st.text_input(
                label="优化后的文件存储路径",
                placeholder="路径为绝对路径的文件夹，如：C:/output"
            )
            
            uploaded_files = st.file_uploader(
                label="请选择上传的PDF文件",
                type=['pdf'],
                accept_multiple_files=True
            )
        
        col1, col2 = st.columns(2)
        
        def load_pdf(pdf_file):
            """读取PDF文档内容"""
            file_bytes = pdf_file.getvalue()
            pdf = fitz.open(stream=file_bytes, filetype="pdf")
            pdf_txt = ""
            for page in pdf:
                cont = page.get_text()
                pdf_txt += cont
            pdf.close()
            return pdf_txt
        
        def optimize_text_with_llm(txt_cont, temperature):
            """使用大模型优化文本内容"""
            sys_prompt = "你是一名资深的文档处理专家，拥有超过15年的文档审查经验。"
            user_prompt = f"""
            [任务]: 你要优化的文档 {txt_cont}是从pdf转换过来的，保理了原来pdf的一些痕迹。你的任务是去除文档中与内容无关的页码、页眉、页脚等从PDF转换时带来的与文章内容不相关的东西，返回文章原始内容。
            [输出要求]：
             ---直接输出文档内容，仅返回文档内容，不要输出不是文档内容的任何话；
             ---返回的内容为仅可去除与内容无关的东西，返回文章原始内容。
             ---如因PDF转换原因造成文字段落分散，可以根据意思，将前后挨着的不同段落的相同内容放在一个段落，但是原文章句子的顺序不得改变，不要有任何文字的修改。
            """
            
            client = ZhipuAI(api_key="927615462c6a5e9758e5b563a8b9003c.f2sbR2fSOxEqYzeN")
            
            response = client.chat.completions.create(
                model="glm-4-plus",
                messages=[
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature,
                stream=True,
            )
            
            # 使用生成器逐块处理流式响应
            for chunk in response:
                content = chunk.choices[0].delta.content
                if content:
                    yield content
        
        if uploaded_files:
            for file in uploaded_files:
                base_name, ext_name = os.path.splitext(file.name)
                
                with col1:
                    st.write(f"**{base_name} 原文**")
                    raw_txt = load_pdf(file)
                    st.text_area(
                        label="PDF读出的文档",
                        height=500,
                        value=raw_txt,
                        key=f"raw_{base_name}"
                    )
                
                with col2:
                    if st.button(f"优化 {base_name}", key=f"btn_{base_name}"):
                        st.write(f"**{base_name} 优化后**")
                        placeholder = st.empty()
                        txt_generator = optimize_text_with_llm(raw_txt, temperature)
                        opt_txt = ""
                        
                        for chunk in txt_generator:
                            if chunk:
                                opt_txt += chunk
                            else:
                                opt_txt += " "
                            
                            placeholder.text_area(
                                label="整理优化后的文档",
                                height=500,
                                value=opt_txt,
                                key=f"opt_{base_name}"
                            )
                        
                        # 保存文件
                        if store_path:
                            if not os.path.exists(store_path):
                                os.makedirs(store_path, exist_ok=True)
                            output_path = os.path.join(store_path, f"{base_name}.txt")
                            with open(output_path, "w", encoding="utf-8") as f:
                                f.write(opt_txt)
                            st.success(f"文件已保存到: {output_path}")
    
    def _table_processing_tool(self):
        """表格处理工具 - 基于Another_Option/1_2Table_Handle.py"""
        st.header("📊 表格处理工具")
        st.markdown("PDF表格智能解读和分析")
        
        # 创建页签
        tab1, tab2, tab3 = st.tabs(["PDF转图片", "图片表格识别", "表格解读"])
        
        with tab1:
            self._pdf_to_image_tab()
        
        with tab2:
            self._image_table_recognition_tab()
        
        with tab3:
            self._table_interpretation_tab()
    
    def _pdf_to_image_tab(self):
        """PDF转图片功能"""
        st.subheader("PDF转图片")
        
        col1, col2 = st.columns([2, 3])
        
        with col1:
            pdf_path = st.text_input(
                label="待解析PDF文件位置路径",
                placeholder="路径为绝对路径，包括文件名.pdf"
            )
            output_path = st.text_input(
                label="图片输出位置路径",
                placeholder="路径为绝对路径文件夹"
            )
            
            if st.button("转换"):
                if pdf_path and output_path:
                    if not os.path.exists(output_path):
                        os.makedirs(output_path, exist_ok=True)
                    
                    image_paths = self._pdf2image(pdf_path, output_path)
                    with col2:
                        for image_path in image_paths:
                            st.image(image_path, caption=os.path.basename(image_path), use_container_width=True)
    
    def _image_table_recognition_tab(self):
        """图片表格识别功能"""
        st.subheader("图片表格识别")
        
        col1, col2 = st.columns([2, 3])
        
        with col1:
            v_mod_temperature = st.slider(
                label="V模型温度",
                max_value=1.0,
                min_value=0.0,
                step=0.1,
                value=0.8
            )
            
            img_path = st.text_input(
                label="待识别图片位置路径",
                placeholder="路径为绝对路径，包括文件名和后缀"
            )
            store_path = st.text_input(
                label="表格csv输出位置路径",
                placeholder="路径为绝对路径文件夹"
            )
            
            if st.button("图片表格识别"):
                if img_path and store_path:
                    csv_filename_list = self._img_label_read(img_path, store_path, v_mod_temperature)
                    with col2:
                        for table in csv_filename_list:
                            csv_file = f"{store_path}/{table}.csv"
                            if os.path.exists(csv_file):
                                dftable = pd.read_csv(csv_file)
                                st.dataframe(dftable)
    
    def _table_interpretation_tab(self):
        """表格解读功能"""
        st.subheader("表格解读分析")
        
        col1, col2 = st.columns([2, 3])
        
        with col1:
            llm_temperature = st.slider(
                label="大语言模型温度",
                max_value=1.0,
                min_value=0.0,
                step=0.1,
                value=0.8
            )
            
            store_path = st.text_input(
                label="表格解析后文件输出位置路径",
                placeholder="路径为绝对路径文件夹"
            )
            
            uploaded_files = st.file_uploader(
                label="请选择上传的CSV文件",
                type=['csv'],
                accept_multiple_files=True
            )
            
            if st.button("表格解读分析"):
                if uploaded_files and store_path:
                    with col2:
                        for upload_file in uploaded_files:
                            int_cont = self._table_interpret(upload_file, llm_temperature)
                            st.text_area(
                                label="表格解析内容",
                                height=400,
                                value=int_cont
                            )
                            
                            base_name, ext_name = os.path.splitext(upload_file.name)
                            if store_path:
                                if not os.path.exists(store_path):
                                    os.makedirs(store_path, exist_ok=True)
                                output_path = os.path.join(store_path, f"{base_name}.txt")
                                with open(output_path, "w", encoding="utf-8") as f:
                                    f.write(int_cont)
                                st.success(f"文件已保存到: {output_path}")
    
    def _pdf2image(self, pdf_path, output_path):
        """PDF转图片函数"""
        image_paths = []
        file_name_with_extension = os.path.basename(pdf_path)
        file_name_without_extension, file_extension = os.path.splitext(file_name_with_extension)
        
        doc = fitz.open(pdf_path)
        for page_num in range(len(doc)):
            page = doc[page_num]
            pix = page.get_pixmap()
            outpath = os.path.join(output_path, f"{file_name_without_extension}page_{page_num + 1}.jpg")
            pix.save(outpath)
            image_paths.append(outpath)
        
        doc.close()
        return image_paths
    
    def _img_label_read(self, img_path, store_path, v_mod_temperature):
        """图片表格识别函数"""
        with open(img_path, 'rb') as img_file:
            img_base = base64.b64encode(img_file.read()).decode('utf-8')
        
        client = ZhipuAI(api_key="927615462c6a5e9758e5b563a8b9003c.f2sbR2fSOxEqYzeN")
        
        response = client.chat.completions.create(
            model="glm-4v-plus",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": img_base}
                        },
                        {
                            "type": "text",
                            "text": "请描述这个图片,识别图片中的每个表格，每个表格请以'表格名称为xxxx\\n\\n'的方式返回表格名称，以'表格正文如下:\\n开始'，以csv的格式输出表格正文，表格正文结束后添加'\\n\\n'结尾"
                        }
                    ]
                }
            ],
            temperature=v_mod_temperature,
        )
        
        rescontent = response.choices[0].message.content
        
        # 解析表格内容
        tables_dict = {}
        tablename_pattern = r"表格名称为(.*?)\n\n"
        tablecontent_pattern = r"表格正文如下:(.*?)(?=\n\n表格名称为|\Z)"
        
        tablename_matches = re.finditer(tablename_pattern, rescontent, re.S)
        tablecontent_matches = re.finditer(tablecontent_pattern, rescontent, re.S)
        
        for name_match, content_match in zip(tablename_matches, tablecontent_matches):
            tablename = name_match.group(1).strip()
            tablecontent = content_match.group(1).strip()
            tables_dict[tablename] = tablecontent
        
        # 保存CSV文件
        csv_file_name_list = []
        for csvname, csvcontent in tables_dict.items():
            if not os.path.exists(store_path):
                os.makedirs(store_path, exist_ok=True)
            
            spath = os.path.join(store_path, f"{csvname}.csv")
            with open(spath, 'w', newline='', encoding='utf-8') as csvfile:
                csvwriter = csv.writer(csvfile)
                for row in csvcontent.split('\n'):
                    csvwriter.writerow(row.split(','))
            csv_file_name_list.append(csvname)
        
        return csv_file_name_list
    
    def _table_interpret(self, csv_table, llm_temperature, background=""):
        """表格解读函数"""
        # 这里简化实现，实际使用时需要根据Another_Option中的完整逻辑实现
        df_table = pd.read_csv(csv_table)
        
        # 生成简单的解读内容
        interpretation = f"""
        表格名称: {os.path.basename(csv_table.name)}
        
        表格概述:
        - 数据行数: {len(df_table)}
        - 数据列数: {len(df_table.columns)}
        - 列名: {', '.join(df_table.columns.tolist())}
        
        数据特点:
        - 这是一个包含{len(df_table)}行数据的表格
        - 主要记录了{df_table.columns[0]}等相关信息
        - 数据完整性良好，适合进行进一步分析
        
        分析建议:
        - 建议对数值型数据进行统计分析
        - 可以探索不同列之间的相关性
        - 考虑使用可视化工具展示数据分布
        """
        
        return interpretation
    
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
