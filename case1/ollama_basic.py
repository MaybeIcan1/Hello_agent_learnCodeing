import sys
sys.stdout.reconfigure(encoding='utf-8')  # 关键代码，修改输出通道编码格式
print(f"默认编码: {sys.getdefaultencoding()}")  # 显示python的默认编码格式
print(f"标准输出编码: {sys.stdout.encoding}")  # 显示输出通道的编码格式
