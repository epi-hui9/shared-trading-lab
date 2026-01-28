"""
Shared Trading Lab - Web App (Streamlit)
"""

from __future__ import annotations

import io
import contextlib
from datetime import date

import pandas as pd
import streamlit as st

from backtest.engine import BacktestEngine
from strategies.strategy_1 import Strategy1


st.set_page_config(
    page_title="Shared Trading Lab",
    page_icon="📈",
    layout="wide",
)


def _is_valid_symbol(symbol: str) -> bool:
    return bool(symbol) and len(symbol) <= 20


@st.cache_data(show_spinner=False, ttl=60 * 60)
def _run_backtest_cached(
    symbol: str,
    start_date: str,
    end_date: str,
    initial_capital: float,
    commission: float,
    short_window: int,
    long_window: int,
) -> dict:
    """
    用 Streamlit 缓存（cache）避免重复下载同一份数据。
    注意：只缓存“相同输入参数”的结果。
    """
    strategy = Strategy1(short_window=short_window, long_window=long_window)
    engine = BacktestEngine(initial_capital=initial_capital, commission=commission)
    result = engine.run(strategy=strategy, symbol=symbol, start_date=start_date, end_date=end_date)
    # 为网页后续画图/下载保留 engine 的内部状态
    result["_engine"] = engine
    return result


def main():
    st.title("Shared Trading Lab")
    st.caption("一个通用的股票策略回测工具（Backtest） · 网页版（Web App）")

    with st.sidebar:
        st.header("参数")

        symbol = st.text_input("股票代码（Symbol）", value="AAPL").strip()
        st.caption("例：AAPL / TSLA / 0700.HK / 000001.SZ / 600000.SS")

        col1, col2 = st.columns(2)
        with col1:
            start = st.date_input("开始日期（Start）", value=date(2021, 1, 1))
        with col2:
            end = st.date_input("结束日期（End）", value=date.today())

        st.divider()
        st.subheader("策略（Strategy）")
        st.selectbox("选择策略", options=["Strategy 1：移动平均"], index=0, disabled=True)

        c1, c2 = st.columns(2)
        with c1:
            short_window = st.number_input("短期均线天数", min_value=2, max_value=200, value=5, step=1)
        with c2:
            long_window = st.number_input("长期均线天数", min_value=5, max_value=400, value=30, step=1)

        st.divider()
        st.subheader("交易设置")
        initial_capital = st.number_input("初始资金（Initial Capital）", min_value=100.0, value=10000.0, step=100.0)
        commission = st.number_input("手续费比例（Commission）", min_value=0.0, max_value=0.05, value=0.001, step=0.0005, format="%.4f")

        st.divider()
        run_btn = st.button("开始回测（Run Backtest）", type="primary", use_container_width=True)

    if not run_btn:
        st.info("在左侧填好参数，然后点击 **开始回测**。")
        return

    if not _is_valid_symbol(symbol):
        st.error("股票代码不合法：请检查是否为空/过长。")
        return

    if start >= end:
        st.error("日期范围不合法：开始日期必须早于结束日期。")
        return

    if short_window >= long_window:
        st.warning("提示：通常短期均线应小于长期均线（Short < Long）。你也可以继续跑，但含义会比较怪。")

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
                    short_window=int(short_window),
                    long_window=int(long_window),
                )
        except Exception as e:
            st.error(f"回测失败：{e}")
            st.stop()

    metrics = result["metrics"]
    engine: BacktestEngine = result["_engine"]

    st.success("回测完成。")

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

    st.subheader("图表（Chart）")
    try:
        fig = engine.create_figure()
        st.pyplot(fig, clear_figure=True)

        img_bytes = io.BytesIO()
        fig.savefig(img_bytes, format="png", dpi=200, bbox_inches="tight")
        img_bytes.seek(0)
        st.download_button(
            "下载图表 PNG",
            data=img_bytes,
            file_name=f"{symbol}_{start_str}_{end_str}.png",
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

    with st.expander("查看运行日志（Logs）"):
        st.text(stdout_buf.getvalue() or "(没有日志输出)")


if __name__ == "__main__":
    main()

