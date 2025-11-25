# 导入依赖包
import os
import  streamlit as st
from zhipuai import ZhipuAI


# ******---------*******--------*******----------------
# 设置页面布局
st.set_page_config(page_title = "报告框架生成",
                   page_icon = "🛄",
                   layout= "wide",
                   initial_sidebar_state="expanded")

st.markdown("# 报告框架生成——流式输出")
# st.sidebar.markdown("# 报告框架生成——流式输出")

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
    
    client = ZhipuAI(api_key="927615462c6a5e9758e5b563a8b9003c.f2sbR2fSOxEqYzeN")
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
    sto_catal_button = st.button(label = "导出报告框架")

col1,col2 = st.columns([1,2])

with col1:
    # 设置左边栏
    title = st.text_area(label = "报告题目",placeholder='请输入')
    field = st.text_area(label = "所属领域",placeholder="财务领域、中国宏观经济、金融、市场分析、企业管理、战略规划等")
    require = st.text_area(label = "报告要求",height= 200,placeholder="请输入报告要求，例如背景、包括哪些内容，字数、风格等")
    storepath= st.text_area(label = "报告框架存储路径",placeholder='请输入文件夹路径',value = "/root/autodl-tmp/Rag_test/scheme")


with col2:   
    cata_txt = ""
    placeholder = st.empty()

    if "sche_catal" not in st.session_state:
        st.session_state["sche_catal"] = ""
    sche_catal2 =  st.session_state["sche_catal"]


    if catal_gen_button:
        if title:
            # 创建生成器对象
            catal_generator = catalogue_gene(field, require, title)
            # 创建一个空的容器，用于后续更新
            # placeholder = st.empty()
            # 使用一个循环来模拟流式输出，并更新text_area的内容
            cata_txt = ""
            for catal_chunk in catal_generator:
                if catal_chunk !="":
                    cata_txt += catal_chunk  # 更新变量
                else:
                    cata_txt += " "
                # st.session_state["sche_catal"] = cata_txt12
                # cata_txt12 = placeholder.text_area(label="报告框架目录", height=630, value=cata_txt)
                cata_txt12 = placeholder.text_area(label="报告框架目录", height=630, value=cata_txt)
            st.session_state["sche_catal"] = cata_txt12
                
    else:
        # st.text_area(label="报告框架目录",height=630,value=st.session_state["sche_catal"])
        cata_txt12 = st.text_area(label="报告框架目录",height=630,value=sche_catal2)

    def sto_cata():        
        path = os.path.join(storepath, f"{title}目录.txt")
        try:
            with open(path, "w") as f:
                f.write(cata_txt12)
                print(f"内容已成功写入到 {title}.txt文件里")
        except Exception as e:
            print(f"An error occurred while writing to the file: {e}")
    
    if sto_catal_button:
        
        sto_cata()
        # st.button(label = "导出报告框架", on_click=sto_cata)


    if del_catal_button:
        st.session_state["sche_catal"]=""
        placeholder.text_area(label="报告框架目录",height=630,value=st.session_state["sche_catal"])



    
    



