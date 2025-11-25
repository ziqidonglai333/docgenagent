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
import math

# *-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*

# 设置页面布局
st.set_page_config(page_title = "报告生成",
                   page_icon = "🛄",
                   layout= "wide",
                   initial_sidebar_state="expanded")

# st.markdown("# 报告生成")

client = ZhipuAI(api_key="927615462c6a5e9758e5b563a8b9003c.f2sbR2fSOxEqYzeN")

with st.sidebar:
    st.markdown("# 报告生成")
    
    temperature = st.slider(label= "模型温度",
                max_value=1.0,
                min_value=0.0,
                step= 0.1,
                value= 0.8)
    
    title = st.text_area(label = "报告题目",placeholder='请输入')
    field = st.text_area(label = "所属领域",placeholder="财务领域、中国宏观经济、金融、市场分析、企业管理、战略规划等")
    require = st.text_area(label = "报告要求",height= 120,placeholder="请输入报告要求，例如背景、包括哪些内容，字数、风格等")
    report_path = st.text_area(label = "报告存储路径",placeholder="请输入报告存储的文件夹路径")

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

def replace_placeholders(content, replacements):
    # 遍历替换字典
    for placeholder, value in replacements.items():
        # 替换占位符
        content = content.replace('{' + placeholder + '}', value)
        content.replace("\n\n","\n")
    # 返回替换后的内容
    return content     

# *-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*

def report_optimize(raw_report):
    # 设置大模型提示词和api_key
    sys_prompt = f"""你是一名资深的{field}领域专家，拥有超过15年的行业经验。"""    
    user_prompt =  f"""
    [任务]
    你任务是的根据专业报告主题{title}，结合对专业报告的要求{require}，根据专业报告整体内容{raw_report}和已经完成的优化内容{st.session_state["optimized"]}，继续完成对专业报告后续部分内容{optimizing}的优化。
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
            3.对标明“需外部知识补充，请具体再由人工补充一下，需要补充完整如下内容框架：XXXXXXX”的地方加黑、斜体显示
         """   
# 调用大模型进行文档优化
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

paragraph_content = {}
tab1,tab2 = st.tabs(["生成报告段落","统稿完善报告"])

# *-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*

with tab1:
    col1,col2,col3 = st.columns([1,1,2])
    
    with col1:
        if ["frame"] not in st.session_state:
            st.session_state["frame"] = ""
        frame_parser_path = st.text_area(label = "报告框架目录解析-XXXX目录解析.txt文件",value = "/root/autodl-tmp/Rag_test/scheme_content/秋天气候分析目录解析.txt")
        if os.path.exists(frame_parser_path):
            with open(frame_parser_path,"r") as f:
                st.session_state["frame"] = f.read()
        
        if "para_list" not in st.session_state:
            st.session_state["para_list"] = []
        paragraph_pkl_path = st.text_area(label = "报告段落列表文件路径-XXXX段落列表.pkl文件",value = "/root/autodl-tmp/Rag_test/scheme_content/秋天气候分析段落列表.txt")
        if os.path.exists(paragraph_pkl_path):
            with open(paragraph_pkl_path,"r") as f:
                paralst = f.read()
                st.session_state["para_list"] = [item.strip() for item in paralst.splitlines() if item.strip()]
        
        st.text_area(label="报告段落列表",height = 270,value = st.session_state["para_list"])
        
    with col2:
        k = st.number_input("请输入检索个数",min_value = 1, max_value = 20,value = 5)
        faiss_db = st.text_area("请输入向量数据库的地址.faiss文件")
        txt_path =  st.text_area("请输入切割文件的地址.pkl文件")
        retri_button = st.button(label = "检索内容")
        para_gene_button = st.button(label = "生成段落")
        para_gene_temp = st.button(label = "段落暂存")
        next_butt = st.button(label = "生成下一个段落")

    with col3:    
        if "paragraph_content" not in st.session_state:
            st.session_state["paragraph_content"] = {}
            
        if "num" not in st.session_state:
            st.session_state["num"] = 1

        if next_butt:
            if st.session_state["num"]<len(st.session_state["para_list"]):
                st.session_state["num"] += 1
        
        if st.session_state["para_list"] != []:
            if st.session_state["num"]<len(st.session_state["para_list"]):
                j = st.session_state["num"]
            else:
                j =len(st.session_state["para_list"])-1
    
            paragraph = st.session_state["para_list"][j]
    
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
             
        if para_gene_temp:
            start_index = st.session_state[f"paracon{j}"].find("[段落内容]")
            end_index = start_index + len("[段落内容]")
            result_text = st.session_state[f"paracon{j}"][end_index:].strip()
            print("去掉后的----------------------&&&&&&&&&&&&&&&")
            print(result_text)
            st.text_area(label = "段落内容", height = 250,value = result_text)
            st.session_state["paragraph_content"].update({f"{paragraph}":f"{result_text}"})
            print("list----------------------&&&&&&&&&&&&&&&")
            print(paragraph_content)

# *-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*

with tab2:
    col1,col2,col3= st.columns([1,2,3])
    with col1:
        scheme_frame_addr = st.text_area(label = "报告框架文件路径-xxx目录解析.txt",value = "/root/autodl-tmp/Rag_test/scheme_content/秋天气候分析目录解析.txt")
        with open(scheme_frame_addr,"r") as f:
            report_frame = f.read()     

        st.text_area(label = "报告框架",height = 170,value=report_frame)        
        st.text_area(label = "段落内容",height = 170,value=st.session_state["paragraph_content"])

        report_gene_button = st.button(label = "生成报告初稿")
    
    with col2:
        # st.text_area(label="报告初稿", height=510, value="") 
        # store_rawreport_button = st.button("报告初稿存储")
        
        if report_gene_button:
            if st.session_state["frame"] !="" and st.session_state["paragraph_content"] != {}:
                formatted_string = replace_placeholders(st.session_state["frame"], st.session_state["paragraph_content"])
                raw_report = st.text_area(label="报告初稿", height=510, value=formatted_string) 
                rawrep_path = os.path.join(report_path,f"{title}初稿.txt")
                with open(rawrep_path,"w") as f:
                    st.write(f"{title}初稿.txt已存储")
                    f.write(raw_report)
                    
        rawrep_path = os.path.join(report_path,f"{title}初稿.txt")
        if os.path.exists(rawrep_path):
            with open(rawrep_path,"r") as f:
                raw_report2 = f.read()
            st.text_area(label="报告初稿全文", height=510, value=raw_report2)
            
        report_opt_button = st.button("报告初稿优化")

    with col3:
                
        if "optimized" not in st.session_state:
            st.session_state["optimized"] = ""
         
        # st.text_area(label = "优化后的报告",height = 510 ,value = st.session_state["optimized"]) 
        rawrep_path = os.path.join(report_path,f"{title}初稿.txt")
        if os.path.exists(rawrep_path):
            with open(rawrep_path,"r") as f:
                raw_report = f.read()  
                raw_split_number = math.ceil(len(raw_report)/1500)    

        placeholder2 = st.empty()  
        
        if "muni" not in st.session_state:
                st.session_state["muni"] = 0
        if report_opt_button and os.path.exists(rawrep_path) and st.session_state["muni"] < raw_split_number:            
            start_index = st.session_state["muni"] * 1500
            stop_index = start_index + 1500
            optimizing = raw_report[start_index:stop_index]
            
            repo_gene = report_optimize(raw_report)
            opt_report_content = ""
            for chunk in repo_gene:
                if chunk != "":
                    opt_report_content +=  chunk
                else:
                    opt_report_content += " "
                optimized = placeholder2.text_area(label = "优化后的报告",height = 510 ,value = opt_report_content)
            st.session_state["optimized"] = st.session_state["optimized"] + optimized
            
            st.session_state["muni"] +=1

        else:
            st.write("报告已经优化结束")
            st.text_area(label = "优化结束的报告全文",height = 510 ,value = st.session_state["optimized"])
        
        store_opt_report_button = st.button("保存优化后的报告")
       # 保存修改后的报告
        if store_opt_report_button and st.session_state["optimized"] != "":            
            opt_report = os.path.join(report_path,f"{title}优化稿.txt")
            with open(opt_report,"w") as f:
                st.write(f"{title}优化稿.txt已经存储")
                f.write(f"{title}\n\n{st.session_state['optimized']}")
                              
                

# /root/autodl-tmp/Rag_test/knowledge_base/test/test_faissindex.faiss
# /root/autodl-tmp/Rag_test/knowledge_base/test/test_splittxt.pkl
#/root/autodl-tmp/Rag_test/scheme/春天目录.txt
