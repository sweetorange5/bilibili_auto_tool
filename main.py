from ui.main_window import MainWindow
from utils.logger import global_logger

def main():
    """程序入口"""
    global_logger.info("启动全自动氛围神器")
    app = MainWindow()
    app.mainloop()

if __name__ == "__main__":
    main()