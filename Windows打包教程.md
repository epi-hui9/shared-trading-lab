# Windows 打包教程

## 步骤

1. 在 Windows 电脑上打开项目文件夹

2. 安装 Python（如果还没安装）：
   - 下载：https://www.python.org/downloads/
   - 安装时勾选 "Add Python to PATH"

3. 安装依赖：
   ```bash
   pip install -r requirements.txt
   pip install pyinstaller
   ```

4. 运行打包：
   ```bash
   python build_exe.py
   ```

5. 完成！exe 文件在 `dist/SharedTradingLab.exe`

## 说明

- 打包需要几分钟
- exe 文件约 50-100 MB
- 可以直接分享给别人使用
