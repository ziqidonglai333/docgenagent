from langchain.agents import tool
from langchain_core.runnables import RunnableLambda
import requests
from langchain.agents import AgentExecutor, create_tool_calling_agent, tool,create_react_agent
from langchain_core.messages import HumanMessage,AIMessage,SystemMessage
from langchain_core.prompts import  MessagesPlaceholder,ChatPromptTemplate
from langchain_openai import ChatOpenAI
@tool
def searxng(user_input):
    '''需要从互联网搜索是，使用searxng进行搜索。
    '''
    url = "http://127.0.0.1:6688"
    search_engine_token = "333666999"
    params = {}
    params["token"] = search_engine_token
    params["q"] = user_input
    params["num"] = 10
    params["format"] = "json"
    respond = requests.get(url,params = params)
    responders = []
    if respond.status_code ==200:
        respond.encoding = "utf-8"
        res = respond.json()["results"]
        for a in res:
            b = {"url":a["url"],"title":a["title"],"content":a["content"]}
            print(b)
            print("/n","&&&"*10)
            responders.append(b)
    return responders

# RunnableLambda(searxng).invoke("张学友")

# deepseek_chat模型
llm_ds = ChatOpenAI(
    temperature = 0.6,
    model = "deepseek-chat",
    openai_api_key = "sk-93a7979c03bc493e977c9edbb7c24601",
    openai_api_base= "https://api.deepseek.com",
)

# 智普清颜模型
llm_zp = ChatOpenAI(
    temperature = 1.0,
    model="glm-4",
    openai_api_key="d2e482be31c453838f46321a197d117d.XnlnLgeyA0KFR2wE",
    openai_api_base="https://open.bigmodel.cn/api/paas/v4/"
)

prompt = ChatPromptTemplate.from_messages(    
    [
        ("system","你是一个人工智能助手，按照用户提问，回答问题，不知道时，可以通过搜索引擎搜索，然后根据搜索结果回答"),
        ("placeholder","{chat_history}"),
        ("human", "{user_input}"),
        ("placeholder","{agent_scratchpad}"),
    ]
)

tools = [searxng]
agent = create_tool_calling_agent(llm = llm_ds ,prompt = prompt ,tools = tools)
# agent = create_tool_calling_agent(llm = llm_zp ,prompt = prompt ,tools = tools)
agent_executor = AgentExecutor(agent = agent ,tools =tools,verbose = True)

res = agent_executor.invoke({"user_input":"中国最近三年经济趋势分析"})
print("88"*18)
print(res)
