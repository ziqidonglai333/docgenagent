import fitz
import streamlit as st
import io
import os
from zhipuai import ZhipuAI

# *-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*

# 设置页面布局
st.set_page_config(page_title = "文档处理",
                   page_icon = "🛄",
                   layout= "wide",
                   initial_sidebar_state="expanded")

st.markdown("# PDF文档智能转化为TXT文档")

with st.sidebar:
    st.markdown("# PDF文档智能转化为TXT文档")
    
    temperature = st.slider(label= "模型温度",
                        max_value=1.0,
                        min_value=0.0,
                        step= 0.1,
                        value= 0.8)
    
    st.write(temperature)
    
    store_path = st.text_area(label= "优化后的文件存储路径",placeholder = '路径为绝对路径的文件夹，linux以/开头')

 # 设置文件上传
    uploaded_files = st.file_uploader(label = "请选择上传的PDF文件", type = ['pdf'],accept_multiple_files = True)

    PDF2TXT_Button = st.button(label="PDF2TXT")

def load_pdf(pdf_file):
    '''
    该函数功能为：读取PDF文档；
    pdf_file：待读取的PDF文件。
    '''
    file_bytes = pdf_file.getvalue()
    # 使用fitz打开字节流
    pdf = fitz.open(stream=file_bytes, filetype="pdf")
    pdf_txt = ""
    for page in pdf:
        cont = page.get_text()
        pdf_txt += cont
    return pdf_txt
        
# 完成pdf读取以及用大模型去除无关内容
def Opti_txt(txt_cont):
    '''
    该函数功能为：利用大模型将文档中的无关内容去除，并输出为.txt文件；
    txt_cont：待优化的文本。
    '''

    # 设置大模型提示词和api_key
    sys_prompt = f"""你是一名资深的文档处理专家，拥有超过15年的文档审查经验。"""    
    user_prompt =  f"""[任务]: 你要优化的文档 {txt_cont}是从pdf转换过来的，保理了原来pdf的一些痕迹。你的任务是去除文档中与内容无关的页码、页眉、页脚等从PDF转换时带来的与文章内容不相关的东西，返回文章原始内容。返回的文档见[输出要求]。
        [输出要求]：
         ---直接输出文档内容，仅返回文档内容，不要输出不是文档内容的任何话；
         ---返回的内容为仅可去除与内容无关的东西，返回文章原始内容。
         ---如因PDF转换原因造成文字段落分散，可以根据意思，将前后挨着的不同段落的相同内容放在一个段落，但是原文章句子的顺序不得改变，不要有任何文字的修改。          
            """    
    client = ZhipuAI(api_key="927615462c6a5e9758e5b563a8b9003c.f2sbR2fSOxEqYzeN")


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
   
col1,col2 = st.columns(2)

if PDF2TXT_Button:
    placeholder1 = st.empty()
    if uploaded_files is not None: 
        for file in uploaded_files:
            base_name,exte_name =os.path.splitext(file.name)
            with placeholder1:
                with col1:
                    # st.write(f"{base_name}原文")
                    raw_txt = st.text_area(label = "PDF读出的文档",height = 500,value = load_pdf(file))
        
                with col2:
                     # 创建一个空的容器，用于后续更新
                    # container =st.container()
                    placeholder2 = st.empty() 
                    txt_generator = Opti_txt(raw_txt)
                    # 使用一个循环来模拟流式输出，并更新text_area的内容
                    opt_txt = ""
                    for chunk in txt_generator:
                        if chunk !="":
                            opt_txt += chunk  # 更新变量
                        else:
                            opt_txt += " "
                        
                        placeholder2.text_area(label = "整理优化后的文档",height = 500,value = opt_txt)
                    
                    paths = os.path.join(store_path,f"{base_name}.txt")
                    with open(paths,"w") as f:
                        f.write(opt_txt)
                    # container.write("文件已优化并存储到您制定文件夹")
 
else:
    with col1:
        st.text_area(label = "PDF读出的文档",height = 500,value ="")
    
    with col2:
        st.text_area(label = "去除无用信息额文档",height = 500,value ="")