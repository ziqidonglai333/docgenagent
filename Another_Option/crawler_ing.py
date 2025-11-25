import requests
import os
from bs4 import BeautifulSoup
from urllib.parse import urlparse

class url_maneger:
    def __init__(self):
        self.old_urls = set()
        self.new_urls = set()

    def add_url(self,url):
        if url is None and len(url)==0:
            return
        if url in self.old_urls and url in self.new_urls:
            return
        self.new_urls.add(url)

    def add_urls(self,urls):
        if urls is None and len(urls) == 0:
            return
        for url in urls:
            self.add_url(url)
                    
    def get_url(self):
        if len(self.new_urls) != 0:
            geturl = self.new_urls.pop()
            self.old_urls.add(geturl)
            return (geturl)
        else:
            return None

def is_valid_url(url):
    result = urlparse(url)
        # 检查scheme（协议）和netloc（网络位置）是否被定义
        # 这通常意味着URL至少包含协议（如http或https）和域名
    if all([result.scheme, result.netloc]):
        return True
    else:
        return False

def crawler_zhrmghgczb(store_path): 
    '''
    功能：爬取财政部发表的相关政策。
    url:财政部网站政策网址链接：https://www.mof.gov.cn/zhengwuxinxi/zhengcefabu/index.htm。
    store_path：爬取文件的存储路径。
    '''
    headers ={"user-agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"}
    
    # *-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*
    # 政策发布页找更新政策的链接
    czbzcfburl = "https://www.mof.gov.cn/zhengwuxinxi/zhengcefabu/index.htm"
    Url_mane = url_maneger()
    urls = []
    wrong_link = []
    czbresp = requests.get(url= czbzcfburl,headers=headers,timeout = 5)
    if czbresp.status_code == 200:
        czbresp.encoding = "utf-8"
        czbresp_text = czbresp.text        
        czbsoup = BeautifulSoup(czbresp_text,"html.parser")
        xwfa_list = czbsoup.find_all("ul",class_ = "xwfb_listbox")
        for xwfa in xwfa_list:
            xwfa1 = xwfa.find_all("a")
            for xwfa2 in xwfa1:
                zcwjlink = xwfa2["href"]
                if  is_valid_url(zcwjlink):
                    urls.append(zcwjlink)
                else:
                    zcwjname = xwfa2["title"]
                    wrong_link.append({zcwjname:zcwjlink})
                    print (f'''错误链接须手工下载：{wrong_link}''')
        print ("*"*39)  
        Url_mane.add_urls(urls)
        print(f"爬取的文件地址：'/n/n'{Url_mane.new_urls}")
           # *-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*
    # 到具体政策页爬取政策
    while Url_mane.new_urls != []:
        zcwjurl = Url_mane.get_url()
        if is_valid_url(zcwjurl):
            resp = requests.get(zcwjurl,"html.parser")
            if resp.status_code == 200:
                resp.encoding = "utf-8"
                url_cont = resp.text
                soup = BeautifulSoup(url_cont,"html.parser")            
                # 获取文件名称和文件内容
                title = soup.find("title").get_text()
                maincontent = soup.find("div",class_ = "box_content")
                con_title = ""
                con_text = ""
                con_titles = maincontent.find_all(class_ = "title_con")            
                for con_title1 in con_titles:
                    con_title += con_title1.get_text()
                    
                con_texts = maincontent.find_all("p")
                for con_text1 in con_texts:
                    con_text += con_text1.get_text()
                
                file_con = con_title+con_text
                print(file_con)

                # *-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*
                # 获取附件地址
                attachmentlinks = []
                aaa = maincontent.find_all(class_ = "gu-download")
                for aa in aaa:
                    bb = aa.find_all("a")
                    for b in bb:
                        if is_valid_url(b['href']):
                            attachmentlinks.append(b['href'])
                        else:
                            ddd = f"{zcwjurl.rsplit('/',1)[0]}/{b['href'].split('/')[-1]}"
                            if is_valid_url(ddd):
                                attachmentlinks.append(ddd)
                    print(attachmentlinks)
                    
                # *-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*
                # 将文件内容写入.txt文件
                if attachmentlinks != []:
                    for attachmentlink in attachmentlinks:
                        file_con += attachmentlink
                filepath = os.path.join(store_path,f"{title}.txt")
                with open(filepath,"w") as file:
                    file.write(file_con) 

                # *-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*      
                # 爬取具体政策的附件
                if attachmentlinks != []:
                    for attachmentlink in attachmentlinks:                     
                        attaresp = requests.get(attachmentlink,"html.parser")
                        if attaresp.headers.get('Content-Type') == 'application/pdf':        
                            url_cont = attaresp.content
                            file_name = os.path.join(store_path,f"{title}附件.pdf")            
                            with open (file_name,"wb") as file:
                                file.write(url_cont)
                                print (f"{title}附件PDF爬取成功")
    
                        if 'application/msword' in attaresp.headers.get('Content-Type') or 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' in attaresp.headers.get('Content-Type'):
                            url_cont = attaresp.content
                            filename = os.path.join(store_path,f"{title}附件.docx") 
                            with open(filename, 'wb') as file:
                                file.write(url_cont)
                                print(f"{title}附件WORD爬取成功")
store_path = "/root/autodl-tmp/Rag_test/knowledge_base/czb"
crawler_zhrmghgczb(store_path)