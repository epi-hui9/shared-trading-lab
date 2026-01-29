"""
策略 3：MACD + 成交量策略

结合了：
1. MACD（移动平均收敛发散指标）- 趋势指标
2. 成交量确认 - 确保趋势有资金支持

策略逻辑：
- MACD 由三条线组成：
  * MACD 线：12日EMA - 26日EMA（快线减慢线）
  * 信号线：MACD 线的9日EMA
  * 柱状图：MACD 线 - 信号线
- 买入：MACD 线上穿信号线（金叉）+ 成交量放大
- 卖出：MACD 线下穿信号线（死叉）或 MACD 柱状图转负
"""

import pandas as pd
import numpy as np
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backtest.strategy import BaseStrategy


def calculate_ema(prices: pd.Series, period: int) -> pd.Series:
    """
    计算指数移动平均（EMA）
    
    参数:
        prices: 价格序列
        period: 周期
    
    返回:
        EMA 序列
    """
    return prices.ewm(span=period, adjust=False).mean()


def calculate_macd(
    prices: pd.Series,
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """
    计算 MACD 指标
    
    参数:
        prices: 价格序列（通常是收盘价）
        fast_period: 快线周期（默认 12）
        slow_period: 慢线周期（默认 26）
        signal_period: 信号线周期（默认 9）
    
    返回:
        (MACD线, 信号线, 柱状图)
    """
    ema_fast = calculate_ema(prices, fast_period)
    ema_slow = calculate_ema(prices, slow_period)
    
    macd_line = ema_fast - ema_slow
    signal_line = calculate_ema(macd_line, signal_period)
    histogram = macd_line - signal_line
    
    return macd_line, signal_line, histogram


def calculate_volume_ma(volume: pd.Series, period: int = 20) -> pd.Series:
    """
    计算成交量移动平均
    
    参数:
        volume: 成交量序列
        period: 周期（默认 20）
    
    返回:
        成交量移动平均序列
    """
    return volume.rolling(window=period).mean()


class Strategy3(BaseStrategy):
    """MACD + 成交量策略"""
    
    def __init__(
        self,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9,
        volume_ma_period: int = 20,
        volume_threshold: float = 1.2
    ):
        """
        初始化策略
        
        参数:
            fast_period: MACD 快线周期（默认 12）
            slow_period: MACD 慢线周期（默认 26）
            signal_period: MACD 信号线周期（默认 9）
            volume_ma_period: 成交量移动平均周期（默认 20）
            volume_threshold: 成交量放大倍数（默认 1.2，即成交量需超过均量的 1.2 倍）
        """
        super().__init__(
            name="策略 3：MACD + 成交量",
            fast_period=fast_period,
            slow_period=slow_period,
            signal_period=signal_period,
            volume_ma_period=volume_ma_period,
            volume_threshold=volume_threshold
        )
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period
        self.volume_ma_period = volume_ma_period
        self.volume_threshold = volume_threshold
    
    def generate_signals(self) -> pd.DataFrame:
        """
        生成交易信号
        
        返回:
            DataFrame with 'Date' and 'Signal' columns
        """
        if self.data is None:
            raise ValueError("请先使用 set_data() 设置数据")
        
        df = self.data.copy()
        
        # 计算 MACD
        macd_line, signal_line, histogram = calculate_macd(
            df['Close'],
            fast_period=self.fast_period,
            slow_period=self.slow_period,
            signal_period=self.signal_period
        )
        
        df['MACD'] = macd_line
        df['Signal_Line'] = signal_line
        df['Histogram'] = histogram
        
        # 计算成交量移动平均
        df['Volume_MA'] = calculate_volume_ma(df['Volume'], period=self.volume_ma_period)
        
        # 生成信号
        df['Signal'] = 0
        
        for i in range(1, len(df)):
            # 检查是否有足够的数据
            if (pd.isna(df.loc[i, 'MACD']) or 
                pd.isna(df.loc[i, 'Signal_Line']) or 
                pd.isna(df.loc[i, 'Histogram']) or
                pd.isna(df.loc[i, 'Volume_MA'])):
                continue
            
            prev_macd = df.loc[i-1, 'MACD']
            prev_signal = df.loc[i-1, 'Signal_Line']
            curr_macd = df.loc[i, 'MACD']
            curr_signal = df.loc[i, 'Signal_Line']
            curr_histogram = df.loc[i, 'Histogram']
            curr_volume = df.loc[i, 'Volume']
            curr_volume_ma = df.loc[i, 'Volume_MA']
            
            # 买入条件：MACD 金叉 + 成交量放大
            is_golden_cross = prev_macd <= prev_signal and curr_macd > curr_signal
            is_volume_confirmed = curr_volume > (curr_volume_ma * self.volume_threshold)
            
            if is_golden_cross and is_volume_confirmed:
                df.loc[i, 'Signal'] = 1  # 买入
            
            # 卖出条件：MACD 死叉 或 MACD 柱状图转负
            is_death_cross = prev_macd >= prev_signal and curr_macd < curr_signal
            is_histogram_negative = curr_histogram < 0
            
            if is_death_cross or is_histogram_negative:
                df.loc[i, 'Signal'] = -1  # 卖出
        
        # 返回信号数据
        signals = df[['Date', 'Signal']].copy()
        return signals


if __name__ == '__main__':
    from backtest.engine import BacktestEngine
    
    print("=" * 60)
    print("策略 3：MACD + 成交量回测")
    print("=" * 60)
    print("\n策略说明：")
    print("- 买入：MACD 金叉 + 成交量放大（超过均量 1.2 倍）")
    print("- 卖出：MACD 死叉 或 MACD 柱状图转负")
    print("\n开始回测...\n")
    
    # 创建策略
    strategy = Strategy3()
    
    # 创建回测引擎
    engine = BacktestEngine(initial_capital=10000.0, commission=0.001)
    
    # 运行回测
    results = engine.run(
        strategy=strategy,
        symbol='AAPL',
        start_date='2021-01-01',
        end_date='2024-01-01'
    )
    
    # 保存图表
    try:
        engine.plot_results(save_path='backtest_results.png')
    except Exception as e:
        print(f"绘图时出错: {e}")
