"""
打包脚本 - 将程序打包成 exe 文件
"""

import os
import sys
import subprocess
import platform


def build_exe():
    """打包成 exe"""
    
    print("=" * 60)
    print("Shared Trading Lab - 打包工具")
    print("=" * 60)
    print()
    
    # 检查 PyInstaller
    try:
        import PyInstaller
        print("✅ PyInstaller 已安装")
    except ImportError:
        print("❌ PyInstaller 未安装")
        print("\n正在安装 PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("✅ PyInstaller 安装完成")
    
    print("\n开始打包...")
    print("-" * 60)
    
    # PyInstaller 命令
    # macOS/Linux 使用 : 分隔，Windows 使用 ;
    import platform
    separator = ":" if platform.system() != "Windows" else ";"
    
    cmd = [
        "pyinstaller",
        "--name=SharedTradingLab",
        "--onefile",
        "--windowed",  # 不显示控制台窗口
        f"--add-data=README.md{separator}.",  # 包含 README
        "gui.py"
    ]
    
    # 添加隐藏导入（如果需要）
    hidden_imports = [
        "yfinance",
        "pandas",
        "numpy",
        "matplotlib",
        "tkinter"
    ]
    
    for imp in hidden_imports:
        cmd.extend(["--hidden-import", imp])
    
    try:
        subprocess.check_call(cmd)
        print("\n" + "=" * 60)
        print("✅ 打包完成！")
        print("=" * 60)
        
        # 根据平台显示不同的文件信息
        system = platform.system()
        if system == "Darwin":  # macOS
            print("\nmacOS 应用程序位置: dist/SharedTradingLab.app")
            print("可执行文件位置: dist/SharedTradingLab")
            print("\n文件大小: 约 100-200 MB")
            print("\n可以将 SharedTradingLab.app 分享给其他 Mac 用户使用")
        elif system == "Windows":
            print("\nexe 文件位置: dist/SharedTradingLab.exe")
            print("\n文件大小: 约 50-100 MB")
            print("\n可以将此文件分享给其他 Windows 用户使用")
        else:
            print("\n可执行文件位置: dist/SharedTradingLab")
            print("\n文件大小: 约 50-100 MB")
        
        print("\n无需安装 Python 即可运行")
        print()
    except subprocess.CalledProcessError as e:
        print(f"\n❌ 打包失败: {e}")
        print("\n请检查错误信息并重试")
        return False
    
    return True


if __name__ == '__main__':
    build_exe()
