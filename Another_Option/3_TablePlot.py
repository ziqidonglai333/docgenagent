import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import streamlit as st
import os

# *-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*

# 设置页面布局
st.set_page_config(page_title = "图表展示PLOT",
                   page_icon = "🛄",
                   layout= "wide",
                   initial_sidebar_state="expanded")

# st.markdown("# 图表展示PLOT")

with st.sidebar:
    st.markdown("# 图表展示PLOT")
    choice_plot = ""
    X = st.number_input(label = "X轴--对象列",placeholder = "X轴--对象列属于表格第几列",value =1)-1
   
    # 创建一个文本输入框，提示用户输入数字列表
    y_input = st.text_input(label = "Y轴--数值列",placeholder = "请Y轴--数值列需要展示的列数，数字之间用“英文逗号,”分隔")
    # 检查用户是否输入了内容
    if y_input:
        # 将输入的字符串按逗号分割，并尝试将每个元素转换为整数
        try:
            # 分割字符串并转换为整数列表
            Y = [int(item.strip())-1 for item in y_input.split(',')]
            if len(Y) ==1:
                choice_plot = "singe"
            else :
                choice_plot = "multi"
            
        except ValueError:
            # 如果转换失败，提示用户输入错误
            st.error("输入包含非数字字符，请确保只输入数字并用逗号分隔。")

    shape = ["line","bar","pie"]
    default_value = shape.index("line")
    option = st.selectbox('选择图形',shape,index = default_value)
    csvfilepath = st.text_area(label = "CSV文件路径",placeholder = "请输入表格的.CSV文件路径")

    plot_button = st.button("图形展示")

# *-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*

def read_table(csv_table_path,X,Y):
    Y.insert(0,X)
    df_table = pd.read_csv(csv_table_path)
    show_df_table = df_table.iloc[:,Y]
    return show_df_table

# *-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*

# 定义针对两列的表格画图
def singe_attri_plot(show_df_table,option):
    # 使用pandas读取CSV文件
    fig,ax = plt.subplots()
    show_np_table = np.array(show_df_table)
    print(show_np_table.shape)
    x = show_np_table[:,0]
    x_name = show_df_table.columns[0]
    y = show_np_table[:,-1]
    y_name = show_df_table.columns[-1]
    print(x,y)
    if option == "bar":
        ax.bar(x,y,color = "blue",width=0.3)
        # plt.xlabel(x_name)
        # plt.ylabel(y_name)
        # plt.bar(x,y,color = "blue",width=0.3)

    elif option == "line":
        # plt.xlabel(x_name,loc = "right")
        # plt.ylabel(y_name,loc = "top")
        # plt.plot(x,y,marker ="o")
        ax.plot(x,y,marker ="o")
            
    elif option == "pie":
        y = y/sum(y)*100
        # plt.pie(y,labels = x)
        ax.pie(y,labels = x)

    # 设置图表标签
    ax.set_xlabel(x_name)
    ax.set_ylabel(y_name)
    ax.set_xticks(np.arange(len(x)))
    ax.set_xticklabels(x)

    # 显示图例
    ax.legend()

    # 返回figure对象
    return fig

# *-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*

# 定义针对三列及以上的表格画图
def multi_attri_plot(show_df_table, option):
    fig, ax = plt.subplots()

    show_np_table = np.array(show_df_table)
    print(show_np_table)
    
    # 使用第一列作为横坐标的名字
    x = show_df_table.iloc[:, 0].tolist()
    x_name = show_df_table.columns[0]
    
    # 准备y数据
    if option == "bar" or "pie":
        y = show_np_table[:, 1:].T  # 转置后每行代表一个属性的所有值
        n = y.shape[0]  # 属性的数量
        width = 0.8 / n  # 每个柱子的宽度
        offset = width / 2  # 柱子位置的偏移量

        for i in range(n):
            # 计算每个柱子的中心位置
            positions = np.arange(len(x)) + i * width - (n * width / 2) + width / 2
            plt.bar(positions, y[i], width=width, label=show_df_table.columns[i + 1])

    elif option == "line":
        y = show_np_table[:, 1:]
        for i in range(y.shape[1]):
            plt.plot(x, y[:, i], marker="o", label=show_df_table.columns[i + 1])

    # # 设置图表标签
    # plt.xlabel(x_name)
    # plt.ylabel('Values')
    # plt.xticks(np.arange(len(x)), x)  # 设置横坐标标签为x的名字
    # plt.legend()  # 显示图例
    # # plt.show()
    # st.pyplot()

    # 设置图表标签
    ax.set_xlabel(x_name)
    ax.set_ylabel('Values')
    ax.set_xticks(np.arange(len(x)))
    ax.set_xticklabels(x)

    # 显示图例
    ax.legend()

    # 返回figure对象
    return fig


# *-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*

col1,col2 = st.columns([1,1])
if plot_button:
    
    if os.path.isdir(csvfilepath):
        st.write("当前路径不正确，请输入正确的.csv文件路径")
    else:
        _, ext = os.path.splitext(csvfilepath)
        # 检查扩展名是否为.csv
        if ext.lower() == '.csv':
            show_df_table = read_table(csvfilepath,X,Y)
              
            with col1:                
                st.write(show_df_table)
                
            with col2:
                # if choice_plot == "singe":
                #     singe_attri_plot(show_df_table,option)
                # else:
                #     if choice_plot == "multi":
                #         multi_attri_plot(show_df_table,option)
                if choice_plot == "singe":
                    fig = singe_attri_plot(show_df_table, option)
                    st.pyplot(fig)
                else:
                    if choice_plot == "multi":
                        fig = multi_attri_plot(show_df_table, option)
                        st.pyplot(fig)
            
        else:
            st.write("当前文件格式不对，请输入正确的.csv文件路径")
    
# /root/autodl-tmp/Rag_test/knowledge_base/sample_data.csv
# /root/autodl-tmp/Rag_test/knowledge_base/sampledata_with_score.csv