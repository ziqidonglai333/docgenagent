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

# *-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*

# 设置页面布局
st.set_page_config(page_title = "知识库",
                   page_icon = "🛄",
                   layout= "wide",
                   initial_sidebar_state="expanded")

st.markdown("# 知识库")

with st.sidebar:
    st.markdown("# 知识库")
    
    kd_temperature = st.slider(label= "模型温度",
                max_value=1.0,
                min_value=0.0,
                step= 0.1,
                value= 0.8)
    
    field = st.text_area(label = "所属领域",placeholder="财务领域、中国宏观经济、金融、市场分析、企业管理、战略规划等")
    know_db_gene_button = st.button(label = "知识库生成/加载")
    retri_button = st.button(label = "检索内容")
    answ_button = st.button(label = "生成回复")
    clear_button = st.button(label = "清除检索结果")

embedding_model = SentenceTransformer("/root/autodl-tmp/bge-large-zh-v1.5")

def load_spilt_embedding_txt(kd_source_file_path):   
    '''
    该函数的功能是对文件夹内全部TXT文档进行分割，完成向量化存储.
    kd_source_file_path:需要向量化的txt文档文件夹路径
    '''
    
    situation = ""
    split_situation = []
    faiss_situation =""
    
    father_path = os.path.dirname(kd_source_file_path)
    kd_source_file_name = os.path.basename(kd_source_file_path)
    pkl_path = os.path.join(father_path,f"{kd_source_file_name}_splittxt.pkl")
    faiss_path = os.path.join(father_path,f"{kd_source_file_name}_faissindex.faiss")
    if (os.path.exists(pkl_path)==True) and(os.path.exists(faiss_path)==True):
        situation = f"{pkl_path}和{faiss_path}两个文件已存在，如原始文档有更新，需要重新加载、分割和向量化文档，请删除这两个文件后重新执行"
        print(situation)
        print("--"*33)
        with open (pkl_path,"rb") as f:
            contents = pickle.load(f)
        split_situation =[f"{pkl_path}有{len(contents)}条数据",f"第一条数据为：{contents[0]}",f"最后一条数据为：{contents[-1]}"]
        print(split_situation[0])
        print("--"*33)
        print(split_situation[1])
        print("--"*33)
        print(split_situation[2])        

        faiss_index =faiss.read_index(faiss_path)
    
        faiss_situation = "对应的向量数据库faiss_index已经加载"
        print("--"*33)
        print(faiss_situation)
        
    else:
        loader = DirectoryLoader(kd_source_file_path,glob="**/*.txt",show_progress=True)
        content = loader.load()
        situation = "已完成知识库原文档加载"
        print(situation)
        # ----------------------------------
        # 用RecursiveCharacterTextSplitter切割
        
        textsplitter = RecursiveCharacterTextSplitter(
            chunk_size = 200,
            chunk_overlap = 30,
            length_function=len,
            is_separator_regex=False,
        )
        spli_docs = textsplitter.create_documents([i.page_content for i in content])
        contents = [i.page_content for i in spli_docs]
        
        with open(pkl_path,"wb") as file:
            pickle.dump(contents,file)
        split_situation = [f"{pkl_path}文件已经生成，共计{len(contents)}条数据",f"第一条数据是{contents[0]}",f"最后一条数据是{contents[-1]}"]
        print(split_situation[0])
        print("--"*33)
        print(split_situation[1])
        print("--"*33)
        print(split_situation[2])
    
        # ----------------------------------
        # 对切割后的文本向量化

        embedding_content = embedding_model.encode(contents)

        # 将文本向量化数据加入faiss数据库
        faiss_index = faiss.IndexFlatL2(embedding_model.get_sentence_embedding_dimension())
        faiss_index.add(embedding_content)
        faiss.write_index(faiss_index,faiss_path)
        
        faiss_situation = f"对应的向量数据库faiss_index已经加载"
        print("--"*33)
        print(faiss_situation)


    return {"situation":situation,"split_situation":split_situation,"faiss_situation":faiss_situation,"faiss_index":faiss_index,"text_contents":contents}

# ----------------------------------

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

# ----------------------------------

def RAG_Answ(squery,retre_result,kd_temperature,field):
    # 设置大模型提示词和api_key
    sys_prompt = f"""你是一名资深的{field}领域专家，拥有超过15年的行业经验。"""    
    user_prompt =  f"""你任务是的根据{retre_result}内容，回答 {squery}的问题，具体回复见[回复要求]。
        [回复要求]：
         ---请严格按照{retre_result}内容要求回答问题；
         ---必要时可根据你自己的知识回答问题，在使用你自有的知识时，需标明'根据我已有经验......'，并将这些字体加黑、斜体显示；
         ---请不要回复大概、可能等模棱两可的答案。
            """    
    client = ZhipuAI(api_key="927615462c6a5e9758e5b563a8b9003c.f2sbR2fSOxEqYzeN")
    answer = ""

# 调用大模型进行文档优化
    response = client.chat.completions.create(
        model="glm-4-plus",
        messages=[
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature = kd_temperature,
        stream=True,
    )

    # 使用生成器逐块处理流式响应
    for chunk in response:
        content = chunk.choices[0].delta.content
        print(content)
        yield content  # 使用yield返回每个块的内容


if "retriel" not in st.session_state:
    st.session_state["retriel"] = ""
if clear_button:
    st.session_state["retriel"] = ""


tab1,tab2 = st.tabs(["知识库","检索问答"])
with tab1:
    col1,col2 = st.columns([1,2])
    with col1:        

        know_db_addr = st.text_area(label = "知识库知识源文件文件夹路径",placeholder="请输入知识库源文件文件夹路径,linux系统以/开始")
              
        know_db_name = os.path.basename(know_db_addr)
        # st.divider()
        st.write(f"知识库名称为{know_db_name}")

        st.write("知识库文件结构为“xxxxx/knowledge_database/具体知识库文件夹/知识源文件的文件夹，知识库名字_splittxt.pkl，知识库名字_splittxt.pkl”。具体知识库文件夹名称和知识源文件的文件夹名称一致。知识源文件的文件夹里面放知识源文件.txt；“知识库名字_splittxt.pkl”文件是分割后的文本文件；“知识库名字_faissindex.faiss”是分割文本向量化后存储的faiss向量数据文件 ")
    
    with col2:
        
        if know_db_gene_button:
            know_retu = load_spilt_embedding_txt(kd_source_file_path = know_db_addr)        
            # st.text_area(label = "知识库名称",value = know_db_name)
            st.text_area(label = "知识库状态",height = 120, value = know_retu["situation"])
            st.text_area(label = "知识分割状态",height = 250, value = (
    f"{know_retu['split_situation'][0]}\n\n"
    f"{know_retu['split_situation'][1]}\n\n"
    f"{know_retu['split_situation'][2]}"
))

            st.write(know_retu["faiss_situation"])
        else:
            # st.text_area(label = "知识库名称",value = "")
            st.text_area(label = "知识库状态",height = 120, value = "")
            st.text_area(label = "知识分割状态",height = 200, value = "")
            st.write("向量数据库状态")
with tab2:
    col1,col2 = st.columns([1,2])
    with col1:
       
        ssssquery =st.text_area(label = "问题",placeholder="请输入需要检索的问题")
        squery = [ssssquery]
        
        k = st.number_input("请输入检索个数",min_value = 1, max_value = 20,value = 5)
        
        # faiss_db = st.file_uploader("请选择向量数据库XXX_faissindex.faiss文件", type=['faiss'])
        faiss_db = st.text_area("请输入向量数据库的地址.faiss文件")
        txt_path =  st.text_area("请输入切割文件的地址.pkl文件")
        # uploaded_file2 = st.file_uploader("请选择一个分割文本库XXX__splittxt.pkl文件", type=['pkl'])
        # # 如果文件被上传，则加载并显示内容
        # if uploaded_file2 is not None:
        #     # 使用 pickle 加载上传的文件
        #     txt_path = uploaded_file2
        # else:
        #     txt_path = ""
    
    with col2:
        
        if retri_button:
            if faiss_db != "" and txt_path != "":
                st.session_state["retriel"] = knoledge_retri(faiss_path=faiss_db,txt_path=txt_path,squery=squery,k=k)
        retre_results = st.text_area(label = "检索结果", height = 200 ,value = st.session_state["retriel"])

        if answ_button and retre_results!="":
            answ_gener = RAG_Answ(squery=squery,retre_result=retre_results,kd_temperature=kd_temperature,field=field)
            answ_txt = ""
            placeholder =st.empty()
            for trunk in answ_gener:
                if trunk != "":
                  answ_txt += trunk
                else:
                  answ_txt += "  "
                placeholder.text_area(label = "大模型答案", height = 250,value = answ_txt)
        else:
            st.text_area(label = "大模型答案",height = 250,value ="")
                
