"""
回测引擎：执行策略回测，计算收益和风险指标
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, Any
from datetime import datetime
import matplotlib.pyplot as plt

from .strategy import BaseStrategy
from .data_loader import DataLoader


class BacktestEngine:
    """回测引擎，执行策略回测并生成报告"""
    
    def __init__(
        self,
        initial_capital: float = 10000.0,
        commission: float = 0.001  # 0.1% 手续费
    ):
        """
        初始化回测引擎
        
        参数:
            initial_capital: 初始资金（默认 10000 元）
            commission: 每次交易的手续费比例（默认 0.1%）
        """
        self.initial_capital = initial_capital
        self.commission = commission
        self.data_loader = DataLoader()
        
        # 回测结果
        self.results: Optional[pd.DataFrame] = None
        self.trades: Optional[pd.DataFrame] = None
        self.portfolio_value: Optional[pd.DataFrame] = None
    
    def run(
        self,
        strategy: BaseStrategy,
        symbol: str,
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """
        运行回测
        
        参数:
            strategy: 交易策略实例
            symbol: 股票代码
            start_date: 开始日期 'YYYY-MM-DD'
            end_date: 结束日期 'YYYY-MM-DD'
        
        返回:
            包含回测结果的字典
        """
        print(f"\n{'='*60}")
        print(f"开始回测: {strategy.name}")
        print(f"股票: {symbol}")
        print(f"时间: {start_date} 到 {end_date}")
        print(f"初始资金: {self.initial_capital:.2f}")
        print(f"{'='*60}\n")
        
        # 1. 加载数据
        data = self.data_loader.load_stock_data(symbol, start_date, end_date)
        
        if not self.data_loader.validate_data(data):
            raise ValueError("数据验证失败")
        
        # 2. 设置数据到策略
        strategy.set_data(data)
        
        # 3. 生成交易信号
        print("正在生成交易信号...")
        signals = strategy.generate_signals()
        
        # 4. 合并数据和信号
        results = data.merge(signals, on='Date', how='left')
        results['Signal'] = results['Signal'].fillna(0).astype(int)
        
        # 5. 执行回测
        print("正在执行回测...")
        portfolio = self._execute_backtest(results)
        
        # 6. 计算指标
        metrics = self._calculate_metrics(portfolio, results)
        
        # 保存结果
        self.results = results
        self.portfolio_value = portfolio
        
        # 7. 打印报告
        self._print_report(metrics)
        
        return {
            'metrics': metrics,
            'portfolio': portfolio,
            'trades': self.trades,
            'results': results
        }
    
    def _execute_backtest(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        执行回测逻辑
        
        参数:
            data: 包含价格和信号的 DataFrame
        
        返回:
            包含每日持仓和资金变化的 DataFrame
        """
        portfolio = pd.DataFrame()
        portfolio['Date'] = data['Date']
        portfolio['Price'] = data['Close']
        portfolio['Signal'] = data['Signal']
        
        # 初始化
        cash = self.initial_capital
        shares = 0
        positions = []  # 记录所有交易
        
        portfolio['Cash'] = 0.0
        portfolio['Shares'] = 0.0  # 改为浮点数，支持小数股
        portfolio['Portfolio_Value'] = 0.0
        portfolio['Returns'] = 0.0
        
        for i in range(len(portfolio)):
            current_price = portfolio.loc[i, 'Price']
            signal = portfolio.loc[i, 'Signal']
            
            # 执行交易
            if signal == 1 and shares == 0:  # 买入信号，且当前没有持仓
                # 计算能买多少股（简化：假设可以买小数股）
                cost = cash * (1 - self.commission)
                shares = cost / current_price
                cash = 0
                positions.append({
                    'Date': portfolio.loc[i, 'Date'],
                    'Type': 'BUY',
                    'Price': current_price,
                    'Shares': shares
                })
            
            elif signal == -1 and shares > 0:  # 卖出信号，且当前有持仓
                cash = shares * current_price * (1 - self.commission)
                positions.append({
                    'Date': portfolio.loc[i, 'Date'],
                    'Type': 'SELL',
                    'Price': current_price,
                    'Shares': shares
                })
                shares = 0
            
            # 计算当前资产价值
            portfolio_value = cash + shares * current_price
            portfolio.loc[i, 'Cash'] = cash
            portfolio.loc[i, 'Shares'] = shares
            portfolio.loc[i, 'Portfolio_Value'] = portfolio_value
            
            # 计算收益率
            if i > 0:
                prev_value = portfolio.loc[i-1, 'Portfolio_Value']
                portfolio.loc[i, 'Returns'] = (portfolio_value - prev_value) / prev_value
        
        # 保存交易记录
        if positions:
            self.trades = pd.DataFrame(positions)
        
        return portfolio
    
    def _calculate_metrics(
        self,
        portfolio: pd.DataFrame,
        data: pd.DataFrame
    ) -> Dict[str, float]:
        """
        计算回测指标
        
        参数:
            portfolio: 回测结果 DataFrame
            data: 原始数据 DataFrame
        
        返回:
            包含各种指标的字典
        """
        final_value = portfolio['Portfolio_Value'].iloc[-1]
        total_return = (final_value - self.initial_capital) / self.initial_capital
        
        # 计算年化收益率
        days = (portfolio['Date'].iloc[-1] - portfolio['Date'].iloc[0]).days
        years = days / 365.25
        annual_return = (1 + total_return) ** (1 / years) - 1 if years > 0 else 0
        
        # 计算波动率（标准差）
        returns = portfolio['Returns'].dropna()
        volatility = returns.std() * np.sqrt(252)  # 年化波动率
        
        # 计算最大回撤
        portfolio_values = portfolio['Portfolio_Value']
        cumulative_max = portfolio_values.expanding().max()
        drawdown = (portfolio_values - cumulative_max) / cumulative_max
        max_drawdown = drawdown.min()
        
        # 计算夏普比率（假设无风险利率为 0）
        sharpe_ratio = annual_return / volatility if volatility > 0 else 0
        
        # 计算交易次数
        num_trades = len(self.trades) if self.trades is not None else 0
        
        # 计算买入持有策略的收益（基准）
        buy_hold_return = (
            (data['Close'].iloc[-1] - data['Close'].iloc[0]) / data['Close'].iloc[0]
        )
        
        return {
            'initial_capital': self.initial_capital,
            'final_value': final_value,
            'total_return': total_return,
            'annual_return': annual_return,
            'volatility': volatility,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'num_trades': num_trades,
            'buy_hold_return': buy_hold_return,
            'excess_return': total_return - buy_hold_return
        }
    
    def _print_report(self, metrics: Dict[str, float]):
        """打印回测报告"""
        print(f"\n{'='*60}")
        print("回测报告")
        print(f"{'='*60}")
        print(f"初始资金:        {metrics['initial_capital']:>12.2f}")
        print(f"最终资金:        {metrics['final_value']:>12.2f}")
        print(f"总收益率:        {metrics['total_return']:>12.2%}")
        print(f"年化收益率:      {metrics['annual_return']:>12.2%}")
        print(f"年化波动率:      {metrics['volatility']:>12.2%}")
        print(f"最大回撤:        {metrics['max_drawdown']:>12.2%}")
        print(f"夏普比率:        {metrics['sharpe_ratio']:>12.2f}")
        print(f"交易次数:        {metrics['num_trades']:>12.0f}")
        print(f"{'-'*60}")
        print(f"买入持有收益:    {metrics['buy_hold_return']:>12.2%}")
        print(f"超额收益:        {metrics['excess_return']:>12.2%}")
        print(f"{'='*60}\n")
    
    def plot_results(self, save_path: Optional[str] = None):
        """
        绘制回测结果图表
        
        参数:
            save_path: 保存路径（可选）
        """
        if self.results is None or self.portfolio_value is None:
            print("请先运行回测")
            return
        
        fig, axes = plt.subplots(3, 1, figsize=(12, 10))
        
        # 图1: 价格和交易信号
        ax1 = axes[0]
        ax1.plot(self.results['Date'], self.results['Close'], label='收盘价', linewidth=1)
        
        # 标记买入点
        buy_signals = self.results[self.results['Signal'] == 1]
        if not buy_signals.empty:
            ax1.scatter(
                buy_signals['Date'], buy_signals['Close'],
                color='green', marker='^', s=100, label='买入', zorder=5
            )
        
        # 标记卖出点
        sell_signals = self.results[self.results['Signal'] == -1]
        if not sell_signals.empty:
            ax1.scatter(
                sell_signals['Date'], sell_signals['Close'],
                color='red', marker='v', s=100, label='卖出', zorder=5
            )
        
        ax1.set_title('股票价格和交易信号', fontsize=14, fontproperties='SimHei')
        ax1.set_ylabel('价格', fontproperties='SimHei')
        ax1.legend(prop={'family': 'SimHei'})
        ax1.grid(True, alpha=0.3)
        
        # 图2: 资产价值变化
        ax2 = axes[1]
        ax2.plot(
            self.portfolio_value['Date'],
            self.portfolio_value['Portfolio_Value'],
            label='策略资产', linewidth=2, color='blue'
        )
        ax2.axhline(
            y=self.initial_capital,
            color='gray', linestyle='--', label='初始资金'
        )
        ax2.set_title('资产价值变化', fontsize=14, fontproperties='SimHei')
        ax2.set_ylabel('资产价值', fontproperties='SimHei')
        ax2.legend(prop={'family': 'SimHei'})
        ax2.grid(True, alpha=0.3)
        
        # 图3: 收益率分布
        ax3 = axes[2]
        returns = self.portfolio_value['Returns'].dropna()
        ax3.plot(self.portfolio_value['Date'], returns, alpha=0.7, linewidth=1)
        ax3.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        ax3.fill_between(
            self.portfolio_value['Date'],
            returns,
            0,
            where=(returns >= 0),
            alpha=0.3,
            color='green',
            label='盈利'
        )
        ax3.fill_between(
            self.portfolio_value['Date'],
            returns,
            0,
            where=(returns < 0),
            alpha=0.3,
            color='red',
            label='亏损'
        )
        ax3.set_title('每日收益率', fontsize=14, fontproperties='SimHei')
        ax3.set_xlabel('日期', fontproperties='SimHei')
        ax3.set_ylabel('收益率', fontproperties='SimHei')
        ax3.legend(prop={'family': 'SimHei'})
        ax3.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"图表已保存到: {save_path}")
        
        # 关闭图表，不显示弹窗
        plt.close()
