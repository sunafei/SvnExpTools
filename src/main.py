import os
import sys
import datetime
import json
import tkinter
from tkinter.font import Font
import xmltodict
import subprocess
import tkinter as t
import tkinter.filedialog
from tkinter import ttk
import shutil
from tkinter import messagebox
import webbrowser

# 工具类 获取content字符串中startStr开头endStr结尾内的字符串内容
def GetMiddleStr(content, startStr, endStr):
    startIndex = content.index(startStr)
    if startIndex >= 0:
        startIndex += len(startStr)
    endIndex = content.index(endStr)
    return content[startIndex:endIndex]


# 工具类 执行cmd命令
def exc_shell(cmd):
    # 执行cmd命令，如果成功，返回(0, 'xxx')；如果失败，返回(1, 'xxx')
    res = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE)  # 使用管道
    result = res.stdout.read()  # 获取输出结果
    res.wait()  # 等待命令执行完成
    res.stdout.close()  # 关闭标准输出
    return result


# 工具类 xml转json
def xml_to_json(xml_str):
    # parse是的xml解析器
    xml_parse = xmltodict.parse(xml_str)
    # json库dumps()是将dict转化成json格式,loads()是将json转化成dict格式。
    # dumps()方法的ident=1,格式化json
    json_str = json.dumps(xml_parse, indent=1)
    return json_str


def select_source():
    filename = t.filedialog.askdirectory()
    source_path.set(filename)
    return


def select_classes():
    filename = t.filedialog.askdirectory()
    classes_path.set(filename)
    return


# 关闭窗口事件
def close_event():
    win.destroy()


# 加载提交记录
def load_log():
    # svninfo = exc_shell("svn info D:\workspace\idea\product\RDSYSEDUV85010003 --xml")
    if len(str(source_path.get())) < 1:
        messagebox.showinfo("错误", "源代码路径不能为空!")
        return
    if len(str(classes_path.get())) < 1:
        messagebox.showinfo("错误", "编译文件路径不能为空!")
        return
    if not os.path.exists(source_path.get()):
        messagebox.showinfo("错误", "源代码路径不存在!")
        return
    if not os.path.exists(classes_path.get()):
        messagebox.showinfo("错误", "编译文件路径不存在!")
        return
    # 根据路径获取svn-url
    try:
        command_update = "svn upgrade " + source_path.get()
        command = "svn info " + source_path.get() + " --xml"
        exc_shell(command_update)
        svninfo = exc_shell(command)
        url_svn.set(GetMiddleStr(str(svninfo), "<url>", "</url>"))
    except:
        messagebox.showinfo("错误", "无法获取svn路径，执行命令[%s]" % (command))
        return
    # svnlog = exc_shell("svn log -l 30 --xml http://172.16.1.2/svn/eplugger/trunk/BEIJING/RDSYSEDUV85010003")
    svnlog = exc_shell("svn log -l 100 --xml " + url_svn.get())
    logJson = json.loads(xml_to_json(svnlog))
    array = logJson.get("log").get("logentry")
    # 每次加载先清空所有记录
    treeItems = tree.get_children()
    for item in treeItems:
        tree.delete(item)
    # 表格展示svn记录
    for i in range(len(array)):
        timeStr = array[i]["date"].split(".")[0].replace("T", " ")
        fd = datetime.datetime.strptime(timeStr, '%Y-%m-%d %H:%M:%S')
        eta = (fd + datetime.timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S")
        tree.insert("", i, values=(array[i]["@revision"], array[i]["author"], eta, array[i]["msg"]))


# 根据包路径和svn路径递归获取源码路径
def recursion_path(classes_root, text):
    if text.endswith(".java"):
        text = text[0:len(text) - 5] + ".class"
    text = text[1:len(text)]
    if not os.path.exists(os.path.join(classes_root, text)):
        start = str(text).find("/")
        if start != -1:
            subText = text[start: len(text)]
            return recursion_path(classes_root, subText)
        else:
            return ''
    else:
        return text


# 执行更新包导出
def exp_update():
    update_path_root_choice = t.filedialog.askdirectory()
    update_path_root = os.path.join(update_path_root_choice, "ROOT")

    classes_path_root = classes_path.get();
    # 获取选择的所有提交记录的
    all_change_log = []
    for item in tree.selection():
        item_text = tree.item(item, "values")
        version = item_text[0]
        svninfo = exc_shell("svn log -r " + version + " -v --xml " + url_svn.get())
        logJson = json.loads(xml_to_json(svninfo))
        array = logJson.get("log").get("logentry").get("paths").get("path")
        if str(array).startswith("{"):
            all_change_log.append(array)
        else:
            for item in array:
                all_change_log.append(item)

    for obj in all_change_log:
        action = obj["@action"]
        text_mods = obj["@text-mods"]
        text = obj["#text"]
        # 如果是删除文件，不做任何动作
        if action == "D":
            continue
        # 如果文件没有后缀是文件夹，不做任何处理
        # 路径必须包含点
        if text.find(".") < 0:
            continue
        is_webroot = "sourcecode" in str(text) and "WebRoot" in str(text)
        # 如果是资源文件,从源代码获取
        if is_webroot:
            startIndex = str(text).index("sourcecode")
            src_code_base = text[startIndex:len(text)]  # 'sourcecode/WebRoot/****'
            source_path_full = os.path.join(source_path.get(), src_code_base)
            fileName = os.path.basename(source_path_full)
            # 生成ROOT下资源文件路径 eg:business/js/projectApply/
            target_code_base = GetMiddleStr(text, "WebRoot", fileName)
            target_path_full = update_path_root + target_code_base
            if not os.path.exists(target_path_full):
                os.makedirs(target_path_full)
            if not os.path.exists(source_path_full):
                continue
            shutil.copy(source_path_full, target_path_full)
        # 如果是java文件，需要找到对应的class文件，如果有内容类 以 xxx$xxx.class体现
        # 无法确认svn路径是否为编译文件，采用向上递归法获取最近的
        elif text.find("/resource/") > -1:
            classes_path_prefix = os.path.join('WEB-INF', 'classes')
            update_path_root_classes = os.path.join(update_path_root, classes_path_prefix)
            classes_path_root_source = classes_path_root
            # 获取编译路径
            classes_path_real = recursion_path(classes_path_root_source, text)
            fileName = os.path.basename(classes_path_real)
            source_path_part = classes_path_real.replace(fileName, "")
            source = os.path.join(classes_path_root_source, classes_path_real)
            target = os.path.join(update_path_root_classes, source_path_part)
            if not os.path.exists(target):
                os.makedirs(target)
            if not os.path.exists(source):
                continue
            shutil.copy(source, target)
        elif text.endswith(".java"):
            classes_path_prefix = os.path.join('WEB-INF', 'classes')
            update_path_root_classes = os.path.join(update_path_root, classes_path_prefix)
            classes_path_root_java = classes_path_root
            # 获取编译路径
            classes_path_real = recursion_path(classes_path_root_java, text)
            fileName = os.path.basename(classes_path_real)
            source_path_part = classes_path_real.replace(fileName, "")
            classes_path_real_dir = os.path.join(classes_path_root_java, source_path_part)
            fileName_un_suffix = fileName.split(".")[0]
            list = os.listdir(classes_path_real_dir)
            for i in range(0, len(list)):
                class_basename = os.path.basename(list[i])
                if fileName_un_suffix + ".class" == class_basename or class_basename.startswith(
                        fileName_un_suffix + "$"):
                    source = os.path.join(classes_path_real_dir, class_basename)
                    target = os.path.join(update_path_root_classes, source_path_part)
                    if not os.path.exists(target):
                        os.makedirs(target)
                    if not os.path.exists(source):
                        continue
                    shutil.copy(source, target)
        elif text.endswith("log4j.properties") or text.endswith("globalMessages.properties"):
            # 如果是log4j.properties或者globalMessages.properties定位到WEB-INFO
            classes_path_root_properties = classes_path_root
            classes_path_prefix = os.path.join('WEB-INF', 'classes')
            update_path_root_classes = os.path.join(update_path_root, classes_path_prefix)
            # 获取编译路径
            classes_path_real = recursion_path(classes_path_root_properties, text)
            fileName = os.path.basename(classes_path_real)
            source_path_part = classes_path_real.replace(fileName, "")
            source = os.path.join(classes_path_root_properties, classes_path_real)
            target = os.path.join(update_path_root_classes, source_path_part)
            if not os.path.exists(target):
                os.makedirs(target)
            if not os.path.exists(source):
                continue
            shutil.copy(source, target)
        else:  # 如果是其他文件 使用源码导出到和ROOT同级
            classes_path_root_other = source_path.get()
            classes_path_real = recursion_path(classes_path_root_other, text)
            fileName = os.path.basename(classes_path_real)
            source_path_part = classes_path_real.replace(fileName, "")
            source = os.path.join(classes_path_root_other, classes_path_real)
            target = os.path.join(update_path_root_choice, source_path_part)
            if not os.path.exists(target):
                os.makedirs(target)
            if not os.path.exists(source):
                continue
            shutil.copy(source, target)
        sysType = sys.platform
        if 'win' in sysType:  # windows和mac打开文件夹不一样
            os.startfile(update_path_root_choice)  # mac下不支持
        else:
            subprocess.call(["open", update_path_root_choice])


def treeviewDoubleClick(event):
    all_change_log = []
    for item in tree.selection():
        item_text = tree.item(item, "values")
        print(item_text[0])  # 输出所选行的第一列的值
        version = item_text[0]
        svninfo = exc_shell("svn log -r " + version + " -v --xml " + url_svn.get())
        logJson = json.loads(xml_to_json(svninfo))
        array = logJson.get("log").get("logentry").get("paths").get("path")
        if str(array).startswith("{"):
            all_change_log.append(array)
        else:
            for item in array:
                all_change_log.append(item)
    print(all_change_log)
    # 每次加载先清空所有记录
    treeItems = tree_log.get_children()
    for item in treeItems:
        tree_log.delete(item)
    for i, log in enumerate(all_change_log):
        action = log["@action"]
        text_mods = log["@text-mods"]
        text = log["#text"]
        text = text[text.index("RDSYSEDU"):len(text)]
        tree_log.insert("", i, values=(action, text))
    tree_log.pack()
    win_top.deiconify()


# 设置导出更新包路径
def set_target_path():
    source_path_full = os.path.join(source_path.get(), "target", "classes")
    classes_path.set(source_path_full)
    return True


def closeTopWindow():
    win_top.withdraw()  # 隐藏窗体
    return


def closeWindow():
    win.destroy()  # 删除窗体
    win_top.destroy()
    return

def openUrl(url):
    webbrowser.open_new(github_link_str)

# 检查svn命令
svn_help = exc_shell("svn help")
if 'checkout' not in str(svn_help) and 'merge' not in str(svn_help):
    messagebox.showinfo("错误", "未安装svn命令环境！")

github_link_str = 'https://github.com/sunafei/SvnExpTools.git'
win = t.Tk()
win.title('svn导出更新包工具')
# win.iconbitmap('icon.ico')
win.geometry('770x440')
win.resizable(0, 0)

source_path = t.StringVar()
source_path.set("")
classes_path = t.StringVar()
classes_path.set("")
url_svn = t.StringVar()
url_svn.set("通过项目路径获取svn远程地址")

srcdir_label = t.Label(win, text='源代码路径：')
srcdir_text = t.Entry(win, textvariable=source_path, width=70, validate="focusout", validatecommand=set_target_path)

srcdir_btn = t.Button(win, heigh=1, width=10, text='选择', command=select_source)
url_text = t.Label(win, text='通过项目路径获取svn远程地址', textvariable=url_svn)

distdir_label = t.Label(win, text='编译文件路径：')
distdir_text = t.Entry(win, textvariable=classes_path, width=70)
distdir_btn = t.Button(win, heigh=1, width=10, text='选择', command=select_classes)
load_btn = t.Button(win, text='加载提交记录', command=load_log, width=15)
# close = t.Button(win, text='关闭', command=close_event, width=15)


# close.grid(row=8, column=2, columnspan=2, pady=5, padx=20)

tree = ttk.Treeview(win, show="headings")  # #创建表格对象
tree["columns"] = ("版本", "日期", "作者", "注释")  # #定义列
tree.column("版本", width=100)  # #设置列
tree.column("日期", width=100)
tree.column("作者", width=150)
tree.column("注释", width=400)

tree.heading("版本", text="版本")
tree.heading("日期", text="日期")
tree.heading("作者", text="作者")
tree.heading("注释", text="注释")

tree.grid(row=10, column=0, columnspan=4, pady=5, padx=10)

exp_btn = t.Button(win, text='导出更新包', command=exp_update, width=15)
exp_btn.grid(row=11, column=1, columnspan=2, pady=2, padx=20)

github_link = t.Label(win, text=github_link_str,
                      font=Font(family='Microsoft YaHei', size=-12, underline=True),
                      fg='#666666', bg='#ebf1f7', cursor='hand2', )
github_link.bind("<Button-1>", openUrl)
# 布局
srcdir_label.grid(row=1, column=0, pady=5, sticky=t.E)
srcdir_text.grid(row=1, column=1, columnspan=2, pady=5)
srcdir_btn.grid(row=1, column=3, pady=5)
distdir_label.grid(row=2, column=0, pady=5, sticky=t.E)
distdir_text.grid(row=2, column=1, columnspan=2, pady=5)
distdir_btn.grid(row=2, column=3, pady=5)
load_btn.grid(row=8, column=1, columnspan=2, pady=5, padx=20)
url_text.grid(row=9, column=0, columnspan=4, pady=0, padx=1)
github_link.grid(row=12, column=0, columnspan=4, pady=2, padx=20, sticky=t.E)
tree.bind('<Double-Button-1>', treeviewDoubleClick)

win_top = t.Tk()
win_top.title('变更记录')
win_top.geometry('750x240')
win_top.withdraw()  # 隐藏窗体
tree_log = ttk.Treeview(win_top, show="headings")  # #创建树状对象
tree_log["columns"] = ("动作", "受影响目录")  # #定义列
tree_log.column("动作", width=50)  # #设置列
tree_log.column("受影响目录", width=1000)
tree_log.heading("动作", text="动作")
tree_log.heading("受影响目录", text="受影响目录")

win_top.protocol('WM_DELETE_WINDOW', closeTopWindow)
win.protocol('WM_DELETE_WINDOW', closeWindow)
win.mainloop()
