# 部署成公开网页版（Streamlit Cloud）

目标：你 `git push` 后，网页自动更新（Deploy）。

## 1）准备（Repository）

- 把这个仓库设为公开（Public）
- 确保有 `app.py` 和 `requirements.txt`

## 2）上线（Deploy）

1. 打开 Streamlit Cloud（Streamlit Community Cloud）
2. 用 GitHub 登录
3. 点 **New app**
4. 选择你的仓库（Repository）：`shared-trading-lab`
5. 选择入口文件（Main file）：`app.py`
6. 点 **Deploy**

完成后你会得到一个网址（URL），发给阿九就能用。

## 3）以后怎么更新？

- 你只要改代码 → `git push`
- 平台会自动重新部署（Auto Deploy）
- 阿九刷新网页就看到新版本

## 4）常见坑（Terms）

- **依赖安装失败（Dependencies）**：检查 `requirements.txt`
- **数据拉取失败（Data Source）**：Yahoo Finance 偶尔会抽风，换股票/换时间段试试
- **回测很慢（Cache）**：网页里已做缓存，第二次同参数会更快

