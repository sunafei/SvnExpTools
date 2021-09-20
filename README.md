<p align="center">
  <img width="200" style="padding: 0 0" src="http://knowledgebase-oss.oss-cn-beijing.aliyuncs.com/star/svn_tools.svg">
</p>


## 简介
公司提交更新包场景为需要加载项目的svn记录，选择提交记录导出对应的编译后的文件，更新到正式环境
1. 选择源码路径，默认带出编译路径，可修改
2. 点击”加载提交记录“,默认加载100条最近提交记录,双击可查看变更记录
3. 选择某个版本(通过shift可以选择多个)提交记录
4. 点击“导出更新包“,选择导出路径
5. 自动打开导出路径

## 运行方式一
1. 支持python3.7及以上版本,使用PyCharm打开源代码,构建venv环境,配置运行环境即可

## 运行方式二
```shell script
# python3.7及以上版本，项目目录下打开Terminal
# 1. 建立专属于项目的python环境
pip install virtualenv
# 2. 初始化venv文件夹
python -m venv venv
# 3. 进入当前环境
venv\Scripts\activate.bat
# 4. 安装依赖包
pip install -r requirements.txt
# 5. 运行
python src\main.py
```

## 打包(windows)
```shell script
Pyinstaller -w -F main.spec
```

## 注意
- 必须配置svn环境变量，可通过svn help检查命令是否有效
- 因源码结构原因，逻辑并不适用于所有项目