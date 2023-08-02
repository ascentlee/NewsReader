from tkinter import Text, Label, StringVar, Frame, Entry, Button, TOP, LEFT, IntVar, Checkbutton, messagebox,Menu,scrolledtext
from tkinterdnd2 import TkinterDnD, DND_FILES
from urllib import request, parse
import requests
import justext
import json
from EN_STOPLIST import stoplist
from win32clipboard import GetClipboardData, OpenClipboard, CloseClipboard, EmptyClipboard
from win32con import CF_TEXT
import webbrowser,re

class FileDropText(scrolledtext.ScrolledText):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.drop_target_register(DND_FILES)
        self.dnd_bind('<<Drop>>', self.on_drop)
        
    def on_drop(self, event):
        files = event.data
        if files:
            file_path = files[1:-1]
            if file_path.endswith(".txt"):
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    # self.delete("1.0", "end")
                    self.insert("1.0", content)
    def get_text(self):
        return self.get("1.0", "end").strip()

class Translator:
    def __init__(self):
        self.access_token = self.get_token()

    def get_token(self):
        tokenUrl = 'https://b2b-api.10jqka.com.cn/gateway/service-mana/app/login-appkey'
        param = {'appId': '62D00B59003C', 'appSecret': '630671328BCD8DC823DB0FC6705C3F55'}
        authResult = requests.post(tokenUrl, data=param)
        authResult = authResult.content
        res = json.loads(authResult)
        access_token = ''
        if 0 == res['flag']:
            access_token = res['data']['access_token']
        return access_token

    def get_txt(self, url):
        lst = []
        try:
            response = requests.get(url)
            paragraphs = justext.justext(response.content, frozenset(stoplist))
            for paragraph in paragraphs:
                if not paragraph.is_boilerplate:
                    lst.append(paragraph.text)
        except Exception as exc:
            messagebox.showwarning('Warning', 'Invalid URL!')
            print(exc)
        return lst

    def translate(self, texts):
        ls = []
        if '' == self.access_token:
            return
        param = {
            'app_id': '62D00B59003C',
            'from': 'en',
            'to': 'zh',
            'domain': 'default',
            'text': json.dumps(texts)
        }

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'open-authorization': 'Bearer ' + self.access_token
        }

        url = 'https://b2b-api.10jqka.com.cn/gateway/arsenal/machineTranslation/batch/get/result'
        response = requests.post(url, headers=headers, data=param)
        Ret = response.content
        res = json.loads(Ret)
        if 0 == res['status_code']:
            res = res['data']
            for rst in res['trans_result']:
                ls.append(rst['dst'])
        return ls


class TextTranslatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("新闻阅读器2.0|By Gordon 403096966")
        self.root.geometry("840x700")
        self.root.attributes("-topmost", True)

        self.var = StringVar()
        self.var.set('Tip:复制网址到下面输入框或者拖动TXT文本到下面文本框看到效果')
        self.url_input = Label(self.root, textvariable=self.var, width=60, height=1, font=("微软雅黑", 12))
        self.url_input.pack()

        self.input_frame = Frame(self.root)
        self.input_frame.pack(side=TOP)
        self.t_url = Entry(self.input_frame, width=70, font=("微软雅黑", 12))
        self.t_url.insert(0, "http://www.chinadaily.com.cn/a/202210/19/WS634f9ad5a310fd2b29e7d604.html")
        self.t_url.pack(side=LEFT, padx=5)
        self.bnt_withdraw = Button(self.input_frame, text="提取文章", width=8, height=1, font=("微软雅黑", 12),command=self.withdraw_prog)
        self.bnt_withdraw.pack(side=TOP, padx=5, pady=2)

        self.text_frame = Frame(self.root)
        self.text_frame.pack(side=TOP)
        self.text = FileDropText(self.text_frame, width=60, height=26, font=("微软雅黑", 12))
        self.text.pack(side=LEFT, fill="both", expand=True)
        self.t_words = Text(self.text_frame, width=20, height=26, font=("微软雅黑", 12))
        self.t_words.pack(side=LEFT)

        self.CheckVar1 = IntVar()
        self.CheckVar2 = IntVar()
        self.btn_frame = Frame(self.root)
        self.btn_frame.pack()
        self.c2 = Checkbutton(self.btn_frame, text="显示译文", font=("微软雅黑", 11), variable=self.CheckVar2, onvalue=1,
                              offvalue=0, height=5, width=8)
        self.c1 = Checkbutton(self.btn_frame, text="中英对照", font=("微软雅黑", 11), variable=self.CheckVar1, onvalue=1,
                              offvalue=0, height=5, width=8,command=self.update_label)

        self.t_url.focus_set()
        self.c2.pack(side=LEFT, padx=10)
        self.c1.pack(side=LEFT, padx=10)
        
        self.open_chinadaily = Button(self.btn_frame, text="中国日报", fg='blue', width=8, height=1, font=("微软雅黑", 12),command=self.open_web)
        self.open_chinadaily.pack(side=LEFT, padx=10)
        
        self.words = Button(self.btn_frame, text="保存生词", fg='blue', width=8, height=1, font=("微软雅黑", 12),command=self.store_words)
        self.words.pack(side=LEFT, padx=10)
        
        self.clear = Button(self.btn_frame, text="重置内容", width=8, height=1, font=("微软雅黑", 12),command=self.clear_words)
        self.clear.pack(side=LEFT, padx=10)
        
        self.translator = Translator()
        
        self.t_url.bind("<Return>", self.withdraw_prog)
        self.menu = Menu(self.root, tearoff=0)
        self.menu.add_command(label="剪切", font=("微软雅黑", 11), command=self.callback1)
        self.menu.add_command(label="复制", font=("微软雅黑", 11), command=self.callback2)
        self.menu.add_command(label="粘贴", font=("微软雅黑", 11), command=self.callback3)
        self.t_url.bind("<Button-3>", self.popup)
        self.menu1 = Menu(self.root, tearoff=0)
        self.menu1.add_command(label="加入生词本", font=("微软雅黑", 11), command=self.callback4)
        self.menu1.add_command(label="在线查字典", font=("微软雅黑", 11), command=self.callback6)
        self.menu1.add_command(label="复制文本", font=("微软雅黑", 11), command=self.callback5)
        self.text.bind("<Button-3>", self.popup1)
        
    def open_web(self):
        webbrowser.open("https://www.chinadaily.com.cn")
        
    def clear_words(self):
        self.text.delete("1.0", "end")
        self.t_words.delete("1.0", "end")
    
    def update_label(self):
        if self.CheckVar1.get() == 1:
            self.bnt_withdraw.config(text="翻译文章",fg='blue')
        else:
            self.bnt_withdraw.config(text="提取文章")
    def withdraw_prog(self,event=None):
        url = self.t_url.get()
        texts = self.translator.get_txt(url)
        self.clear_words()

        if self.CheckVar1.get() == 1 and self.CheckVar2.get() == 0:
            trans = self.translator.translate(texts)
            for s, t in zip(texts, trans):
                self.text.insert("end", "   " + s + "\n" + "   " + t + "\n")
        elif self.CheckVar1.get() == 0 and self.CheckVar2.get() == 1:
            trans = self.translator.translate(texts)
            for tran in trans:
                self.text.insert("end", "   " + tran + "\n")
        elif self.CheckVar1.get() == 1 and self.CheckVar2.get() == 1:
            messagebox.showwarning("Warning", "Can't be selected both!")
        else:
            for text in texts:
                self.text.insert("end", "   " + text + "\n")
    
    def translate_word(self, string):
        url = "https://fanyi.baidu.com/sug"
        data = {
            'kw': string,
        }
        data_url = parse.urlencode(data)
        req = request.Request(url=url, data=data_url.encode('utf-8'))
        response = request.urlopen(req).read()
        res = json.loads(response)
        trans = res['data'][0]['v'].split(';')[0]
        return trans
    
    def store_words(self):
        words = self.t_words.get("1.0", "end-1c")
        with open("newwords.txt", "a+", encoding="utf-8") as f:
            for w in words.split("|"):
                f.write(w.strip() + "\n")
                
    def callback1(self, event=None):
        self.t_url.event_generate('<<Cut>>')

    def callback2(self, event=None):
        self.t_url.event_generate('<<Copy>>')

    def callback3(self, event=None):
        self.t_url.event_generate('<<Paste>>')

    def callback4(self):
        try:
            self.callback5()
            OpenClipboard()
            w = GetClipboardData(CF_TEXT)
            clean_word = re.match("[A-z- ]+", w.decode('utf-8')).group().lower()
            self.t_words.insert('insert', f"{clean_word} {self.translate_word(clean_word)}\n")
            CloseClipboard()
        except Exception as exc:
            print(exc)
            EmptyClipboard()

    def callback5(self, event=None):
        self.text.event_generate('<<Copy>>')

    def callback6(self, event=None):
        self.callback5()
        OpenClipboard()
        w = GetClipboardData(CF_TEXT)
        path = "https://fanyi.baidu.com/#en/zh/"
        name = path + w.decode('utf-8')
        wb = webbrowser.get('windows-default')
        wb.open(name)
        CloseClipboard()
    def popup(self, event):
        self.menu.post(event.x_root, event.y_root)

    def popup1(self, event):
        self.menu1.post(event.x_root, event.y_root)
if __name__ == "__main__":
    root = TkinterDnD.Tk()
    app = TextTranslatorApp(root)
    root.mainloop()
