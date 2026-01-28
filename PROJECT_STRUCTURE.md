# 项目结构

```
shared-trading-lab/
├── README.md                  # 项目说明文档
├── USAGE.md                   # 使用指南
├── Windows打包教程.md         # Windows 打包说明
├── DEPLOY_STREAMLIT.md        # 部署成公开网页版（Streamlit Cloud）
├── requirements.txt           # Python 依赖包
├── requirements-dev.txt       # 打包依赖（仅打包需要）
├── .gitignore                 # Git 忽略文件
│
├── app.py                     # 网页版入口（Streamlit）⭐
├── gui.py                     # 图形界面主程序 ⭐
├── build_exe.py              # 打包脚本
│
├── backtest/                  # 回测框架核心代码
│   ├── __init__.py
│   ├── engine.py             # 回测引擎
│   ├── strategy.py           # 策略基类
│   └── data_loader.py        # 数据加载器
│
├── strategies/                # 策略实现（可切换）
│   ├── __init__.py
│   └── strategy_1.py         # 策略1：移动平均策略
│
├── data/                      # 数据存储目录
├── logs/                      # 回测结果和日志目录
└── notebooks/                 # 可选：Jupyter notebooks
```

## 核心文件说明

- **gui.py** - 主程序，运行图形界面
- **build_exe.py** - 打包成 exe/app 的脚本
- **backtest/** - 回测框架，处理数据下载、回测计算、结果分析
- **strategies/** - 策略代码，可以添加新策略

## 文档说明

- **README.md** - 项目总览和使用说明
- **USAGE.md** - 详细使用指南
- **Windows打包教程.md** - Windows 系统打包步骤
