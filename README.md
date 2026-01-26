# Shared Trading Lab

> 一个通用的股票策略回测工具 - 可以回测任何股票的历史数据

## 项目简介

**Shared Trading Lab** 是一个功能强大的股票策略回测工具，支持：

- ✅ **回测任何股票**：支持美股、港股、A股等主要市场的股票
- ✅ **灵活的策略系统**：可以轻松切换不同的交易策略
- ✅ **图形化界面**：提供友好的 GUI 界面，无需编程即可使用
- ✅ **详细的分析报告**：自动生成收益率、风险指标、可视化图表等
- ✅ **可打包成 exe**：可以打包成独立的可执行文件，方便分享和使用

## 快速开始

### 方法 1：使用图形界面（推荐）

```bash
python gui.py
```

### 方法 2：命令行使用

```bash
python -m strategies.strategy_1
```

### 方法 3：打包成 exe

```bash
python build_exe.py
```

详细说明见 [如何打包.md](如何打包.md)

## 项目结构

```
shared-trading-lab/
├── README.md              # 项目说明
├── USAGE.md              # 使用指南
├── 如何打包.md           # 打包说明
├── requirements.txt       # Python 依赖包
├── gui.py                 # 图形界面主程序
├── build_exe.py          # 打包脚本
├── backtest/             # 回测框架核心代码
│   ├── __init__.py
│   ├── engine.py         # 回测引擎
│   ├── strategy.py       # 策略基类
│   └── data_loader.py    # 数据加载器
├── strategies/           # 策略实现
│   ├── __init__.py
│   └── strategy_1.py    # 策略1：移动平均策略
├── data/                 # 数据存储
└── logs/                 # 回测结果和日志
```

## 核心功能

### 1. 多市场支持

- **美股**：如 `AAPL`（苹果）、`TSLA`（特斯拉）、`MSFT`（微软）
- **港股**：如 `0700.HK`（腾讯）、`9988.HK`（阿里巴巴）
- **A股**：如 `000001.SZ`（平安银行）、`600000.SS`（浦发银行）
- **其他国际市场**：欧洲、日本、澳大利亚等

### 2. 策略系统

策略就像"衣服"一样可以轻松切换：

- **Strategy 1**：移动平均策略（5日均线 vs 30日均线）
- 更多策略可以轻松添加...

### 3. 回测引擎

- 自动下载历史数据
- 模拟真实交易（考虑手续费）
- 计算各种性能指标
- 生成可视化图表

## 使用示例

### GUI 界面使用

1. 运行 `python gui.py`
2. 输入股票代码（如 `AAPL`）
3. 选择时间段（如 2021-01-01 到 2024-01-01）
4. 选择策略（如 Strategy 1）
5. 点击"开始回测"
6. 查看结果和图表

### 命令行使用

```python
from backtest.engine import BacktestEngine
from strategies.strategy_1 import Strategy1

# 创建策略和引擎
strategy = Strategy1(short_window=5, long_window=30)
engine = BacktestEngine(initial_capital=10000.0)

# 运行回测
results = engine.run(
    strategy=strategy,
    symbol='AAPL',
    start_date='2021-01-01',
    end_date='2024-01-01'
)

# 保存图表
engine.plot_results(save_path='results.png')
```

## 添加新策略

创建新策略非常简单：

1. 在 `strategies/` 目录创建新文件，如 `strategy_2.py`
2. 继承 `BaseStrategy` 类
3. 实现 `generate_signals()` 方法
4. 在 GUI 中添加新策略选项

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
- **matplotlib**: 可视化
- **tkinter**: 图形界面（Python 内置）

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

**Shared Trading Lab** - 让股票策略回测变得简单
