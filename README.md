# 绘九的交易实验室

> 绘九一起做的「股票策略实验室」：支持单只回测和组合回测

## 在线地址（给阿九）

- 固定网址：`https://shared-trading-lab-4wjsslhltjb3zbcgs8hjpt.streamlit.app`

## 项目简介

**绘九的交易实验室** 是一个面向绘和阿九（绘九）的小型股票策略实验工具，支持：

- ✅ **回测任何股票**：支持美股、港股、A股等主要市场的股票（基于 Yahoo Finance）
- ✅ **三种可切换策略**：均线、均线 + RSI、MACD + 成交量
- ✅ **单只回测 & 组合回测**：既可以看单只股票，也可以看一篮子股票的组合净值
- ✅ **中文网页界面**：浏览器打开即可使用，适合非技术背景
- ✅ **详细指标与图表**：总收益率、年化、最大回撤、夏普比率 + 图表下载

## 快速开始

### 本地启动 Web（开发/调试用）

```bash
pip install -r requirements.txt
streamlit run app.py
```

然后在浏览器访问 `http://localhost:8501`。

## 部署与更新（Streamlit Cloud）

- **部署一次**：
  1. 打开 Streamlit Cloud（Streamlit Community Cloud）
  2. 用 GitHub 登录
  3. 点 **New app**
  4. 选择仓库：`shared-trading-lab`
  5. 入口文件（Main file）：`app.py`
  6. 点 **Deploy**

- **以后怎么更新**：
  - 你改代码并 `git push` 后，网页会自动更新
  - 阿九刷新网页就能看到新版本

## 项目结构

```
shared-trading-lab/
├── README.md              # 项目说明
├── requirements.txt       # Python 依赖包
├── app.py                 # 网页版入口（Streamlit）
├── backtest/             # 回测框架核心代码
│   ├── __init__.py
│   ├── engine.py         # 回测引擎
│   ├── strategy.py       # 策略基类
│   └── data_loader.py    # 数据加载器
├── strategies/           # 策略实现
│   ├── __init__.py
│   ├── strategy_1.py     # 策略1：均线策略
│   ├── strategy_2.py     # 策略2：均线 + RSI
│   └── strategy_3.py     # 策略3：MACD + 成交量
├── data/                 # 数据存储
└── logs/                 # 回测结果和日志
```

## 核心功能

### 1. 多市场支持（股票代码格式）

- **美股**：如 `AAPL`（苹果）、`TSLA`（特斯拉）、`MSFT`（微软）
- **港股**：如 `0700.HK`（腾讯）、`9988.HK`（阿里巴巴）
- **A股**：如 `000001.SZ`（平安银行）、`600000.SS`（浦发银行）
- **其他国际市场**：欧洲、日本、澳大利亚等

### 2. 策略系统（像“换衣服”一样切换）

策略就像"衣服"一样可以轻松切换，目前内置 3 个：

- **策略 1：均线策略**  
  - 用两条均线（短期 vs 长期）判断趋势  
  - 短期上穿长期 → 买入；短期下穿长期 → 卖出

- **策略 2：均线 + RSI**  
  - 在策略 1 的基础上，加了一个“热度指标 RSI”  
  - 避免在已经过热的位置买入，减少追高的概率

- **策略 3：MACD + 成交量**  
  - 用 MACD 看“趋势是否在加速”，用成交量看“有没有真金白银在推”  
  - 只有“趋势对”且“有资金推”才考虑上车

### 3. 回测引擎与组合回测

- 自动下载历史数据
- 模拟真实交易（考虑手续费）
- 计算各种性能指标
- 生成可视化图表
- 支持 **单只股票回测** 与 **组合回测（多只股票等权拆分）**

在网页左侧可以选择：

- **回测模式**：单只股票 / 组合（多只股票）
- **策略**：策略 1 / 策略 2 / 策略 3
- **参数**：日期范围、初始资金、手续费、策略参数（均线天数 / RSI / MACD / 成交量等）

## 网页使用示例

1. 安装依赖：

```bash
pip install -r requirements.txt
```

2. 启动网页：

```bash
streamlit run app.py
```

3. 在浏览器中：
   - 选择「单只股票」或「组合（多只股票）」
   - 选股票代码 / 多选一篮子股票
   - 选择时间范围、策略与参数
   - 点击“开始回测”
   - 查看指标、图表，并可下载 PNG 图片

## 常见坑（很短）

- **数据拉取失败**：Yahoo Finance 偶尔会抽风，换股票/换时间段/稍等再试
- **回测很慢**：网页有缓存，同参数第二次会更快
- **组合回测对不齐交易日**：尽量选同一市场（例如都选美股）

## 添加新策略（进阶）

如果之后想一起设计更多策略，可以参考：

1. 在 `strategies/` 目录创建新文件，如 `strategy_4.py`
2. 继承 `BaseStrategy` 类（见 `backtest/strategy.py`）
3. 实现 `generate_signals()` 方法，返回包含 `Date` 和 `Signal` 列的 DataFrame
4. 在 `app.py` 中引入并添加到策略选择里

示例：

```python
from backtest.strategy import BaseStrategy
import pandas as pd

class Strategy2(BaseStrategy):
    def __init__(self, **params):
        super().__init__(name="策略2", **params)
    
    def generate_signals(self) -> pd.DataFrame:
        # 实现你的策略逻辑
        # 返回包含 'Date' 和 'Signal' 列的 DataFrame
        pass
```

## 技术栈

- **Python 3.8+**
- **pandas**: 数据处理
- **numpy**: 数值计算
- **yfinance**: 股票数据获取（Yahoo Finance）
- **streamlit**: 网页界面
- **plotly**: 网页图表与 PNG 导出

## 数据来源

- **Yahoo Finance**：免费、公开的股票历史数据
- 支持大多数主流股票市场
- 数据延迟：A股约30分钟，其他市场实时

## 注意事项

- 这个工具仅用于**回测**（历史数据模拟），不构成任何投资建议
- 回测结果不代表未来表现
- 实盘交易有风险，请谨慎决策
- 需要网络连接以下载股票数据

## 常见问题

### Q: 支持哪些股票？

A: 支持 Yahoo Finance 上有数据的所有股票，包括：
- 美股（如 AAPL, TSLA, MSFT）
- 港股（如 0700.HK, 9988.HK）
- A股（如 000001.SZ, 600000.SS）

### Q: 数据准确吗？

A: 数据来自 Yahoo Finance，是公开的市场数据，一般很准确。但仅供参考，不保证100%准确。

### Q: 可以实盘交易吗？

A: 这个工具只做回测，不涉及实盘交易。如需实盘交易，需要：
- 开证券账户
- 使用券商提供的 API
- 承担真实风险

### Q: 如何添加新策略？

A: 参考 `strategies/strategy_1.py` 的实现，创建新策略文件即可。

## 许可证

本项目仅供学习和研究使用。

---

**绘九的交易实验室** - 让「一起做实验」这件事变得简单
