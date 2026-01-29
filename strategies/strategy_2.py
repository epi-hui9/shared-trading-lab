"""
策略 2：均线 + RSI 策略

策略逻辑：
- 计算短期移动平均线和长期移动平均线
- 计算 RSI（相对强弱指标）
- 买入：均线金叉 + RSI < 50（趋势向上且还没过热）
- 卖出：均线死叉 或 RSI > 70（趋势向下或过热）
"""

import pandas as pd
import numpy as np
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backtest.strategy import BaseStrategy


def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    """
    计算 RSI（相对强弱指标）
    
    参数:
        prices: 价格序列（通常是收盘价）
        period: RSI 周期（默认 14）
    
    返回:
        RSI 值序列（0-100）
    """
    delta = prices.diff()
    
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi


class Strategy2(BaseStrategy):
    """均线 + RSI 策略"""
    
    def __init__(
        self,
        short_window: int = 5,
        long_window: int = 30,
        rsi_period: int = 14,
        rsi_oversold: float = 30.0,
        rsi_overbought: float = 70.0,
        rsi_buy_threshold: float = 50.0
    ):
        """
        初始化策略
        
        参数:
            short_window: 短期移动平均天数（默认 5）
            long_window: 长期移动平均天数（默认 30）
            rsi_period: RSI 计算周期（默认 14）
            rsi_oversold: RSI 超卖阈值（默认 30）
            rsi_overbought: RSI 超买阈值（默认 70）
            rsi_buy_threshold: RSI 买入阈值（默认 50，买入时 RSI 应小于此值）
        """
        super().__init__(
            name="策略 2：均线 + RSI",
            short_window=short_window,
            long_window=long_window,
            rsi_period=rsi_period,
            rsi_oversold=rsi_oversold,
            rsi_overbought=rsi_overbought,
            rsi_buy_threshold=rsi_buy_threshold
        )
        self.short_window = short_window
        self.long_window = long_window
        self.rsi_period = rsi_period
        self.rsi_oversold = rsi_oversold
        self.rsi_overbought = rsi_overbought
        self.rsi_buy_threshold = rsi_buy_threshold
    
    def generate_signals(self) -> pd.DataFrame:
        """
        生成交易信号
        
        返回:
            DataFrame with 'Date' and 'Signal' columns
        """
        if self.data is None:
            raise ValueError("请先使用 set_data() 设置数据")
        
        df = self.data.copy()
        
        # 计算移动平均线
        df['MA_Short'] = df['Close'].rolling(window=self.short_window).mean()
        df['MA_Long'] = df['Close'].rolling(window=self.long_window).mean()
        
        # 计算 RSI
        df['RSI'] = calculate_rsi(df['Close'], period=self.rsi_period)
        
        # 生成信号
        df['Signal'] = 0
        
        for i in range(1, len(df)):
            # 检查是否有足够的数据
            if pd.isna(df.loc[i, 'MA_Short']) or pd.isna(df.loc[i, 'MA_Long']) or pd.isna(df.loc[i, 'RSI']):
                continue
            
            prev_short = df.loc[i-1, 'MA_Short']
            prev_long = df.loc[i-1, 'MA_Long']
            curr_short = df.loc[i, 'MA_Short']
            curr_long = df.loc[i, 'MA_Long']
            curr_rsi = df.loc[i, 'RSI']
            
            # 买入条件：均线金叉 + RSI 还没过热
            is_golden_cross = prev_short <= prev_long and curr_short > curr_long
            is_rsi_ok = curr_rsi < self.rsi_buy_threshold
            
            if is_golden_cross and is_rsi_ok:
                df.loc[i, 'Signal'] = 1  # 买入
            
            # 卖出条件：均线死叉 或 RSI 过热
            is_death_cross = prev_short >= prev_long and curr_short < curr_long
            is_rsi_overbought = curr_rsi > self.rsi_overbought
            
            if is_death_cross or is_rsi_overbought:
                df.loc[i, 'Signal'] = -1  # 卖出
        
        # 返回信号数据
        signals = df[['Date', 'Signal']].copy()
        return signals


if __name__ == '__main__':
    from backtest.engine import BacktestEngine
    
    print("=" * 60)
    print("策略 2：均线 + RSI 回测")
    print("=" * 60)
    print("\n策略说明：")
    print("- 买入：均线金叉 + RSI < 50")
    print("- 卖出：均线死叉 或 RSI > 70")
    print("\n开始回测...\n")
    
    # 创建策略
    strategy = Strategy2(short_window=5, long_window=30)
    
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
