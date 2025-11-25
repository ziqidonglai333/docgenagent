# 导入相关的包
import streamlit as st
import os
import pickle
import nltk
import faiss
from langchain_community.document_loaders import DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from zhipuai import ZhipuAI
from sentence_transformers import SentenceTransformer
import re

# *-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*

# 设置页面布局
st.set_page_config(page_title = "报告生成",
                   page_icon = "🛄",
                   layout= "wide",
                   initial_sidebar_state="expanded")

st.markdown("# 报告生成")

client = ZhipuAI(api_key="927615462c6a5e9758e5b563a8b9003c.f2sbR2fSOxEqYzeN")

with st.sidebar:
    st.markdown("# 报告生成")
    
    temperature = st.slider(label= "模型温度",
                max_value=1.0,
                min_value=0.0,
                step= 0.1,
                value= 0.8)
    
    field = st.text_area(label = "所属领域",placeholder="财务领域、中国宏观经济、金融、市场分析、企业管理、战略规划等")
    title = st.text_area(label = "报告题目",placeholder='请输入')
    require = st.text_area(label = "报告要求",height= 120,placeholder="请输入报告要求，例如背景、包括哪些内容，字数、风格等")
    report_gene_button = st.button(label = "生成报告")
    # clear_button = st.button(label = "清除检索结果")

embedding_model = SentenceTransformer("/root/autodl-tmp/bge-large-zh-v1.5")

# *-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*

def knoledge_retri(faiss_path,txt_path,squery,k):   
    '''
    该函数的功能是对实现知识库搜索,根据检索结果回答问题
    faiss_path:向量数据库文件路径
    txt_path：切割文本数据文件路径
    squery:需要大模型回答的问题
    k:检索后，从检索排序结果中录取的数量
    ''' 

    faiss_db = faiss.read_index(faiss_path)
    retr = faiss_db.search(embedding_model.encode(squery),k)
    print ("***"*39)
    dist = retr[0]
    index =retr[1]
    print ("距离：",dist)
    print ("距离：",type(dist))
    print ("索引",index)
    print ("距离：",type(index))
    retre_result = ""
    with open (txt_path,"rb") as f:
            contents = pickle.load(f)
    for i in index[0]:
        xx = contents[i]+"/n/n"
        retre_result = retre_result+xx
    return  retre_result

# *-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*

def Scheme_Frame_Parser(schemeframe):
    sys_prompt = f"""你是一名资深的{field}领域专家，拥有超过15年的行业经验。"""    
    user_prompt =  f"""你任务是的根据专业报告的框架{schemeframe}，针对每个报告的段落，生成解析语句，详见[解析要求]，参考[解析示例]。
        [解析要求]：
         ---报告框架中每个“撰写内容包括：”字样后的话，根据上下文意思解析为一个或多个段落。
         ---以“段落名称为：”开始，每个段落名称用“\”分割，结束后不要加任何标点符号。
         ---解析的段落名称要根据上下文语义补充称完整的名称，能够单独看明白。例如：人口情况，可以根据上下文解析为经开区人口情况。
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
            报告撰写的目的\报告撰写的背景\郑州经济开发区的地理位置\郑州经济开发区的面积\郑州经济开发区的人口\郑州经济开发区的经济发展现状\郑州经济开发区近年GDP总量\郑州经济开发区近年GDP总量增长率\郑州经济开发区人口发展规划\郑州经济开发区就业率目标
            
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

def Paragraph_generate(field,title,scheme,Paragraph,retrie_result):
    # 设置大模型提示词和api_key
    sys_prompt = f"""你是一名资深的{field}领域专家，拥有超过15年的行业经验。"""    
    user_prompt =  f"""
    [任务]
    你任务是的根据专业报告主题{title}，结合专业报告的整体大纲{scheme}，完成专业报告段落{Paragraph}的内容的编写。
    [技能]
        ---数据分析：从数据中提炼关键洞察并进行深入分析。
        ---深度洞察：识别领域中的问题与亮点，并提出专业意见和评论。
    [思考过程]
    “
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
    ”
    [编写要求]
         ---请结合检索已知的{retrie_result}内容；
         ---必要时可根据你自己的知识，在使用你自有的知识时，需标明'根据我已有经验......'，并将这些字体加黑、斜体显示；
         ---针对缺少数据的内容，可以列好表格，将数据空着；
         ---针对需要补充外部知识的地方，可以标明“需外部知识补充，请具体再由人工补充一下，需要补充完整如下内容框架：XXXXXXX”
         ---请不要写大概、可能等模棱两可的语句；
         ---以专业报告，正向行文的风格写。
    [输出]
    你“必须”使用Plaintext代码框，在每个输出前用Plaintext代码框展示你的思考过程，格式为:以[思考过程]四个字为开始，具体思考内容换行后输出。
    你“必须”以[段落内容]四个字为开始，具体段落内容编写换行后输出。
                """   
# 调用大模型进行文档优化
    response = client.chat.completions.create(
        model="glm-4-plus",
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

paragraph_content = {}
tab1,tab2,tab3 = st.tabs(["报告架构解析","生成报告段落","统稿完善报告"])


with tab1:
    col1,col2 = st.columns([1,2])
    with col1:        
        scheme_frame_addr = st.text_area(label = "报告框架文件路径",placeholder="请输入报告框架文件路径,linux系统以/开始")
        paragr_parser_button = st.button(label = "报告段落解析")
        extra_button = st.button(label = "提取段落和报告框架")

    with col2:
        if "parapar" not in st.session_state:
            st.session_state["parapar"] = ""
        if "para" not in st.session_state:   
            st.session_state["para"] = []
        if "frame" not in st.session_state:    
            st.session_state["frame"] = ""

        if paragr_parser_button:
            with open(scheme_frame_addr, "r") as f:
                report_sche = f.read()
            parser_gener = Scheme_Frame_Parser(report_sche)        
    
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
            paragraph_names_pattern = re.compile(r"段落名称为：\n(.*?)\n", re.DOTALL)
            template_pattern = re.compile(r"解析后的报告模版：\n(.*?)$", re.DOTALL)
            
            # 提取段落名称
            paragraph_names_match = re.search(paragraph_names_pattern, st.session_state["parapar"])
            st.session_state["para"] = paragraph_names_match.group(1).split("\\") if paragraph_names_match else []
            
            # 提取报告模版
            template_match = re.search(template_pattern, st.session_state["parapar"])
            st.session_state["frame"] = template_match.group(1) if template_match else "空字符"
            
        # 显示段落名称和报告框架，确保转换为字符串
        report_paragraph = st.text_area(label="报告段落解析", height=200, value="\n".join(st.session_state["para"]))
        report_frame = st.text_area(label="报告框架解析", height=200, value=st.session_state["frame"])
            
# *-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*     

with tab2:
    paragraph_list = st.session_state["para"]
    # paragraph_list = report_paragraph
    paragraph_conts = {}
    col1,col2 = st.columns([1,2])
    with col1:
        k = st.number_input("请输入检索个数",min_value = 1, max_value = 20,value = 5)
        faiss_db = st.text_area("请输入向量数据库的地址.faiss文件")
        txt_path =  st.text_area("请输入切割文件的地址.pkl文件")
        retri_button = st.button(label = "检索内容")
        para_gene_button = st.button(label = "生成段落")
        para_gene_catch = st.button(label = "段落暂存")
        next_butt = st.button(label = "生成下一个段落")

    with col2:    
        if "num" not in st.session_state:
            st.session_state["num"] = 1

        if next_butt:
            if st.session_state["num"]<len(paragraph_list):
                st.session_state["num"] += 1
        
        if paragraph_list != []:
            if st.session_state["num"]<len(paragraph_list):
                j = st.session_state["num"]
            else:
                j =len(paragraph_list)-1
    
            paragraph = paragraph_list[j]
    
            ssssquery =st.write(f"报告段落是：{paragraph}")
            squery = [paragraph]
            
            if f"retriel{j}" not in st.session_state:
                st.session_state[f"retriel{j}"] = ""
            
            if f"paracon{j}" not in st.session_state:
                st.session_state[f"paracon{j}"] = ""
            
            if retri_button:
                if faiss_db != "" and txt_path != "":
                    st.session_state[f"retriel{j}"] = knoledge_retri(faiss_path=faiss_db,txt_path=txt_path,squery=squery,k=k)
            retrie_result = st.text_area(label = "检索结果", height = 200 ,value = st.session_state[f"retriel{j}"]) 

        if para_gene_button and retrie_result!="":
            #     Paragraph_generate(field,title,scheme,Paragraph,retrie_result)
            para_gener = Paragraph_generate(field=field,title=title,scheme=st.session_state["frame"],Paragraph=ssssquery,retrie_result=retrie_result)
            para_txt = ""
            placeholder =st.empty()
            for trunk in para_gener:
                if trunk != "":
                  para_txt += trunk
                else:
                  para_txt += "  "
                para = placeholder.text_area(label = "段落内容", height = 250,value =para_txt)
            st.session_state[f"paracon{j}"] = para
             
        if para_gene_catch:
            start_index = st.session_state[f"paracon{j}"].find("[段落内容]")
            end_index = start_index + len("[段落内容]")
            result_text = st.session_state[f"paracon{j}"][end_index:].strip()
            print("去掉后的----------------------&&&&&&&&&&&&&&&")
            print(result_text)
            st.text_area(label = "段落内容", height = 250,value = result_text)
            paragraph_content.update({f"{paragraph}":f"{result_text}"})
            print("list----------------------&&&&&&&&&&&&&&&")
            print(paragraph_content)

# *-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*

with tab3:
    if report_gene_button:
        if st.session_state["frame"] !="" and paragraph_conts != {}:
            formatted_string = st.session_state["frame"].format(**paragraph_content)
            st.text_area(label="报告", height=500, value=formatted_string)

# /root/autodl-tmp/Rag_test/knowledge_base/test/test_faissindex.faiss
# /root/autodl-tmp/Rag_test/knowledge_base/test/test_splittxt.pkl
#/root/autodl-tmp/Rag_test/scheme/春天目录.txt
