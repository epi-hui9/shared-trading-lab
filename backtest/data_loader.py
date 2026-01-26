"""
数据加载器：从各种数据源获取股票历史数据
"""

import pandas as pd
from typing import Optional
from datetime import datetime

# yfinance 是可选的，只在需要时导入
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False


class DataLoader:
    """数据加载器，用于获取股票历史数据"""
    
    def __init__(self):
        self.cache = {}  # 简单的内存缓存
    
    def load_stock_data(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        use_cache: bool = True
    ) -> pd.DataFrame:
        """
        加载股票历史数据
        
        参数:
            symbol: 股票代码（如 'AAPL' 表示苹果公司）
            start_date: 开始日期，格式 'YYYY-MM-DD'
            end_date: 结束日期，格式 'YYYY-MM-DD'
            use_cache: 是否使用缓存
        
        返回:
            DataFrame，包含以下列：
            - Date: 日期
            - Open: 开盘价
            - High: 最高价
            - Low: 最低价
            - Close: 收盘价
            - Volume: 成交量
        """
        cache_key = f"{symbol}_{start_date}_{end_date}"
        
        # 检查缓存
        if use_cache and cache_key in self.cache:
            print(f"使用缓存数据: {symbol}")
            return self.cache[cache_key].copy()
        
        print(f"正在下载数据: {symbol} ({start_date} 到 {end_date})")
        
        if not YFINANCE_AVAILABLE:
            raise ImportError("yfinance 未安装。请运行: pip install yfinance")
        
        try:
            # 使用 yfinance 获取数据
            ticker = yf.Ticker(symbol)
            df = ticker.history(start=start_date, end=end_date)
            
            if df.empty:
                raise ValueError(f"无法获取 {symbol} 的数据，请检查股票代码和日期范围")
            
            # 重置索引，将 Date 作为列
            df.reset_index(inplace=True)
            
            # 确保列名正确
            if 'Date' not in df.columns and 'Datetime' in df.columns:
                df.rename(columns={'Datetime': 'Date'}, inplace=True)
            
            # 选择需要的列
            required_columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
            df = df[required_columns].copy()
            
            # 确保日期格式
            df['Date'] = pd.to_datetime(df['Date'])
            
            # 按日期排序
            df.sort_values('Date', inplace=True)
            df.reset_index(drop=True, inplace=True)
            
            # 缓存数据
            if use_cache:
                self.cache[cache_key] = df.copy()
            
            print(f"成功加载 {len(df)} 条数据")
            return df
            
        except Exception as e:
            raise Exception(f"加载数据失败: {str(e)}")
    
    def validate_data(self, df: pd.DataFrame) -> bool:
        """
        验证数据的完整性
        
        参数:
            df: 数据 DataFrame
        
        返回:
            bool: 数据是否有效
        """
        if df.empty:
            return False
        
        required_columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
        for col in required_columns:
            if col not in df.columns:
                print(f"缺少必需的列: {col}")
                return False
        
        # 检查是否有缺失值
        if df[required_columns].isnull().any().any():
            print("警告: 数据中存在缺失值")
        
        return True
