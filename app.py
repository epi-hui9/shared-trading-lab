"""
绘九的交易实验室 - Web App (Streamlit)
"""

from __future__ import annotations

import io
import contextlib
from datetime import date

import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.io as pio

from backtest.engine import BacktestEngine
from strategies.strategy_1 import Strategy1
from strategies.strategy_2 import Strategy2
from strategies.strategy_3 import Strategy3


st.set_page_config(
    page_title="绘九的交易实验室",
    page_icon="📊",
    layout="wide",
)

常见股票列表 = [
    ("AAPL", "苹果"),
    ("MSFT", "微软"),
    ("TSLA", "特斯拉"),
    ("NVDA", "英伟达"),
    ("AMZN", "亚马逊"),
    ("GOOGL", "谷歌"),
    ("META", "脸书"),
    ("0700.HK", "腾讯控股"),
    ("9988.HK", "阿里巴巴"),
    ("000001.SZ", "平安银行"),
    ("600000.SS", "浦发银行"),
    ("600519.SS", "贵州茅台"),
    ("300750.SZ", "宁德时代"),
]

股票名称表 = {代码: 名称 for 代码, 名称 in 常见股票列表}


def _is_valid_symbol(symbol: str) -> bool:
    return bool(symbol) and len(symbol) <= 20


def _normalize_symbols(symbols: list[str]) -> list[str]:
    cleaned: list[str] = []
    seen: set[str] = set()
    for s in symbols:
        sym = (s or "").strip().upper()
        if not sym:
            continue
        if sym in seen:
            continue
        seen.add(sym)
        cleaned.append(sym)
    return cleaned


def _calc_metrics_like_engine(portfolio: pd.DataFrame, initial_capital: float) -> dict:
    final_value = float(portfolio["Portfolio_Value"].iloc[-1])
    total_return = (final_value - float(initial_capital)) / float(initial_capital)

    days = (portfolio["Date"].iloc[-1] - portfolio["Date"].iloc[0]).days
    years = days / 365.25
    annual_return = (1 + total_return) ** (1 / years) - 1 if years > 0 else 0.0

    returns = portfolio["Returns"].dropna()
    volatility = float(returns.std() * np.sqrt(252)) if len(returns) > 1 else 0.0

    portfolio_values = portfolio["Portfolio_Value"]
    cumulative_max = portfolio_values.expanding().max()
    drawdown = (portfolio_values - cumulative_max) / cumulative_max
    max_drawdown = float(drawdown.min()) if len(drawdown) else 0.0

    sharpe_ratio = float(annual_return / volatility) if volatility > 0 else 0.0

    return {
        "initial_capital": float(initial_capital),
        "final_value": float(final_value),
        "total_return": float(total_return),
        "annual_return": float(annual_return),
        "volatility": float(volatility),
        "max_drawdown": float(max_drawdown),
        "sharpe_ratio": float(sharpe_ratio),
    }


@st.cache_data(show_spinner=False, ttl=60 * 60)
def _run_backtest_cached(
    symbol: str,
    start_date: str,
    end_date: str,
    initial_capital: float,
    commission: float,
    strategy_type: str,
    short_window: int = 5,
    long_window: int = 30,
    rsi_period: int = 14,
    rsi_buy_threshold: float = 50.0,
    rsi_overbought: float = 70.0,
    macd_fast: int = 12,
    macd_slow: int = 26,
    macd_signal: int = 9,
    volume_ma_period: int = 20,
    volume_threshold: float = 1.2,
) -> dict:
    """
    用 Streamlit 缓存避免重复下载同一份数据。
    注意：只缓存“相同输入参数”的结果。
    """
    if strategy_type == "策略 1：均线交叉":
        strategy = Strategy1(short_window=short_window, long_window=long_window)
    elif strategy_type == "策略 2：均线 + RSI":
        strategy = Strategy2(
            short_window=short_window,
            long_window=long_window,
            rsi_period=rsi_period,
            rsi_buy_threshold=rsi_buy_threshold,
            rsi_overbought=rsi_overbought,
        )
    elif strategy_type == "策略 3：MACD + 成交量":
        strategy = Strategy3(
            fast_period=macd_fast,
            slow_period=macd_slow,
            signal_period=macd_signal,
            volume_ma_period=volume_ma_period,
            volume_threshold=volume_threshold,
        )
    else:
        strategy = Strategy1(short_window=short_window, long_window=long_window)
    
    engine = BacktestEngine(initial_capital=initial_capital, commission=commission)
    result = engine.run(strategy=strategy, symbol=symbol, start_date=start_date, end_date=end_date)
    # 为网页后续画图/下载保留 engine 的内部状态
    result["_engine"] = engine
    return result


@st.cache_data(show_spinner=False, ttl=60 * 60)
def _run_portfolio_backtest_cached(
    symbols: tuple[str, ...],
    start_date: str,
    end_date: str,
    initial_capital: float,
    commission: float,
    strategy_type: str,
    short_window: int = 5,
    long_window: int = 30,
    rsi_period: int = 14,
    rsi_buy_threshold: float = 50.0,
    rsi_overbought: float = 70.0,
    macd_fast: int = 12,
    macd_slow: int = 26,
    macd_signal: int = 9,
    volume_ma_period: int = 20,
    volume_threshold: float = 1.2,
) -> dict:
    """
    组合回测（最小可行版）：
    - 初始资金等权拆分到每只股票
    - 每只股票独立执行同一个策略
    - 组合净值 = 各股票净值相加（不做再平衡）
    - 交易日对齐：取共同交易日（inner join）
    """
    if not symbols:
        raise ValueError("请至少选择 1 只股票")

    per_capital = float(initial_capital) / float(len(symbols))
    per_symbol_runs: list[dict] = []

    for sym in symbols:
        # 复用单标的回测逻辑（同一套策略参数）
        single = _run_backtest_cached(
            symbol=sym,
            start_date=start_date,
            end_date=end_date,
            initial_capital=per_capital,
            commission=float(commission),
            strategy_type=strategy_type,
            short_window=int(short_window),
            long_window=int(long_window),
            rsi_period=int(rsi_period),
            rsi_buy_threshold=float(rsi_buy_threshold),
            rsi_overbought=float(rsi_overbought),
            macd_fast=int(macd_fast),
            macd_slow=int(macd_slow),
            macd_signal=int(macd_signal),
            volume_ma_period=int(volume_ma_period),
            volume_threshold=float(volume_threshold),
        )
        single["_symbol"] = sym
        per_symbol_runs.append(single)

    # 合并组合净值（共同交易日）
    value_series = []
    for run in per_symbol_runs:
        pf = run["portfolio"].copy()
        pf["Date"] = pd.to_datetime(pf["Date"])
        s = pf.set_index("Date")["Portfolio_Value"].rename(run["_symbol"])
        value_series.append(s)

    combined = pd.concat(value_series, axis=1, join="inner").sort_index()
    if combined.empty:
        raise ValueError("组合交易日无法对齐（可能混合了不同市场/节假日）。请换一组股票或缩小到同一市场。")

    total_value = combined.sum(axis=1)
    portfolio = pd.DataFrame({"Date": total_value.index, "Portfolio_Value": total_value.values})
    portfolio["Returns"] = portfolio["Portfolio_Value"].pct_change().fillna(0.0)

    metrics = _calc_metrics_like_engine(portfolio, initial_capital=float(initial_capital))

    # 组合层面的“交易次数/买入持有/超额收益”：用每只股票结果聚合（等权）
    per_metrics = [r["metrics"] for r in per_symbol_runs]
    num_trades = int(sum(int(m.get("num_trades", 0)) for m in per_metrics))
    buy_hold_return = float(np.mean([float(m.get("buy_hold_return", 0.0)) for m in per_metrics])) if per_metrics else 0.0
    metrics["num_trades"] = num_trades
    metrics["buy_hold_return"] = buy_hold_return
    metrics["excess_return"] = float(metrics["total_return"] - buy_hold_return)

    # 汇总每只股票的简表，方便网页展示
    per_table_rows = []
    for run in per_symbol_runs:
        m = run["metrics"]
        per_table_rows.append(
            {
                "股票代码": run["_symbol"],
                "股票名称": 股票名称表.get(run["_symbol"], "未知股票"),
                "总收益率": float(m.get("total_return", 0.0)),
                "年化收益率": float(m.get("annual_return", 0.0)),
                "最大回撤": float(m.get("max_drawdown", 0.0)),
                "夏普比率": float(m.get("sharpe_ratio", 0.0)),
                "交易次数": int(m.get("num_trades", 0)),
            }
        )
    per_table = pd.DataFrame(per_table_rows)

    return {
        "metrics": metrics,
        "portfolio": portfolio,
        "per_symbol_table": per_table,
        "symbols": list(symbols),
        # 为了保持结构一致，仍返回 results（用于页面“数据预览”）
        "results": portfolio.copy(),
    }


def _build_charts(
    results_df: pd.DataFrame,
    portfolio_df: pd.DataFrame,
    股票代码: str,
    股票名称: str,
) -> tuple[go.Figure, go.Figure, go.Figure]:
    """
    生成三张图（纯中文标签）：
    1）价格 + 买卖点
    2）资产曲线
    3）每日收益率
    """
    df = results_df.copy()
    pf = portfolio_df.copy()

    df["Date"] = pd.to_datetime(df["Date"])
    pf["Date"] = pd.to_datetime(pf["Date"])

    # 图1：价格 + 买卖点
    fig1 = go.Figure()
    fig1.add_trace(
        go.Scatter(
            x=df["Date"],
            y=df["Close"],
            mode="lines",
            name="收盘价",
            line=dict(width=1),
        )
    )
    buys = df[df["Signal"] == 1]
    sells = df[df["Signal"] == -1]
    if not buys.empty:
        fig1.add_trace(
            go.Scatter(
                x=buys["Date"],
                y=buys["Close"],
                mode="markers",
                name="买入",
                marker=dict(color="green", symbol="triangle-up", size=10),
            )
        )
    if not sells.empty:
        fig1.add_trace(
            go.Scatter(
                x=sells["Date"],
                y=sells["Close"],
                mode="markers",
                name="卖出",
                marker=dict(color="red", symbol="triangle-down", size=10),
            )
        )
    fig1.update_layout(
        title=f"{股票名称}（{股票代码}）价格与买卖点",
        xaxis_title="日期",
        yaxis_title="价格",
        legend_title="图例",
        margin=dict(l=10, r=10, t=50, b=10),
        height=360,
    )

    # 图2：资产曲线
    fig2 = go.Figure()
    fig2.add_trace(
        go.Scatter(
            x=pf["Date"],
            y=pf["Portfolio_Value"],
            mode="lines",
            name="总资产",
            line=dict(width=2, color="#1f77b4"),
        )
    )
    fig2.update_layout(
        title=f"{股票名称}（{股票代码}）资产曲线",
        xaxis_title="日期",
        yaxis_title="资产",
        legend_title="图例",
        margin=dict(l=10, r=10, t=50, b=10),
        height=300,
    )

    # 图3：每日收益率
    fig3 = go.Figure()
    fig3.add_trace(
        go.Scatter(
            x=pf["Date"],
            y=pf["Returns"],
            mode="lines",
            name="每日收益率",
            line=dict(width=1),
        )
    )
    fig3.add_hline(y=0, line_width=1, line_color="black")
    fig3.update_layout(
        title=f"{股票名称}（{股票代码}）每日收益率",
        xaxis_title="日期",
        yaxis_title="收益率",
        legend_title="图例",
        margin=dict(l=10, r=10, t=50, b=10),
        height=300,
    )

    return fig1, fig2, fig3


def _build_portfolio_charts(portfolio_df: pd.DataFrame, 标题: str) -> tuple[go.Figure, go.Figure]:
    pf = portfolio_df.copy()
    pf["Date"] = pd.to_datetime(pf["Date"])

    fig_equity = go.Figure()
    fig_equity.add_trace(
        go.Scatter(x=pf["Date"], y=pf["Portfolio_Value"], mode="lines", name="组合总资产", line=dict(width=2))
    )
    fig_equity.update_layout(
        title=f"{标题}组合资产曲线",
        xaxis_title="日期",
        yaxis_title="资产",
        legend_title="图例",
        margin=dict(l=10, r=10, t=50, b=10),
        height=340,
    )

    fig_ret = go.Figure()
    fig_ret.add_trace(
        go.Scatter(x=pf["Date"], y=pf["Returns"], mode="lines", name="组合每日收益率", line=dict(width=1))
    )
    fig_ret.add_hline(y=0, line_width=1, line_color="black")
    fig_ret.update_layout(
        title=f"{标题}组合每日收益率",
        xaxis_title="日期",
        yaxis_title="收益率",
        legend_title="图例",
        margin=dict(l=10, r=10, t=50, b=10),
        height=300,
    )

    return fig_equity, fig_ret


def main():
    st.markdown(
        """
<style>
/* 在线字体（有降级方案；加载失败也不影响显示） */
@import url("https://fonts.googleapis.com/css2?family=ZCOOL+QingKe+HuangYou&family=Noto+Sans+SC:wght@400;600&display=swap");

/* 轻量优雅排版（尽量使用系统内置中文字体，无需额外下载） */
:root {
  --hj-text: rgba(17, 24, 39, 0.95);
  --hj-muted: rgba(107, 114, 128, 1);
  --hj-line: rgba(17, 24, 39, 0.08);
  --hj-neon-1: rgba(255, 90, 159, 0.55);
  --hj-neon-2: rgba(88, 215, 255, 0.45);
  --hj-hero-bg: radial-gradient(1200px 420px at 20% 10%, rgba(255, 90, 159, 0.20), transparent 55%),
                radial-gradient(900px 380px at 80% 0%, rgba(88, 215, 255, 0.18), transparent 55%),
                linear-gradient(180deg, rgba(12, 14, 20, 0.96), rgba(8, 10, 15, 0.98));
}

html, body, [class*="css"] {
  font-family: "Noto Sans SC", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  color: var(--hj-text);
}

.block-container {
  /* 桌面端也给顶部导航多留更大的空间，避免被 Streamlit 顶栏遮住 */
  padding-top: calc(6rem + env(safe-area-inset-top));
}

.hj-hero {
  padding: 1.05rem 1.05rem 1.05rem 1.05rem;
  margin: 0 0 1.1rem 0;
  border-radius: 18px;
  background: var(--hj-hero-bg);
  border: 1px solid rgba(255, 255, 255, 0.10);
  box-shadow:
    0 18px 55px rgba(0, 0, 0, 0.35),
    inset 0 1px 0 rgba(255, 255, 255, 0.08);
}
.hj-title {
  /* “招牌感”：略夸张但不浮夸，失败就回退到常规字体 */
  font-family: "ZCOOL QingKe HuangYou", "Songti SC", "STSong", "Noto Serif SC", "SimSun", serif;
  font-weight: 400;
  letter-spacing: 0.04em;
  font-size: 2.65rem;
  line-height: 1.06;
  margin: 0 0 0.25rem 0;
  color: rgba(255, 255, 255, 0.95);
  text-shadow:
    0 0 6px rgba(255, 255, 255, 0.22),
    0 0 18px var(--hj-neon-1),
    0 0 32px var(--hj-neon-2);
}
.hj-subtitle {
  color: rgba(255, 255, 255, 0.78);
  font-size: 1.02rem;
  letter-spacing: 0.02em;
  margin: 0;
}

/* 手机端：给顶部工具栏留足空间，避免遮住标题（含刘海安全区） */
@media (max-width: 640px) {
  .block-container { padding-top: calc(5.25rem + env(safe-area-inset-top)); }
  .hj-hero { border-radius: 16px; padding: 0.95rem 0.95rem; }
  .hj-title { font-size: 2.15rem; line-height: 1.10; }
  .hj-subtitle { font-size: 0.98rem; }
}
</style>
<div class="hj-hero">
  <div class="hj-title">绘九的交易实验室</div>
  <div class="hj-subtitle">一个通用的股票策略回测工具 · 网页版</div>
</div>
""",
        unsafe_allow_html=True,
    )

    with st.expander("说明", expanded=False):
        st.markdown(
            """
**策略 1：均线交叉**
- 使用两条均线：短期均线与长期均线
- 买入：短期均线从下向上穿过长期均线
- 卖出：短期均线从上向下穿过长期均线
- 其它时间：不交易

**策略 2：均线 + RSI**
- 使用两条均线 + RSI（相对强弱指标）
- 买入：均线金叉 + RSI < 70（趋势向上且不在超买区）
- 卖出：均线死叉 或 RSI > 75（趋势向下或过热）
- 优势：减少假信号，避免在过热时买入，避免过早卖出

**策略 3：MACD + 成交量**
- 使用 MACD（趋势指标）+ 成交量确认
- MACD 由三条线组成：MACD 线、信号线、柱状图
- 买入：MACD 金叉 + 成交量放大（确认有资金支持）
- 卖出：MACD 死叉 或 MACD 柱状图转负
- 优势：结合趋势和资金流向，减少假信号

**策略 3 详细说明：**
- **MACD 是什么？** MACD 线 = 快线 - 慢线（快线是最近 12 天平均，慢线是最近 26 天平均）。如果 MACD 线 > 0，说明最近比过去涨得更快；如果 < 0，说明最近比过去跌得更快。
- **信号线是什么？** 信号线是 MACD 线的 9 天平均，让 MACD 线更平滑，更容易看出趋势。
- **金叉/死叉是什么？** 金叉 = MACD 线从下往上穿过信号线（上涨趋势刚刚启动）；死叉 = MACD 线从上往下穿过信号线（上涨趋势开始减弱）。
- **成交量放大是什么？** 今天的成交量 > 过去 20 天平均成交量 × 1.2 倍，说明有真金白银在推，不是小打小闹。
- **柱状图是什么？** 柱状图 = MACD 线 - 信号线。如果柱状图从正数变成负数，说明上涨的力度用完了。
- **为什么这样设计？** 只有"趋势对"（MACD 金叉）且"有资金推"（成交量放大）才买入；一旦"趋势减弱"（死叉）或"力度用完"（柱状图转负）就卖出。

**三张图**
- 价格与买卖点：看什么时候买/卖
- 资产曲线：看总体赚钱情况与回撤
- 每日收益率：看每天波动大小
"""
        )

    with st.sidebar:
        st.header("参数设置")

        模式 = st.radio("回测模式", options=["单只股票", "组合（多只股票）"], horizontal=True, index=0)

        if 模式 == "单只股票":
            选项列表 = ["手动输入"] + [f"{名称}（{代码}）" for 代码, 名称 in 常见股票列表]
            选择 = st.selectbox("常见股票（可选）", options=选项列表, index=1)

            if 选择 == "手动输入":
                symbol = st.text_input("股票代码", value="AAPL").strip().upper()
                股票名称 = 股票名称表.get(symbol, "未知股票")
                st.caption("例：AAPL / TSLA / 0700.HK / 000001.SZ / 600000.SS")
            else:
                股票名称 = 选择.split("（", 1)[0]
                symbol = 选择.split("（", 1)[1].rstrip("）")

            symbols = [symbol]
            st.caption(f"当前选择：{股票名称}（{symbol}）")
        else:
            st.caption("提示：尽量选同一市场的股票（例如都选美股），这样交易日更容易对齐。")
            默认选择 = [f"{名称}（{代码}）" for 代码, 名称 in 常见股票列表[:4]]
            多选 = st.multiselect("选择多只股票（可多选）", options=[f"{名称}（{代码}）" for 代码, 名称 in 常见股票列表], default=默认选择)
            额外 = st.text_input("补充股票代码（可选，逗号分隔）", value="").strip()

            chosen_codes = []
            for item in 多选:
                chosen_codes.append(item.split("（", 1)[1].rstrip("）"))
            if 额外:
                for s in 额外.split(","):
                    chosen_codes.append(s)

            symbols = _normalize_symbols(chosen_codes)
            if not symbols:
                symbols = ["AAPL"]

            names = [f"{股票名称表.get(s, '未知股票')}（{s}）" for s in symbols]
            st.caption("当前选择：" + "、".join(names))

        col1, col2 = st.columns(2)
        with col1:
            start = st.date_input("开始日期", value=date(2021, 1, 1))
        with col2:
            end = st.date_input("结束日期", value=date.today())

        st.divider()
        st.subheader("策略")
        策略选择 = st.selectbox("选择策略", options=["策略 1：均线交叉", "策略 2：均线 + RSI", "策略 3：MACD + 成交量"], index=2)

        # 策略 1 和 2 的均线参数
        if 策略选择 in ["策略 1：均线交叉", "策略 2：均线 + RSI"]:
            c1, c2 = st.columns(2)
            with c1:
                if 策略选择 == "策略 2：均线 + RSI":
                    short_window = st.number_input("短期均线天数", min_value=2, max_value=200, value=10, step=1)
                else:
                    short_window = st.number_input("短期均线天数", min_value=2, max_value=200, value=5, step=1)
            with c2:
                long_window = st.number_input("长期均线天数", min_value=5, max_value=400, value=30, step=1)
        else:
            short_window = 5
            long_window = 30
        
        # 策略 2 的 RSI 参数
        if 策略选择 == "策略 2：均线 + RSI":
            st.caption("RSI 参数（策略 2）")
            rsi_col1, rsi_col2, rsi_col3 = st.columns(3)
            with rsi_col1:
                rsi_period = st.number_input("RSI 周期", min_value=5, max_value=30, value=14, step=1)
            with rsi_col2:
                rsi_buy_threshold = st.number_input("买入 RSI 阈值", min_value=50.0, max_value=85.0, value=70.0, step=5.0, help="RSI 低于此值时才买入，避免过热时买入")
            with rsi_col3:
                rsi_overbought = st.number_input("卖出 RSI 阈值", min_value=60.0, max_value=90.0, value=75.0, step=5.0, help="RSI 超过此值时卖出，避免过早卖出")
        else:
            rsi_period = 14
            rsi_buy_threshold = 70.0
            rsi_overbought = 75.0
        
        # 策略 3 的 MACD 参数
        if 策略选择 == "策略 3：MACD + 成交量":
            st.caption("MACD 参数（策略 3）")
            macd_col1, macd_col2, macd_col3 = st.columns(3)
            with macd_col1:
                macd_fast = st.number_input("MACD 快线周期", min_value=5, max_value=30, value=12, step=1, help="默认 12")
            with macd_col2:
                macd_slow = st.number_input("MACD 慢线周期", min_value=15, max_value=50, value=26, step=1, help="默认 26")
            with macd_col3:
                macd_signal = st.number_input("MACD 信号线周期", min_value=5, max_value=20, value=9, step=1, help="默认 9")
            
            st.caption("成交量参数（策略 3）")
            vol_col1, vol_col2 = st.columns(2)
            with vol_col1:
                volume_ma_period = st.number_input("成交量均线周期", min_value=10, max_value=50, value=20, step=1, help="计算成交量移动平均的周期")
            with vol_col2:
                volume_threshold = st.number_input("成交量放大倍数", min_value=1.0, max_value=3.0, value=1.2, step=0.1, format="%.1f", help="成交量需超过均量的倍数，默认 1.2 倍")
        else:
            macd_fast = 12
            macd_slow = 26
            macd_signal = 9
            volume_ma_period = 20
            volume_threshold = 1.2

        st.divider()
        st.subheader("交易设置")
        initial_capital = st.number_input("初始资金", min_value=100.0, value=10000.0, step=100.0)
        commission = st.number_input("手续费比例", min_value=0.0, max_value=0.05, value=0.001, step=0.0005, format="%.4f")

        st.divider()
        run_btn = st.button("开始回测", type="primary", use_container_width=True)

    if not run_btn:
        st.info("在左侧填好参数，然后点击 **开始回测**。")
        return

    for s in symbols:
        if not _is_valid_symbol(s):
            st.error(f"股票代码不合法：{s}（请检查是否为空/过长）")
            return
    if 模式 != "单只股票" and len(symbols) < 2:
        st.error("组合回测至少需要选择 2 只股票。")
        return

    if start >= end:
        st.error("日期范围不合法：开始日期必须早于结束日期。")
        return

    if 策略选择 in ["策略 1：均线交叉", "策略 2：均线 + RSI"]:
        if short_window >= long_window:
            st.warning("提示：通常短期均线应小于长期均线。你也可以继续跑，但含义可能不太符合常见用法。")

    start_str = start.strftime("%Y-%m-%d")
    end_str = end.strftime("%Y-%m-%d")

    # 捕获 console 输出，放到网页里可展开查看
    stdout_buf = io.StringIO()
    with st.spinner("正在下载数据并回测...（第一次会更慢）"):
        try:
            with contextlib.redirect_stdout(stdout_buf):
                if 模式 == "单只股票":
                    result = _run_backtest_cached(
                        symbol=symbols[0],
                        start_date=start_str,
                        end_date=end_str,
                        initial_capital=float(initial_capital),
                        commission=float(commission),
                        strategy_type=策略选择,
                        short_window=int(short_window),
                        long_window=int(long_window),
                        rsi_period=int(rsi_period),
                        rsi_buy_threshold=float(rsi_buy_threshold),
                        rsi_overbought=float(rsi_overbought),
                        macd_fast=int(macd_fast),
                        macd_slow=int(macd_slow),
                        macd_signal=int(macd_signal),
                        volume_ma_period=int(volume_ma_period),
                        volume_threshold=float(volume_threshold),
                    )
                else:
                    result = _run_portfolio_backtest_cached(
                        symbols=tuple(symbols),
                        start_date=start_str,
                        end_date=end_str,
                        initial_capital=float(initial_capital),
                        commission=float(commission),
                        strategy_type=策略选择,
                        short_window=int(short_window),
                        long_window=int(long_window),
                        rsi_period=int(rsi_period),
                        rsi_buy_threshold=float(rsi_buy_threshold),
                        rsi_overbought=float(rsi_overbought),
                        macd_fast=int(macd_fast),
                        macd_slow=int(macd_slow),
                        macd_signal=int(macd_signal),
                        volume_ma_period=int(volume_ma_period),
                        volume_threshold=float(volume_threshold),
                    )
        except Exception as e:
            st.error(f"回测失败：{e}")
            st.stop()

    metrics = result["metrics"]
    engine: BacktestEngine | None = result.get("_engine")

    if 模式 == "单只股票":
        股票名称 = 股票名称表.get(symbols[0], "未知股票")
        st.success(f"回测完成：{股票名称}（{symbols[0]}）")
    else:
        st.success(f"回测完成：组合（{len(symbols)} 只股票）")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("总收益率", f"{metrics['total_return']:.2%}")
    m2.metric("年化收益率", f"{metrics['annual_return']:.2%}")
    m3.metric("最大回撤", f"{metrics['max_drawdown']:.2%}")
    m4.metric("夏普比率", f"{metrics['sharpe_ratio']:.2f}")

    st.subheader("更多指标")
    st.write(
        {
            "初始资金": float(metrics["initial_capital"]),
            "最终资金": float(metrics["final_value"]),
            "年化波动率": float(metrics["volatility"]),
            "交易次数": int(metrics["num_trades"]),
            "买入持有收益": float(metrics["buy_hold_return"]),
            "超额收益": float(metrics["excess_return"]),
        }
    )

    st.subheader("图表")
    try:
        if 模式 == "单只股票":
            fig1, fig2, fig3 = _build_charts(result["results"], result["portfolio"], 股票代码=symbols[0], 股票名称=股票名称)
            st.plotly_chart(fig1, use_container_width=True)
            st.plotly_chart(fig2, use_container_width=True)
            st.plotly_chart(fig3, use_container_width=True)

            # 下载：只导出第一张（价格与买卖点）
            png_bytes = pio.to_image(fig1, format="png", width=1200, height=600, scale=2)
            st.download_button(
                "下载图表（PNG）",
                data=png_bytes,
                file_name=f"{股票名称}_{symbols[0]}_{start_str}_{end_str}.png",
                mime="image/png",
                use_container_width=True,
            )
        else:
            fig_equity, fig_ret = _build_portfolio_charts(result["portfolio"], 标题="绘九的交易实验室 · ")
            st.plotly_chart(fig_equity, use_container_width=True)
            st.plotly_chart(fig_ret, use_container_width=True)

            png_bytes = pio.to_image(fig_equity, format="png", width=1200, height=600, scale=2)
            st.download_button(
                "下载图表（PNG）",
                data=png_bytes,
                file_name=f"组合_{len(symbols)}只_{start_str}_{end_str}.png",
                mime="image/png",
                use_container_width=True,
            )
    except Exception as e:
        st.warning(f"图表生成失败：{e}")

    st.subheader("数据预览")
    results_df = result["results"].copy()
    # Date 列太长的话，网页显示会很挤
    if "Date" in results_df.columns:
        results_df["Date"] = pd.to_datetime(results_df["Date"]).dt.strftime("%Y-%m-%d")
    st.dataframe(results_df.head(50), use_container_width=True)

    if 模式 != "单只股票":
        st.subheader("每只股票的结果（等权拆分资金，独立运行）")
        per_table = result.get("per_symbol_table")
        if isinstance(per_table, pd.DataFrame) and not per_table.empty:
            show_table = per_table.copy()
            for col in ["总收益率", "年化收益率", "最大回撤"]:
                if col in show_table.columns:
                    show_table[col] = show_table[col].map(lambda x: f"{x:.2%}")
            if "夏普比率" in show_table.columns:
                show_table["夏普比率"] = show_table["夏普比率"].map(lambda x: f"{x:.2f}")
            st.dataframe(show_table, use_container_width=True)

    with st.expander("查看运行日志"):
        st.text(stdout_buf.getvalue() or "(没有日志输出)")


if __name__ == "__main__":
    main()

