# main.py
import sys
from PyQt5.QtWidgets import QApplication, QDialog

# --- 将其他导入移到 main 函数内部，以遵循最佳实践 ---

def main():
    """程序主入口，包含一个循环来处理登出和重新登录"""
    app = QApplication(sys.argv)
    
    # --- 核心修改点 1: 更换为浅色主题 ---
    from qt_material import apply_stylesheet
    # 'light_blue.xml' 是一个非常清爽专业的浅色主题
    # 您也可以尝试: 'light_cyan.xml', 'light_teal.xml', 'light_lightgreen.xml'
    apply_stylesheet(app, theme='light_blue.xml')
    
    # --- 导入我们自己的模块 ---
    import user_manager
    from login_window import LoginDialog
    from main_window import MainWindow

    # 为 QSettings 设置应用信息，这对于持久化至关重要
    app.setOrganizationName("YourCompany")
    app.setApplicationName("MicroSprinklingSystem")

    # --- 核心修改点 2: 实现登录/登出循环 ---
    while True:
        # 尝试获取已登录的用户
        username = user_manager.get_logged_in_user()
        
        # 如果没有自动登录的用户，则显示登录对话框
        if not username:
            login_dialog = LoginDialog()
            login_dialog.setFixedSize(900, 550)
            
            # 居中代码
            screen_center = app.primaryScreen().availableGeometry().center()
            login_geometry = login_dialog.frameGeometry()
            login_geometry.moveCenter(screen_center)
            login_dialog.move(login_geometry.topLeft())

            if login_dialog.exec_() == QDialog.Accepted:
                username = login_dialog.username
                user_manager.save_logged_in_user(username)
            else:
                # 如果用户关闭了登录窗口，则退出循环
                sys.exit(0) # 正常退出
        
        # 创建并显示主窗口
        main_win = MainWindow(username)
        
        # 主窗口自适应尺寸和居中代码
        screen_geometry = app.primaryScreen().geometry()
        width = int(screen_geometry.width() * 0.8)
        height = int(screen_geometry.height() * 0.8)
        main_win.resize(width, height)
        
        window_geometry = main_win.frameGeometry()
        center_point = app.primaryScreen().availableGeometry().center()
        window_geometry.moveCenter(center_point)
        main_win.move(window_geometry.topLeft())
        
        main_win.show()
        
        app.exec_() # 等待主窗口关闭

        # 检查主窗口关闭的原因
        if hasattr(main_win, 'logout_triggered') and main_win.logout_triggered:
            # 如果是登出触发的，则继续循环，下一次循环会显示登录框
            continue
        else:
            # 如果是正常关闭（点X），则退出循环
            break
            
if __name__ == "__main__":
    main()