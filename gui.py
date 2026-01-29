"""
绘九的交易实验室 - 图形界面
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import os
from datetime import datetime, timedelta

# 导入回测模块
from backtest.engine import BacktestEngine
from strategies.strategy_1 import Strategy1


class TradingLabGUI:
    """回测工具图形界面"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("绘九的交易实验室 - 股票策略回测工具")
        self.root.geometry("800x700")
        
        # 回测引擎
        self.engine = None
        self.results = None
        
        # 创建界面
        self.create_widgets()
    
    def create_widgets(self):
        """创建界面组件"""
        
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 标题
        title_label = ttk.Label(
            main_frame, 
            text="绘九的交易实验室", 
            font=("Arial", 16, "bold")
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=10)
        
        subtitle_label = ttk.Label(
            main_frame, 
            text="股票策略回测工具 - 支持任何股票", 
            font=("Arial", 10)
        )
        subtitle_label.grid(row=1, column=0, columnspan=2, pady=5)
        
        # 分隔线
        separator = ttk.Separator(main_frame, orient='horizontal')
        separator.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        # 股票代码输入
        ttk.Label(main_frame, text="股票代码:", font=("Arial", 10)).grid(
            row=3, column=0, sticky=tk.W, pady=5
        )
        self.symbol_var = tk.StringVar(value="AAPL")
        symbol_frame = ttk.Frame(main_frame)
        symbol_frame.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=5)
        ttk.Entry(symbol_frame, textvariable=self.symbol_var, width=20).pack(side=tk.LEFT, padx=5)
        ttk.Label(symbol_frame, text="(如: AAPL, TSLA, 0700.HK, 000001.SZ)", 
                 font=("Arial", 8), foreground="gray").pack(side=tk.LEFT)
        
        # 开始日期
        ttk.Label(main_frame, text="开始日期:", font=("Arial", 10)).grid(
            row=4, column=0, sticky=tk.W, pady=5
        )
        self.start_date_var = tk.StringVar(value="2021-01-01")
        ttk.Entry(main_frame, textvariable=self.start_date_var, width=20).grid(
            row=4, column=1, sticky=tk.W, pady=5
        )
        
        # 结束日期
        ttk.Label(main_frame, text="结束日期:", font=("Arial", 10)).grid(
            row=5, column=0, sticky=tk.W, pady=5
        )
        end_date = datetime.now().strftime("%Y-%m-%d")
        self.end_date_var = tk.StringVar(value=end_date)
        ttk.Entry(main_frame, textvariable=self.end_date_var, width=20).grid(
            row=5, column=1, sticky=tk.W, pady=5
        )
        
        # 策略选择
        ttk.Label(main_frame, text="策略选择:", font=("Arial", 10)).grid(
            row=6, column=0, sticky=tk.W, pady=5
        )
        self.strategy_var = tk.StringVar(value="Strategy 1")
        strategy_combo = ttk.Combobox(
            main_frame, 
            textvariable=self.strategy_var, 
            values=["Strategy 1: 移动平均策略"],
            state="readonly",
            width=30
        )
        strategy_combo.grid(row=6, column=1, sticky=tk.W, pady=5)
        
        # 策略参数（Strategy 1）
        param_frame = ttk.LabelFrame(main_frame, text="策略参数 (Strategy 1)", padding="5")
        param_frame.grid(row=7, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        ttk.Label(param_frame, text="短期均线天数:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.short_window_var = tk.StringVar(value="5")
        ttk.Entry(param_frame, textvariable=self.short_window_var, width=10).grid(
            row=0, column=1, padx=5
        )
        
        ttk.Label(param_frame, text="长期均线天数:").grid(row=0, column=2, sticky=tk.W, padx=5)
        self.long_window_var = tk.StringVar(value="30")
        ttk.Entry(param_frame, textvariable=self.long_window_var, width=10).grid(
            row=0, column=3, padx=5
        )
        
        # 初始资金
        ttk.Label(main_frame, text="初始资金:", font=("Arial", 10)).grid(
            row=8, column=0, sticky=tk.W, pady=5
        )
        self.capital_var = tk.StringVar(value="10000")
        ttk.Entry(main_frame, textvariable=self.capital_var, width=20).grid(
            row=8, column=1, sticky=tk.W, pady=5
        )
        
        # 按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=9, column=0, columnspan=2, pady=20)
        
        self.run_button = ttk.Button(
            button_frame, 
            text="开始回测", 
            command=self.start_backtest,
            width=20
        )
        self.run_button.pack(side=tk.LEFT, padx=5)
        
        self.save_button = ttk.Button(
            button_frame, 
            text="保存图表", 
            command=self.save_chart,
            width=20,
            state="disabled"
        )
        self.save_button.pack(side=tk.LEFT, padx=5)
        
        # 结果显示区域
        result_frame = ttk.LabelFrame(main_frame, text="回测结果", padding="5")
        result_frame.grid(row=10, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        
        self.result_text = scrolledtext.ScrolledText(
            result_frame, 
            height=15, 
            width=70,
            font=("Courier", 9)
        )
        self.result_text.pack(fill=tk.BOTH, expand=True)
        
        # 进度条
        self.progress = ttk.Progressbar(
            main_frame, 
            mode='indeterminate',
            length=400
        )
        self.progress.grid(row=11, column=0, columnspan=2, pady=10)
        
        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(
            main_frame, 
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        status_bar.grid(row=12, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(10, weight=1)
    
    def start_backtest(self):
        """开始回测"""
        # 获取输入
        symbol = self.symbol_var.get().strip()
        start_date = self.start_date_var.get().strip()
        end_date = self.end_date_var.get().strip()
        
        # 验证输入
        if not symbol:
            messagebox.showerror("错误", "请输入股票代码")
            return
        
        if not start_date or not end_date:
            messagebox.showerror("错误", "请输入开始和结束日期")
            return
        
        try:
            initial_capital = float(self.capital_var.get())
        except ValueError:
            messagebox.showerror("错误", "初始资金必须是数字")
            return
        
        # 禁用按钮
        self.run_button.config(state="disabled")
        self.save_button.config(state="disabled")
        self.progress.start()
        self.status_var.set("正在运行回测...")
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, "正在运行回测，请稍候...\n\n")
        
        # 在新线程中运行回测
        thread = threading.Thread(target=self.run_backtest_thread, daemon=True)
        thread.start()
    
    def run_backtest_thread(self):
        """在后台线程中运行回测"""
        try:
            # 获取参数
            symbol = self.symbol_var.get().strip()
            start_date = self.start_date_var.get().strip()
            end_date = self.end_date_var.get().strip()
            initial_capital = float(self.capital_var.get())
            
            # 创建策略
            strategy_name = self.strategy_var.get()
            if "Strategy 1" in strategy_name:
                short_window = int(self.short_window_var.get())
                long_window = int(self.long_window_var.get())
                strategy = Strategy1(short_window=short_window, long_window=long_window)
            else:
                strategy = Strategy1()  # 默认
            
            # 创建引擎
            self.engine = BacktestEngine(
                initial_capital=initial_capital,
                commission=0.001
            )
            
            # 运行回测
            self.results = self.engine.run(
                strategy=strategy,
                symbol=symbol,
                start_date=start_date,
                end_date=end_date
            )
            
            # 更新界面
            self.root.after(0, self.update_results)
            
        except Exception as e:
            error_msg = f"回测失败: {str(e)}"
            self.root.after(0, lambda: self.show_error(error_msg))
    
    def update_results(self):
        """更新结果显示"""
        self.progress.stop()
        self.run_button.config(state="normal")
        self.save_button.config(state="normal")
        self.status_var.set("回测完成")
        
        # 显示结果
        metrics = self.results['metrics']
        
        result_str = f"""
{'='*60}
回测结果
{'='*60}

股票代码: {self.symbol_var.get()}
时间段: {self.start_date_var.get()} 到 {self.end_date_var.get()}
策略: {self.strategy_var.get()}

核心指标:
  初始资金:        {metrics['initial_capital']:>12.2f}
  最终资金:        {metrics['final_value']:>12.2f}
  总收益率:        {metrics['total_return']:>12.2%}
  年化收益率:      {metrics['annual_return']:>12.2%}
  年化波动率:      {metrics['volatility']:>12.2%}
  最大回撤:        {metrics['max_drawdown']:>12.2%}
  夏普比率:        {metrics['sharpe_ratio']:>12.2f}
  交易次数:        {metrics['num_trades']:>12.0f}

对比基准:
  买入持有收益:    {metrics['buy_hold_return']:>12.2%}
  超额收益:        {metrics['excess_return']:>12.2%}

{'='*60}
"""
        
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, result_str)
        
        # 保存图表
        try:
            os.makedirs('logs', exist_ok=True)
            chart_path = f"logs/backtest_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            self.engine.plot_results(save_path=chart_path)
            self.result_text.insert(tk.END, f"\n图表已保存到: {chart_path}\n")
        except Exception as e:
            self.result_text.insert(tk.END, f"\n图表保存失败: {e}\n")
    
    def show_error(self, error_msg):
        """显示错误"""
        self.progress.stop()
        self.run_button.config(state="normal")
        self.save_button.config(state="disabled")
        self.status_var.set("回测失败")
        messagebox.showerror("错误", error_msg)
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, f"错误: {error_msg}\n")
    
    def save_chart(self):
        """保存图表"""
        if self.engine is None or self.results is None:
            messagebox.showwarning("警告", "请先运行回测")
            return
        
        from tkinter import filedialog
        filename = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                self.engine.plot_results(save_path=filename)
                messagebox.showinfo("成功", f"图表已保存到: {filename}")
            except Exception as e:
                messagebox.showerror("错误", f"保存失败: {e}")


def main():
    """主函数"""
    root = tk.Tk()
    app = TradingLabGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()
