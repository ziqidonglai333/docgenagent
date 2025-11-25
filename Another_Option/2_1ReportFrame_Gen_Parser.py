# 导入依赖包
import os
import streamlit as st
from zhipuai import ZhipuAI
import pickle
import re

# *-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*

# 设置页面布局
st.set_page_config(page_title = "报告框架生成",
                   page_icon = "🛄",
                   layout= "wide",
                   initial_sidebar_state="expanded")

# st.markdown("# 报告框架生成——流式输出")

# *-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*

# 设置侧边栏
with st.sidebar:
    st.markdown("# 报告框架生成——流式输出")
    temperature = st.slider(label= "温度",
                        max_value=1.0,
                        min_value=0.0,
                        step= 0.1,
                        value= 0.8)
    st.write(temperature)

    catal_gen_button = st.button(label = "生成报告目录")
    del_catal_button = st.button(label = "清除目录内容")
    store_catal_button = st.button(label = "导出报告框架")
    st.divider()
    paragr_parser_button = st.button(label = "报告段落解析")
    extra_button = st.button(label = "提取段落和报告框架")
    store_catalparser_button = st.button(label = "导出报告解析")
    
client = ZhipuAI(api_key="927615462c6a5e9758e5b563a8b9003c.f2sbR2fSOxEqYzeN")

# *-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*

def catalogue_gene(field, require, title):

    catalogue_gen_prompt = f"""
    [角色]:你是一名资深的{field}领域专家，拥有超过15年的行业经验。
    [任务]:作为一名专业人士，你的工作是首先理解用户的需求{require}，然后帮助用户撰写报告框架目录，具体按照[目录要求]写。
    [目录要求]：
       ---各级序号从大到小为:1、  1.1、   1.1.1、   1.1.1.1、   1.1.1.1.1，目录一般不超过五级；
       ---目录示例：1\经营分析  1.1\财务分析  1.1.1\利润分析；
       ---在每个最下级目录下，写本目录主要撰写哪几点内容，以"撰写内容包括："为开始，具体参考[目录模板]
    [目录模板]：
        1\总述  
           1.1\报告目的与背景
           撰写内容包括：报告撰写的目的、报告撰写的背景
           1.2\报告时间范围与数据来源
           撰写内容包括：描述本次报告属于哪个经营期间，以及相关数据从哪里获取
           1.3\公司概述  
           撰写内容包括：公司成立时间、人数、所属行业等基本情况
    
        2\经营概况  
           2.1\经营成果概述  
              2.1.1\主要财务数据概览  
              撰写内容包括：利润总额、营业收入、成本、
              2.1.2\主要经营指标概览  
              撰写内容包括：xx区域销售回款、重大项目进度情况...
              ......
        ......           
        """    
    user_prompt = f"请根据标题{title}，撰写包括框架目录。要求：直接输出框架目录，不要输出任何与框架目录无关的文字，别瞎BB。"
    
    
    response = client.chat.completions.create(
        model="glm-4-plus",
        messages=[
            {"role": "system", "content": catalogue_gen_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature = temperature,
        stream=True,
    )
    
    # 使用生成器逐块处理流式响应
    for chunk in response:
        content = chunk.choices[0].delta.content
        print(content)
        yield content  # 使用yield返回每个块的内容


# *-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*

def Scheme_Frame_Parser(schemeframe):
    sys_prompt = f"""你是一名资深的{field}领域专家，拥有超过15年的行业经验。"""    
    user_prompt =  f"""你任务是的根据专业报告的框架{schemeframe}，针对每个报告的段落，生成解析语句，详见[解析要求]，参考[解析示例]。
        [解析要求]：
         ---报告框架中每个“撰写内容包括：”字样后的话，根据上下文意思解析为一个或多个段落。
         ---以“段落名称为：”开始，每个段落名称用“,”分割，结束后不要加任何标点符号。
         ---解析的段落名称要根据上下文语义补充称完整的名称，即时单看段落名，也表述完整。例如：人口情况，可以根据上下文解析为经开区人口情况。补充完整的目的是为了根据段落名进行知识检索。
         ---全部段落解析完后，增加解析后的报告模板，解析后的报告模板是：在原模版中，把“撰写内容包括：”字样去掉，保理每个段落名称，每个段落名称后面增加“{{段落名称}}”，以“解析后的报告模版：”为开头，换行输出。
         ---直接输出段落解析内容和解析后的报告模版，不要说其他任何废话。
         
         [解析示例]：
         报告框架如下：
            1\总述
               1.1\报告目的与背景
               撰写内容包括：报告撰写的目的、报告撰写的背景
               1.2\区域概述
               撰写内容包括：郑州经济开发区的地理位置、面积、人口、经济发展现状等基本情况
            
            2\发展现状分析
               2.1\经济基础分析
                  2.1.1\GDP及增长率
                  撰写内容包括：近年GDP总量及增长率
              
            3\发展规划
               3.1\总体发展目标
                  3.1.1\经济目标
                  撰写内容包括：未来GDP目标、产业结构优化目标
            
            对上面报告框架的解析如下：            
            段落名称为：
            报告撰写的目的,报告撰写的背景,郑州经济开发区的地理位置,郑州经济开发区的面积,郑州经济开发区的人口,郑州经济开发区的经济发展现状,郑州经济开发区近年GDP总量,郑州经济开发区近年GDP总量增长率,郑州经济开发区人口发展规划,郑州经济开发区就业率目标
            
            解析后的报告模版：
            1\总述
               1.1\报告目的与背景
               报告撰写的目的{{报告撰写的目的}}、报告撰写的背景{{报告撰写的背景}}
                1.2\区域概述
               郑州经济开发区的地理位置{{郑州经济开发区的地理位置}}、郑州经济开发区的面积{{郑州经济开发区的面积}}、郑州经济开发区的人口{{郑州经济开发区的人口}}、郑州经济开发区的经济发展现状{{郑州经济开发区的经济发展现状}}
            2\发展现状分析
               2.1\经济基础分析
                  2.1.1\GDP及增长率
                  郑州经济开发区近年GDP总量{{郑州经济开发区近年GDP总量}}、郑州经济开发区近年GDP总量增长率{{郑州经济开发区近年GDP总量增长率}}            
             3\发展规划
                3.1\总体发展目标
                  3.1.1\经济目标
                  郑州经济开发区人口发展规划{{郑州经济开发区人口发展规划}}、郑州经济开发区就业率目标{{郑州经济开发区就业率目标}}
            ......
            ......
            """    
    # 调用大模型进行结构解析
    response = client.chat.completions.create(
        model="glm-4-long",
        messages=[
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature = temperature,
        stream=True,
    )

    # 使用生成器逐块处理流式响应
    for chunk in response:
        content = chunk.choices[0].delta.content
        print(content)
        yield content  # 使用yield返回每个块的内容

# *-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*

tab1,tab2 = st.tabs(["报告模板生成","报告架构解析"])

# *-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*     

with tab1:
    
    col1,col2 = st.columns([1,2])
    
    with col1:
        # 设置左边栏
        title = st.text_area(label = "报告题目",placeholder='请输入')
        field = st.text_area(label = "所属领域",placeholder="财务领域、中国宏观经济、金融、市场分析、企业管理、战略规划等")
        require = st.text_area(label = "报告要求",height= 120,placeholder="请输入报告要求，例如背景、包括哪些内容，字数、风格等")
        storepath= st.text_area(label = "报告框架存储路径",placeholder='请输入文件夹路径',value = "/root/autodl-tmp/Rag_test/scheme")
    
    with col2:   
        cata_txt = ""
        # 创建一个空的容器，用于后续更新
        placeholder = st.empty()
    
        if "sche_catal" not in st.session_state:
            st.session_state["sche_catal"] = ""
        sche_catal2 =  st.session_state["sche_catal"]
        
        if catal_gen_button:
            if title:
                # 创建生成器对象
                catal_generator = catalogue_gene(field, require, title)
                # 使用一个循环来模拟流式输出，并更新text_area的内容
                cata_txt = ""
                for catal_chunk in catal_generator:
                    if catal_chunk !="":
                        cata_txt += catal_chunk  # 更新变量
                    else:
                        cata_txt += " "
                    # st.session_state["sche_catal"] = cata_txt12
                    cata_txt12 = placeholder.text_area(label="报告框架目录", height=470, value=cata_txt)
                st.session_state["sche_catal"] = cata_txt12
                    
        else:
            cata_txt12 = st.text_area(label="报告框架目录",height=500,value=sche_catal2)
    
        def store_cata():        
            path = os.path.join(storepath, f"{title}目录.txt")
            try:
                with open(path, "w") as f:
                    f.write(cata_txt12)
                    print(f"内容已成功写入到 {title}.txt文件里")
            except Exception as e:
                print(f"An error occurred while writing to the file: {e}")
        
        if store_catal_button:
            store_cata()
            with col2:
                st.write(f"{title}目录.txt文件已经成功存储")
                
        if del_catal_button:
            st.session_state["sche_catal"]=""
            placeholder.text_area(label="报告框架目录",height=630,value=st.session_state["sche_catal"])

# *-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*

with tab2:
    col1,col2 = st.columns([2,1])
    paragraph_names = ""
    template_name = ""

    if "parapar" not in st.session_state:
        st.session_state["parapar"] = ""
    if "para" not in st.session_state:   
        st.session_state["para"] = []
    if "frame" not in st.session_state:    
        st.session_state["frame"] = ""

    if paragr_parser_button:
        parser_gener = Scheme_Frame_Parser(cata_txt12)        
        paragr_parser_content = ""
        placeholder =st.empty()
        for trunk in parser_gener:
            if trunk != "":
              paragr_parser_content += trunk
            else:
              paragr_parser_content += "  "
            st.session_state["parapar"] = placeholder.text_area(label = "报告框架解析",height = 450, value =  paragr_parser_content)

    if extra_button:
        # 使用正则表达式提取所需信息
        paragraph_names_pattern = re.compile(r"段落名称为：((?:.|\n)*?)解析后的报告模版：", re.DOTALL)
        template_pattern = re.compile(r"解析后的报告模版：\n(.*?)$", re.DOTALL)
        
        # 提取报告模版
        template_match = re.search(template_pattern, st.session_state["parapar"])
        template_name = template_match.group(1) if template_match else "空字符"
        with col1:        
            st.session_state["frame"] = st.text_area(label="报告框架解析", height=400, value=template_name)
        
        # 提取段落名称
        paragraph_names_match = re.search(paragraph_names_pattern, st.session_state["parapar"])
        if paragraph_names_match:
            paragraph_names = paragraph_names_match.group(1).strip()
            paragraph_list = [item.strip() for item in paragraph_names.split(',') if item.strip()]
        else:
            paragraph_list = []  
        
        with col2: 
            st.session_state["para"] = st.text_area(label="报告段落解析", height=400, value="\n".join(paragraph_list))
        
           
    def store_parser_paragr():
        
        parer_path = os.path.join(storepath, f"{title}目录解析.txt")
        with open(parer_path, "w") as f:
            f.write(st.session_state["frame"])
            with col1:  
                st.write(f"{title}目录解析内容已成功写入到【{title}目录解析.txt】文件里")
        paragra_path = os.path.join(storepath, f"{title}段落列表.txt")
        with open(paragra_path,"w") as file:
            file.write(st.session_state["para"])
            with col2: 
                st.write(f"{title}的段落列表已经成功写到【{title}段落列表.txt】文件里面")

    if store_catalparser_button:
        # 存储报告解析.txt文件和报告段落列表.pkl文件
        store_parser_paragr()

        


    
    



