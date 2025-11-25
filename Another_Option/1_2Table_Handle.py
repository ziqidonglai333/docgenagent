import streamlit as st
import fitz  # PyMuPDF
import os
import base64
from zhipuai import ZhipuAI
import os
import re
import csv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
import pandas as pd



# *-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*
# 设置页面布局
st.set_page_config(page_title = "表格处理",
                   page_icon = "🛄",
                   layout= "wide",
                   initial_sidebar_state="expanded")

st.markdown("# PDF表格智能解读")
st.sidebar.markdown("# PDF表格智能解读")



# 该函数用来将pdf转换为图片
def pdf2image(pdf_path,output_path):
   # pdf_path为pdf的文件地址，output_path为输出的文件地址
    image_paths = []
    # 使用os.path.basename()获取文件名（包括扩展名）
    file_name_with_extension = os.path.basename(pdf_path)
    # 使用os.path.splitext()分离文件名和扩展名
    file_name_without_extension, file_extension = os.path.splitext(file_name_with_extension)
    print(file_name_without_extension)  # 输出: file
    print(file_extension)               # 输出: .txt

    # 打开PDF文件
    doc = fitz.open(pdf_path)
   # 遍历每一页
    for page_num in range(len(doc)):
        page = doc[page_num]
        # PDF页面转换为图像
        pix = page.get_pixmap()
        # 保存图像
        outpath = os.path.join(output_path, f"{file_name_without_extension}page_{page_num + 1}.jpg")
        pix.save(outpath)
        image_paths.append(outpath)  # 将路径添加到列表中

    doc.close()
    return image_paths
    # doc.close()
    # return outpath

# 函数调用测试
# pdf_path = "/root/autodl-tmp/Rag_test/knowledge_base/附件：2025年度江苏省民用建筑能效测评标识项目（第一批）+.pdf"
# output_path = "/root/autodl-tmp/Rag_test/scheme"
# pdf2image(pdf_path,output_path)
   

# *-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*
# 使用glm-4v-flash模型识别图片中的表格并输出
def img_lable_read(img_path,store_path,v_mod_temperature):
# 参数说明：img_path为需要解析的图片的路径；
# store_path为需要将解析图片生成的内容存放的路径。
    with open(img_path, 'rb') as img_file:
        img_base = base64.b64encode(img_file.read()).decode('utf-8')
    client = ZhipuAI(api_key="927615462c6a5e9758e5b563a8b9003c.f2sbR2fSOxEqYzeN") # 填写您自己的APIKey
    response = client.chat.completions.create(
        model="glm-4v-plus",  # 填写需要调用的模型名称
        messages=[
          {
            "role": "user",
            "content": [
              {
                "type": "image_url",
                "image_url": {
                    "url": img_base
                }
              },
              {
                "type": "text",
                "text": "请描述这个图片,识别图片中的每个表格，每个表格请以'表格名称为xxxx\n\n'的方式返回表格名称，以'表格正文如下:\n开始'，以csv的格式输出表格正文，表格正文结束后添加'\n\n'结尾"
              }
            ]
          }
        ],
        temperature = v_mod_temperature,
    )
    rescontent = response.choices[0].message.content
    print(rescontent)
    
    # 将从PDF中识别的表格，经大模型优化后的字符串输出写到CSV文件里
    tables_dict = {}

    # 正则表达式 patterns
    tablename_pattern = r"表格名称为(.*?)\n\n"
    tablecontent_pattern = r"表格正文如下:(.*?)(?=\n\n表格名称为|\Z)"
    
    # Find all matches for table names and contents
    tablename_matches = re.finditer(tablename_pattern,rescontent, re.S)
    tablecontent_matches = re.finditer(tablecontent_pattern,rescontent, re.S)
    
    # Extract key-value pairs and store them in the dictionary
    for name_match, content_match in zip(tablename_matches, tablecontent_matches):
        tablename = name_match.group(1).strip()
        tablecontent = content_match.group(1).strip()
        tables_dict[tablename] = tablecontent
    
    # 输出结果
    for name, content in tables_dict.items():
        print(f"表格名称: {name}")
        print("表格正文:")
        print(content)
        print("-" * 40)

    
    # 将字典中的每个键作为.csv文件名称，值作为.csv文件内容
    for csvname, csvcontent in tables_dict.items():
        csv_file_name_list=[]
        spath = os.path.join(store_path,f"{csvname}.csv")
        # 创建 CSV 文件
        with open(spath, 'w', newline='', encoding='utf-8') as csvfile:
            # 创建 CSV 写入器
            csvwriter = csv.writer(csvfile)
            # 将表格内容按行分割，并写入 CSV 文件    
            for row in csvcontent.split('\n'):
                csvwriter.writerow(row.split(','))
        csv_file_name_list.append(csvname)
    return csv_file_name_list
                

# 函数功能测试
# img_path = "/root/autodl-tmp/Rag_test/knowledge_base/1737602055535.jpg"
# store_path = "/root/autodl-tmp/Rag_test/scheme"
# img_lable_read(img_path,store_path)



# *-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*
# 创建表格解读模型函数，利用大模型对表格进行解读



def table_interpret(csv_table,llm_temperature,background=""):
    # csv_table_path是表格CSV的文件路径，background是字符串类型，描述跟表格相关的说明
    
    # 实例化在线glm-4模型
    llm_line = ChatOpenAI(
        temperature = llm_temperature,
        model = "glm-4",
        openai_api_key = "927615462c6a5e9758e5b563a8b9003c.f2sbR2fSOxEqYzeN",
        openai_api_base="https://open.bigmodel.cn/api/paas/v4/"
    )
    
    # 使用pandas的read_csv函数读取CSV文件
    df_table = pd.read_csv(csv_table)  
    
    # 显示DataFrame内容
    print(df_table)
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
    return(table_interpret_chain.invoke({"df_table": df_table.to_string(), "background": background}))


# 测试函数功能
# csv_table_path = '/root/autodl-tmp/Rag_test/knowledge_base/技术记录表.csv'
# print(table_interpret(csv_table_path))


# *-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*



# 创建两个页签
tab1, tab2,tab3 = st.tabs(["PDF转图片", "图片里提取表格","表格解读"])

# 在第一个页签中添加内容
with tab1:
    col1,col2 = st.columns([2,3])
    with col1:
        pdf_path = st.text_area(label= "待解析PDF文件位置路径",placeholder = '路径为绝对路径，linux以/开头，包括文件名.pdf')
        output_path = st.text_area(label= "图片输出位置路径",placeholder = '路径为绝对路径文件夹，linux以/开头')
        pdf2img_butt = st.button(label = "转换")

    with col2:
        if pdf2img_butt:
            if not os.path.exists(output_path):
                st.error(f"输出路径不存在: {output_path}")
            else:
                # 确保调用 pdf2image 并接收返回的列表
                image_paths = pdf2image(pdf_path, output_path)
                for image_path in image_paths:  # 遍历列表中的每个路径
                    st.image(image_path, caption=os.path.basename(image_path), use_container_width=True)


with tab2:
    col1,col2 = st.columns([2,3])
    with col1:
    # 设置模型温度
        v_mod_temperature = st.slider(label= "V模型温度",
                                max_value=1.0,
                                min_value=0.0,
                                step= 0.1,
                                value= 0.8)
        st.write(v_mod_temperature)
        img_path = st.text_area(label= "待识别图片位置路径",placeholder = '路径为绝对路径，linux以/开头，包括文件名和后缀')
        store_path = st.text_area(label= "表格csv输出位置路径",placeholder = '路径为绝对路径文件夹，linux以/开头')
        img_lable_read_button = st.button(label = "图片表格识别")
    with col2:
        if img_lable_read_button:
            csv_filename_list = img_lable_read(img_path,store_path,v_mod_temperature)
            for table in csv_filename_list:
                csv_file = f"{store_path}/{table}.csv"
                dftable = pd.read_csv(csv_file)
                st.dataframe(dftable)
            
with tab3:
    col1,col2 = st.columns([2,3])
    with col1:
    # 设置模型温度
        llm_temperature = st.slider(label= "大语言模型温度",
                                max_value=1.0,
                                min_value=0.0,
                                step= 0.1,
                                value= 0.8)
        st.write(llm_temperature)
        # img_path = st.text_area(label= "待识别图片位置路径",placeholder = '路径为绝对路径，linux以/开头，包括文件名和后缀')
        store_path = st.text_area(label= "表格解析后文件输出位置路径",placeholder = '路径为绝对路径文件夹，linux以/开头')
        
        # 设置文件上传
        uploaded_files = st.file_uploader(label = "请选择上传的CSV文件", type = ['csv'],accept_multiple_files = True)
        # interpre_contents = []
        if uploaded_files is not None:
            st.write("文件上传成功")


        table_interpret_button = st.button(label = "表格解读分析")

    with col2:
        if table_interpret_button:
            for upload_file in uploaded_files:
                int_cont = table_interpret(upload_file,llm_temperature,background="")
                st.text_area(label = "表格解析内容",height = 400 ,value = int_cont)
                # interpre_contents.append(int_cont)
                print(upload_file.name)
                base_name,exte_name =os.path.splitext(upload_file.name)
                print(type(base_name))
                print(base_name)
                pathsss = os.path.join(store_path,f"{base_name}.txt")
                with open(pathsss,"w") as f:
                    f.write(int_cont)
                st.write("文件已存储")
