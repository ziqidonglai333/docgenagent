"""
数据处理器 - 处理和分析从搜索引擎获取的数据
集成大模型分析、知识库功能、PDF处理和表格提取
根据Another_Option思想进行修订
"""

import re
import json
import os
import io
import base64
import csv
import pickle
import math
from typing import List, Dict, Any, Tuple, Generator
from collections import Counter
import jieba
import jieba.analyse
import fitz  # PyMuPDF
import pandas as pd
from zhipuai import ZhipuAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from sentence_transformers import SentenceTransformer
import faiss
from langchain_community.document_loaders import DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter


class DataProcessor:
    """数据处理器类"""
    
    def __init__(self):
        # 初始化jieba分词
        jieba.initialize()
        
        # 初始化智谱AI客户端
        self.client = ZhipuAI(api_key="927615462c6a5e9758e5b563a8b9003c.f2sbR2fSOxEqYzeN")
        
        # 行业分析常用关键词
        self.industry_keywords = {
            "市场规模": ["规模", "市场", "容量", "产值", "营收"],
            "竞争格局": ["竞争", "对手", "市场份额", "市场集中度"],
            "发展趋势": ["趋势", "增长", "发展", "前景", "预测"],
            "技术发展": ["技术", "创新", "研发", "专利", "突破"],
            "政策环境": ["政策", "法规", "监管", "支持", "限制"]
        }
        
        # 初始化embedding模型
        self.embedding_model = SentenceTransformer("BAAI/bge-large-zh-v1.5")

    def _extract_all_text(self, search_results: List[Dict[str, Any]]) -> str:
        """提取所有搜索结果的文本内容"""
        all_text = ""
        for result in search_results:
            title = result.get('title', '')
            abstract = result.get('abstract', '')
            all_text += f"{title} {abstract} "
        return all_text

    def _extract_entities(self, text: str) -> Dict[str, List[str]]:
        """从文本中提取实体信息"""
        entities = {
            "companies": [],
            "products": [],
            "technologies": []
        }
        
        # 使用jieba提取关键词
        keywords = jieba.analyse.extract_tags(text, topK=50, withWeight=False)
        
        # 简单的实体分类（基于关键词匹配）
        for keyword in keywords:
            if len(keyword) >= 2:  # 过滤掉单个字符的关键词
                if any(char in keyword for char in ["公司", "集团", "企业", "有限"]):
                    entities["companies"].append(keyword)
                elif any(char in keyword for char in ["产品", "服务", "方案", "系统"]):
                    entities["products"].append(keyword)
                elif any(char in keyword for char in ["技术", "算法", "模型", "平台"]):
                    entities["technologies"].append(keyword)
        
        return entities

    def analyze_market_size(self, search_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """市场规模分析"""
        market_data = {
            "size_estimates": [],
            "growth_rates": [],
            "market_segments": []
        }
        
        all_text = self._extract_all_text(search_results)
        
        # 提取数字和单位信息
        size_patterns = [
            r"(\d+(?:\.\d+)?)\s*(亿元|亿元|亿美元|万美元|亿|万)",
            r"规模[约为]?\s*(\d+(?:\.\d+)?)\s*(亿元|亿元|亿美元|万美元|亿|万)",
            r"市场[规模容量][约为]?\s*(\d+(?:\.\d+)?)\s*(亿元|亿元|亿美元|万美元|亿|万)"
        ]
        
        for pattern in size_patterns:
            matches = re.findall(pattern, all_text)
            for match in matches:
                value, unit = match
                market_data["size_estimates"].append({
                    "value": float(value),
                    "unit": unit,
                    "source": "search_results"
                })
        
        # 提取增长率信息
        growth_patterns = [
            r"增长[率为]?\s*(\d+(?:\.\d+)?)%",
            r"增长率[约为]?\s*(\d+(?:\.\d+)?)%",
            r"同比增长[率为]?\s*(\d+(?:\.\d+)?)%"
        ]
        
        for pattern in growth_patterns:
            matches = re.findall(pattern, all_text)
            for match in matches:
                market_data["growth_rates"].append({
                    "rate": float(match),
                    "unit": "%",
                    "source": "search_results"
                })
        
        return market_data

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

    def analyze_trends(self, search_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """趋势分析"""
        trends_data = {
            "technological_trends": [],
            "market_trends": [],
            "regulatory_trends": []
        }
        
        all_text = self._extract_all_text(search_results)
        
        # 使用大模型进行趋势分析
        try:
            prompt = f"""
            请分析以下文本中提到的行业趋势，包括技术趋势、市场趋势和监管趋势：
            
            {all_text[:2000]}  # 限制文本长度
            
            请以JSON格式返回分析结果，包含以下字段：
            - technological_trends: 技术发展趋势列表
            - market_trends: 市场发展趋势列表  
            - regulatory_trends: 监管政策趋势列表
            """
            
            response = self.client.chat.completions.create(
                model="glm-4",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            
            analysis_result = response.choices[0].message.content
            # 这里可以添加JSON解析逻辑
            # trends_data.update(json.loads(analysis_result))
            
        except Exception as e:
            print(f"趋势分析失败: {e}")
        
        return trends_data

    def generate_insights(self, search_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成综合洞察"""
        insights = {
            "key_findings": [],
            "recommendations": [],
            "risks_opportunities": []
        }
        
        """
        利用大模型对表格进行解读
        
        Args:
            csv_table_path: CSV表格文件路径
            temperature: 模型温度
            background: 表格背景说明
            
        Returns:
            表格解读内容
        """
        try:
            # 实例化在线glm-4模型
            llm_line = ChatOpenAI(
                temperature=temperature,
                model="glm-4",
                openai_api_key="927615462c6a5e9758e5b563a8b9003c.f2sbR2fSOxEqYzeN",
                openai_api_base="https://open.bigmodel.cn/api/paas/v4/"
            )
            
            # 使用pandas的read_csv函数读取CSV文件
            df_table = pd.read_csv(csv_table_path)  
            
            # 解读表格的提示词
            intrepre_case = ''' 
            表格名称: 技术记录表
            时间, 人员名字, 测量次数, 备注
            2020.1.10, 张三, 1212, 
            2020.1.15, 李四, 2, 
            2020.2.3, 王五, 34, 
            2020.2.18, 赵六, 6,
            表格说明：
            这张表是记录了单位人员技术测量内容，主要记录了测量时间、人员姓名，测量次数等信息。
            经分析，共测量四次。时间角度看，1月测量2次，2月测量2次；测量人员共四人，每人测量一次，测量次数最多的是张三，测量1212次，测量次数最少的是李四测量2次。人员测量次数差异较大，每次测量次数波动较大，相关趋势不明显。
            '''
            interpret_prompt = ChatPromptTemplate(
                [
                    ("system","你对数据分析专家，拥有超过15年的数据分析经验，具备数据对比分析、趋势分析各类数据分析能力。"),
                    ("user", f"你的工作任务是对{df_table}进行描述和解读，这个表格的背景是{background}。解读要求为：首先列示表格，其次对表格表达的内容背景进行综合阐述，然后根据表格内容进行详细说明，最后根据表格数据特点进行分析描述。具体可参考解读示例{intrepre_case}")
                ]
            )
            output_parser = StrOutputParser()

            table_interpret_chain = interpret_prompt | llm_line | output_parser
            # 修正传递给invoke方法的键名
            return table_interpret_chain.invoke({"df_table": df_table.to_string(), "background": background})
        except Exception as e:
            print(f"表格解读失败: {e}")
            return f"表格解读失败: {str(e)}"

    # ==================== 报告框架生成功能 ====================
    
    def generate_report_catalogue(self, field: str, require: str, title: str, temperature: float = 0.8) -> Generator[str, None, None]:
        """
        生成报告目录结构
        
        Args:
            field: 所属领域
            require: 报告要求
            title: 报告标题
            temperature: 模型温度
            
        Returns:
            生成器，逐块返回报告目录
        """
        try:
            catalogue_gen_prompt = f"""
            [角色]:你是一名资深的{field}领域专家，拥有超过15年的行业经验。
            [任务]:作为一名专业人士，你的工作是首先理解用户的需求{require}，然后帮助用户撰写报告框架目录，具体按照[目录要求]写。
            [目录要求]：
               ---各级序号从大到小为:1、  1.1、   1.1.1、   1.1.1.1、   1.1.1.1.1，目录一般不超过五级；
               ---目录示例：1\\经营分析  1.1\\财务分析  1.1.1\\利润分析；
               ---在每个最下级目录下，写本目录主要撰写哪几点内容，以"撰写内容包括："为开始，具体参考[目录模板]
            [目录模板]：
                1\\总述  
                   1.1\\报告目的与背景
                   撰写内容包括：报告撰写的目的、报告撰写的背景
                   1.2\\报告时间范围与数据来源
                   撰写内容包括：描述本次报告属于哪个经营期间，以及相关数据从哪里获取
                   1.3\\公司概述  
                   撰写内容包括：公司成立时间、人数、所属行业等基本情况
            
                2\\经营概况  
                   2.1\\经营成果概述  
                      2.1.1\\主要财务数据概览  
                      撰写内容包括：利润总额、营业收入、成本、
                      2.1.2\\主要经营指标概览  
                      撰写内容包括：xx区域销售回款、重大项目进度情况...
                      ......
                ......           
                """    
            user_prompt = f"请根据标题{title}，撰写包括框架目录。要求：直接输出框架目录，不要输出任何与框架目录无关的文字，别瞎BB。"
            
            response = self.client.chat.completions.create(
                model="glm-4-plus",
                messages=[
                    {"role": "system", "content": catalogue_gen_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature,
                stream=True,
            )
            
            # 使用生成器逐块处理流式响应
            for chunk in response:
                content = chunk.choices[0].delta.content
                yield content
        except Exception as e:
            print(f"报告目录生成失败: {e}")
            yield f"报告目录生成失败: {str(e)}"

    def parse_report_framework(self, schemeframe: str, field: str, temperature: float = 0.8) -> Generator[str, None, None]:
        """
        解析报告框架为段落
        
        Args:
            schemeframe: 报告框架
            field: 所属领域
            temperature: 模型温度
            
        Returns:
            生成器，逐块返回解析结果
        """
        try:
            sys_prompt = f"""你是一名资深的{field}领域专家，拥有超过15年的行业经验。"""    
            user_prompt =  f"""你任务是的根据专业报告的框架{schemeframe}，针对每个报告的段落，生成解析语句，详见[解析要求]，参考[解析示例]。
                [解析要求]：
                 ---报告框架中每个"撰写内容包括："字样后的话，根据上下文意思解析为一个或多个段落。
                 ---以"段落名称为："开始，每个段落名称用","分割，结束后不要加任何标点符号。
                 ---解析的段落名称要根据上下文语义补充称完整的名称，即时单看段落名，也表述完整。例如：人口情况，可以根据上下文解析为经开区人口情况。补充完整的目的是为了根据段落名进行知识检索。
                 ---全部段落解析完后，增加解析后的报告模板，解析后的报告模板是：在原模版中，把"撰写内容包括："字样去掉，保理每个段落名称，每个段落名称后面增加"{{段落名称}}"，以"解析后的报告模版："为开头，换行输出。
                 ---直接输出段落解析内容和解析后的报告模版，不要说其他任何废话。
                 
                 [解析示例]：
                 报告框架如下：
                    1\\总述
                       1.1\\报告目的与背景
                       撰写内容包括：报告撰写的目的、报告撰写的背景
                       1.2\\区域概述
                       撰写内容包括：郑州经济开发区的地理位置、面积、人口、经济发展现状等基本情况
                    
                    2\\发展现状分析
                       2.1\\经济基础分析
                          2.1.1\\GDP及增长率
                          撰写内容包括：近年GDP总量及增长率
                      
                    3\\发展规划
                       3.1\\总体发展目标
                          3.1.1\\经济目标
                          撰写内容包括：未来GDP目标、产业结构优化目标
                    
                    对上面报告框架的解析如下：            
                    段落名称为：
                    报告撰写的目的,报告撰写的背景,郑州经济开发区的地理位置,郑州经济开发区的面积,郑州经济开发区的人口,郑州经济开发区的经济发展现状,郑州经济开发区近年GDP总量,郑州经济开发区近年GDP总量增长率,郑州经济开发区人口发展规划,郑州经济开发区就业率目标
                    
                    解析后的报告模版：
                    1\\总述
                       1.1\\报告目的与背景
                       报告撰写的目的{{报告撰写的目的}}、报告撰写的背景{{报告撰写的背景}}
                        1.2\\区域概述
                       郑州经济开发区的地理位置{{郑州经济开发区的地理位置}}、郑州经济开发区的面积{{郑州经济开发区的面积}}、郑州经济开发区的人口{{郑州经济开发区的人口}}、郑州经济开发区的经济发展现状{{郑州经济开发区的经济发展现状}}
                    2\\发展现状分析
                       2.1\\经济基础分析
                          2.1.1\\GDP及增长率
                          郑州经济开发区近年GDP总量{{郑州经济开发区近年GDP总量}}、郑州经济开发区近年GDP总量增长率{{郑州经济开发区近年GDP总量增长率}}            
                     3\\发展规划
                        3.1\\总体发展目标
                          3.1.1\\经济目标
                          郑州经济开发区人口发展规划{{郑州经济开发区人口发展规划}}、郑州经济开发区就业率目标{{郑州经济开发区就业率目标}}
                    ......
                    ......
                    """    
            # 调用大模型进行结构解析
            response = self.client.chat.completions.create(
                model="glm-4-long",
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
                yield content
        except Exception as e:
            print(f"报告框架解析失败: {e}")
            yield f"报告框架解析失败: {str(e)}"

    # ==================== 知识库检索功能 ====================
    
    def knowledge_retrieve(self, faiss_path: str, txt_path: str, squery: str, k: int = 5) -> str:
        """
        知识库搜索功能，根据检索结果回答问题
        
        Args:
            faiss_path: 向量数据库文件路径
            txt_path: 切割文本数据文件路径
            squery: 需要搜索的问题
            k: 检索结果数量
            
        Returns:
            检索结果文本
        """
        try:
            # 初始化embedding模型
            embedding_model = SentenceTransformer("BAAI/bge-large-zh-v1.5")
            
            faiss_db = faiss.read_index(faiss_path)
            retr = faiss_db.search(embedding_model.encode(squery), k)
            
            dist = retr[0]
            index = retr[1]
            
            retre_result = ""
            with open(txt_path, "rb") as f:
                contents = pickle.load(f)
            for i in index[0]:
                xx = contents[i] + "\n\n"
                retre_result = retre_result + xx
            return retre_result
        except Exception as e:
            print(f"知识库检索失败: {e}")
            return f"知识库检索失败: {str(e)}"

    def generate_paragraph(self, field: str, title: str, scheme: str, paragraph: str, 
                         retrie_result: str, temperature: float = 0.8) -> Generator[str, None, None]:
        """
        生成报告段落内容
        
        Args:
            field: 所属领域
            title: 报告标题
            scheme: 报告大纲
            paragraph: 段落标题
            retrie_result: 检索结果
            temperature: 模型温度
            
        Returns:
            生成器，逐块返回段落内容
        """
        try:
            sys_prompt = f"""你是一名资深的{field}领域专家，拥有超过15年的行业经验。"""    
            user_prompt =  f"""
            [任务]
            你任务是的根据专业报告主题{title}，结合专业报告的整体大纲{scheme}，完成专业报告段落{paragraph}的内容的编写。
            [技能]
                ---数据分析：从数据中提炼关键洞察并进行深入分析。
                ---深度洞察：识别领域中的问题与亮点，并提出专业意见和评论。
            [思考过程]
            "
            [目标]："<段落标题>"；
            [思考]："<
            **思考步骤1：步骤名称**
            对段落标题的的详细思考和分析；
            **思考步骤2：步骤名称**
            完成标题内容需要的数据分析、供参考的检索的知识是否充足，不足的部分你的自有知识是否充足，需要从外部补充哪些额外知识
            **思考步骤n:步骤名称**
            该步骤的推理和思考内容
            **最终思考**
            最终的结果或结论>"
            "
            [编写要求]
                 ---请结合检索已知的{retrie_result}内容；
                 ---必要时可根据你自己的知识，在使用你自有的知识时，需标明'根据我已有经验......'，并将这些字体加黑、斜体显示；
                 ---针对缺少数据的内容，可以列好表格，将数据空着；
                 ---针对需要补充外部知识的地方，可以标明"需外部知识补充，请具体再由人工补充一下，需要补充完整如下内容框架：XXXXXXX"
                 ---请不要写大概、可能等模棱两可的语句；
                 ---以专业报告，正向行文的风格写。
            [输出]
            你"必须"使用Plaintext代码框，在每个输出前用Plaintext代码框展示你的思考过程，格式为:以[思考过程]四个字为开始，具体思考内容换行后输出。
            你"必须"以[段落内容]四个字为开始，具体段落内容编写换行后输出。
                        """   
            # 调用大模型进行文档优化
            response = self.client.chat.completions.create(
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
                yield content
        except Exception as e:
            print(f"段落生成失败: {e}")
            yield f"段落生成失败: {str(e)}"

    def replace_placeholders(self, content: str, replacements: Dict[str, str]) -> str:
        """
        替换占位符
        
        Args:
            content: 包含占位符的内容
            replacements: 替换字典
            
        Returns:
            替换后的内容
        """
        try:
            # 遍历替换字典
            for placeholder, value in replacements.items():
                # 替换占位符
                content = content.replace('{' + placeholder + '}', value)
                content = content.replace("\n\n", "\n")
            # 返回替换后的内容
            return content
        except Exception as e:
            print(f"占位符替换失败: {e}")
            return content

    def optimize_report(self, field: str, title: str, require: str, raw_report: str, 
                       optimized: str, optimizing: str, temperature: float = 0.8) -> Generator[str, None, None]:
        """
        优化报告内容
        
        Args:
            field: 所属领域
            title: 报告标题
            require: 报告要求
            raw_report: 原始报告
            optimized: 已优化的内容
            optimizing: 待优化的内容
            temperature: 模型温度
            
        Returns:
            生成器，逐块返回优化后的内容
        """
        try:
            sys_prompt = f"""你是一名资深的{field}领域专家，拥有超过15年的行业经验。"""    
            user_prompt =  f"""
            [任务]
            你任务是的根据专业报告主题{title}，结合对专业报告的要求{require}，根据专业报告整体内容{raw_report}和已经完成的优化内容{optimized}，继续完成对专业报告后续部分内容{optimizing}的优化。
            [技能]
                ---文字表达：精准的文字表达能力，能对报告进行精确表达。
                ---数据分析：从数据中提炼关键洞察并进行深入分析。
                ---深度洞察：识别领域中的问题与亮点，并提出专业意见和评论。
            [优化要求]
                
                 ---以专业报告，正向行文的风格写。
                 ---去除多余的空格，换行，空行等无效字符。
                 ---对表达重复的地方进行去重。
                 ---对前后矛盾的地方进行统一。
                 ---对欠缺的得分进行补充。
                 ---必要时可以修改各级标题。
                 ---对各级标题下，没有内容，缺乏必要的连接过渡的地方补充适当文字进行连接，确保文章的连贯性。
                 ---对以下三情况进行加黑、斜体表注，提示人工进行确认和修订：
                    1.对标明'根据我已有经验......'，并将这些字体加黑、斜体显示；
                    2.针对缺少数据的内容和表格，将数据继续空着，并将这些地方的上文加黑、斜体显示；
                    3.对标明"需外部知识补充，请具体再由人工补充一下，需要补充完整如下内容框架：XXXXXXX"的地方加黑、斜体显示
                 """   
            # 调用大模型进行文档优化
            response = self.client.chat.completions.create(
                model="glm-4-long",
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
                yield content
        except Exception as e:
            print(f"报告优化失败: {e}")
            yield f"报告优化失败: {str(e)}"
