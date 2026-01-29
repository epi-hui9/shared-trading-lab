"""
绘九的交易实验室 - Web App (Streamlit)
"""

from __future__ import annotations

import io
import contextlib
from datetime import date

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


def main():
    st.markdown(
        """
<style>
/* 轻量优雅排版（尽量使用系统内置中文字体，无需额外下载） */
:root {
  --hj-text: rgba(17, 24, 39, 0.95);
  --hj-muted: rgba(107, 114, 128, 1);
  --hj-line: rgba(17, 24, 39, 0.08);
}

html, body, [class*="css"] {
  font-family: "PingFang SC", "Hiragino Sans GB", "Noto Sans SC", "Microsoft YaHei", system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  color: var(--hj-text);
}

.block-container { padding-top: 2.2rem; }

.hj-hero {
  padding: 0.15rem 0 0.95rem 0;
  border-bottom: 1px solid var(--hj-line);
  margin-bottom: 1.1rem;
}
.hj-title {
  font-family: "Songti SC", "STSong", "Noto Serif SC", "Source Han Serif SC", "SimSun", serif;
  font-weight: 600;
  letter-spacing: 0.02em;
  font-size: 2.35rem;
  line-height: 1.18;
  margin: 0 0 0.25rem 0;
}
.hj-subtitle {
  color: var(--hj-muted);
  font-size: 1.02rem;
  letter-spacing: 0.01em;
  margin: 0;
}

/* 手机端：给顶部工具栏留足空间，避免遮住标题（含刘海安全区） */
@media (max-width: 640px) {
  .block-container { padding-top: calc(5.25rem + env(safe-area-inset-top)); }
  .hj-title { font-size: 1.95rem; line-height: 1.22; }
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

        选项列表 = ["手动输入"] + [f"{名称}（{代码}）" for 代码, 名称 in 常见股票列表]
        选择 = st.selectbox("常见股票（可选）", options=选项列表, index=1)

        if 选择 == "手动输入":
            symbol = st.text_input("股票代码", value="AAPL").strip().upper()
            股票名称 = 股票名称表.get(symbol, "未知股票")
            st.caption("例：AAPL / TSLA / 0700.HK / 000001.SZ / 600000.SS")
        else:
            股票名称 = 选择.split("（", 1)[0]
            symbol = 选择.split("（", 1)[1].rstrip("）")

        st.caption(f"当前选择：{股票名称}（{symbol}）")

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

    if not _is_valid_symbol(symbol):
        st.error("股票代码不合法：请检查是否为空/过长。")
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
                result = _run_backtest_cached(
                    symbol=symbol,
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
    engine: BacktestEngine = result["_engine"]

    st.success(f"回测完成：{股票名称}（{symbol}）")

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
        fig1, fig2, fig3 = _build_charts(result["results"], result["portfolio"], 股票代码=symbol, 股票名称=股票名称)
        st.plotly_chart(fig1, use_container_width=True)
        st.plotly_chart(fig2, use_container_width=True)
        st.plotly_chart(fig3, use_container_width=True)

        # 下载：把三张图合成一个 PNG（简单起见：只导出第一张，最关键）
        png_bytes = pio.to_image(fig1, format="png", width=1200, height=600, scale=2)
        st.download_button(
            "下载图表（PNG）",
            data=png_bytes,
            file_name=f"{股票名称}_{symbol}_{start_str}_{end_str}.png",
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

    with st.expander("查看运行日志"):
        st.text(stdout_buf.getvalue() or "(没有日志输出)")


if __name__ == "__main__":
    main()

