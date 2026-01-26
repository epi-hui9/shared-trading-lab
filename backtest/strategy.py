"""
策略基类：所有交易策略都应该继承这个类
"""

from abc import ABC, abstractmethod
import pandas as pd
from typing import Dict, Any, Optional


class BaseStrategy(ABC):
    """策略基类，所有自定义策略都应该继承这个类"""
    
    def __init__(self, name: str, **params):
        """
        初始化策略
        
        参数:
            name: 策略名称
            **params: 策略参数（如移动平均的天数等）
        """
        self.name = name
        self.params = params
        self.data: Optional[pd.DataFrame] = None
        self.signals: Optional[pd.DataFrame] = None
    
    def set_data(self, data: pd.DataFrame):
        """设置要处理的数据"""
        self.data = data.copy()
    
    @abstractmethod
    def generate_signals(self) -> pd.DataFrame:
        """
        生成交易信号
        
        这个方法必须由子类实现。
        应该返回一个 DataFrame，包含以下列：
        - Date: 日期
        - Signal: 交易信号
          - 1: 买入
          - -1: 卖出
          - 0: 持有/不操作
        
        返回:
            DataFrame with 'Date' and 'Signal' columns
        """
        pass
    
    def get_params(self) -> Dict[str, Any]:
        """获取策略参数"""
        return self.params
    
    def set_params(self, **params):
        """更新策略参数"""
        self.params.update(params)
    
    def __repr__(self):
        return f"{self.name}({self.params})"
