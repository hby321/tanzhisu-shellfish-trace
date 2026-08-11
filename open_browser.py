"""
自动打开浏览器的辅助脚本
在服务启动完成后自动打开 Flask 系统页面和小程序 H5 页面
"""
import time
import webbrowser
import sys

print("[辅助脚本] 等待 Flask 系统启动（约 5 秒）...")
time.sleep(5)

print("[辅助脚本] 正在打开 Flask 系统页面...")
webbrowser.open('http://127.0.0.1:5000')
print("[辅助脚本] Flask 系统页面已打开")

if len(sys.argv) > 1 and sys.argv[1] == 'with-mini':
    print("[辅助脚本] 等待小程序 H5 编译（约 15 秒）...")
    time.sleep(15)
    print("[辅助脚本] 正在打开小程序 H5 页面...")
    webbrowser.open('http://127.0.0.1:10086')
    print("[辅助脚本] 小程序 H5 页面已打开")

print("[辅助脚本] 完成！")
