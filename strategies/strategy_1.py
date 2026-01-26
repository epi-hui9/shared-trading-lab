"""
Strategy 1: 移动平均策略

策略逻辑：
- 计算短期移动平均线（如 5 日）和长期移动平均线（如 30 日）
- 当短期均线上穿长期均线时，买入（金叉）
- 当短期均线下穿长期均线时，卖出（死叉）
"""

import pandas as pd
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backtest.strategy import BaseStrategy


class Strategy1(BaseStrategy):
    """移动平均交叉策略"""
    
    def __init__(self, short_window: int = 5, long_window: int = 30):
        """
        初始化策略
        
        参数:
            short_window: 短期移动平均天数（默认 5）
            long_window: 长期移动平均天数（默认 30）
        """
        super().__init__(
            name="Strategy 1: 移动平均策略",
            short_window=short_window,
            long_window=long_window
        )
        self.short_window = short_window
        self.long_window = long_window
    
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
        
        # 生成信号
        # 1: 买入（短期均线上穿长期均线）
        # -1: 卖出（短期均线下穿长期均线）
        # 0: 持有
        
        df['Signal'] = 0
        
        # 计算均线交叉
        for i in range(1, len(df)):
            # 检查是否有足够的均线数据
            if pd.isna(df.loc[i, 'MA_Short']) or pd.isna(df.loc[i, 'MA_Long']):
                continue
            
            prev_short = df.loc[i-1, 'MA_Short']
            prev_long = df.loc[i-1, 'MA_Long']
            curr_short = df.loc[i, 'MA_Short']
            curr_long = df.loc[i, 'MA_Long']
            
            # 金叉：短期均线上穿长期均线
            if prev_short <= prev_long and curr_short > curr_long:
                df.loc[i, 'Signal'] = 1  # 买入
            
            # 死叉：短期均线下穿长期均线
            elif prev_short >= prev_long and curr_short < curr_long:
                df.loc[i, 'Signal'] = -1  # 卖出
        
        # 返回信号数据
        signals = df[['Date', 'Signal']].copy()
        return signals


# 为了兼容性，保留旧名称
MovingAverageStrategy = Strategy1


if __name__ == '__main__':
    from backtest.engine import BacktestEngine
    
    print("=" * 60)
    print("Strategy 1: 移动平均策略回测")
    print("=" * 60)
    print("\n策略说明：")
    print("- 当 5 日均线上穿 30 日均线时，买入")
    print("- 当 5 日均线下穿 30 日均线时，卖出")
    print("\n开始回测...\n")
    
    # 创建策略
    strategy = Strategy1(short_window=5, long_window=30)
    
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
