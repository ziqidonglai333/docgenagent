# 导入依赖包
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableParallel,RunnablePassthrough
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings.huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
import os
from langchain_community.document_loaders import TextLoader
import  streamlit as st
import  streamlit as st

# 设置页面布局
st.set_page_config(page_title = "知识库",
                   page_icon = "🛄",
                   layout= "wide",
                   initial_sidebar_state="expanded")

# 设置标题
st.title(body="智永方略***知识库***")
# st.markdown(f"<h1 style='color: blue;'>王智东的***知识库***🔧</h1>",unsafe_allow_html=True)

# 设置左边栏
with st.sidebar:
    # 设置文件上传
    uploaded_file = st.file_uploader("请选择上传的文件")
    if uploaded_file is not None:
        # stingio = StringIO(uploaded_file.getvalue().decode("utf-8"))
        file_content = uploaded_file.read()
        # contract_content = file_content
        text = file_content.decode("utf-8")
        st.write("文件上传成功")

    # 分割线
    st.divider()

    # 设置模型温度
    temperature = st.slider(label= "温度",
                            max_value=1.0,
                            min_value=0.0,
                            step= 0.1,
                            value= 0.8)
    st.write(temperature)

    # 设置检索匹配的数量
    select_num = st.slider(label= "检索数量",
                            max_value=20,
                            min_value=1,
                            step= 1,
                            value= 8)
    st.write(select_num)


    # 加载知识
    loader = TextLoader("/root/rag-deom/财务基础知识(1).txt")
    content = loader.load()

    # 对加载的知识进行切分块
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size = 500,
        chunk_overlap = 10,
        length_function = len,
        add_start_index =True
    )
    documents  = text_splitter.split_documents(content)

    # 对分块的知识进行向量化
    embedding_path ="/root/.cache/modelscope/hub/AI-ModelScope/bge-large-zh-v1.5"
    embeddings = HuggingFaceEmbeddings(model_name = embedding_path)
    vectorstore = Chroma.from_documents(documents = documents,embedding=embeddings)

def retriever_results(query) :
    retriever_results=vectorstore.similarity_search(query=query,k=4)
    knowle = "\n".join(x.page_content for x in retriever_results)
    return(knowle)
    
col1,col2 = st.columns(spec = 2)
with col1:
    input = st.chat_input("请输入：")
    st.text_area(label = "检索问题",height = 150,value = input) 

if input is not None:
    retrie_resul = retriever_results(input)
else:
    retrie_resul = ""
    input = ""

with col2:
    st.text_area(label = "检索内容",height = 550,value = (retrie_resul)) 

# 建立大模型对象链接
from langchain_openai import ChatOpenAI
import os
llm = ChatOpenAI(
    temperature = temperature,
    model="glm-4",
    openai_api_key="d2e482be31c453838f46321a197d117d.XnlnLgeyA0KFR2wE",
    openai_api_base="https://open.bigmodel.cn/api/paas/v4/"
)

prompt  = f"根据{retrie_resul}的内容，回答{input}问题。"

from langchain_core.output_parsers import StrOutputParser
output_parser = StrOutputParser()
chain = llm| output_parser
llm_resul = chain.invoke(prompt)

with col1:
    st.text_area(label = "模型回复",height = 300,value = (llm_resul) )
