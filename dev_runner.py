# dev_runner.py
import sys
import time
import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# --- 配置 ---
# 要执行的主程序文件
MAIN_APP_SCRIPT = 'main.py'
# 要监视的文件夹路径 ('.' 表示当前文件夹)
WATCH_PATH = '.'

class AppReloader(FileSystemEventHandler):
    """文件变动事件处理器"""
    def __init__(self):
        super().__init__()
        self.process = None
        self.start_app()

    def start_app(self):
        """启动或重启应用程序"""
        if self.process:
            print("-------------------------------------------------")
            print("检测到代码变动，正在重启应用...")
            self.process.terminate() # 终止旧进程
            self.process.wait()      # 等待进程完全终止
        
        # 使用 subprocess.Popen 启动新进程
        # sys.executable 指的是当前正在使用的 python 解释器
        self.process = subprocess.Popen([sys.executable, MAIN_APP_SCRIPT])
        print(f"应用已启动 (PID: {self.process.pid})...")
        print("-------------------------------------------------")

    def on_modified(self, event):
        """当文件被修改时调用"""
        # 我们只关心 .py 文件的变动
        if event.src_path.endswith('.py'):
            self.start_app()

if __name__ == "__main__":
    print(">>> 启动开发模式：代码热重载已激活 <<<")
    
    event_handler = AppReloader()
    observer = Observer()
    observer.schedule(event_handler, WATCH_PATH, recursive=True)
    observer.start()
    
    try:
        # 保持主脚本运行，以便持续监视
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        # 当用户按下 Ctrl+C 时，停止监视并终止子进程
        observer.stop()
        if event_handler.process:
            event_handler.process.terminate()
            event_handler.process.wait()
        print("\n>>> 开发模式已退出 <<<")

    observer.join()