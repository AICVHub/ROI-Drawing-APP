import sys
import cv2
import json
import time
import threading

import numpy as np
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QLabel, QStyle, \
    QFileDialog, QAction, QComboBox, QToolBar, QInputDialog

from utils.source_pull import SourcePuller
from utils.custom_qlabel import CustomLabel


class DrawROI(QMainWindow):
    def __init__(self, fps=10):
        super().__init__()
        self.scaled_pixmap = None
        self.config = None
        self.points_image = []  # 存储鼠标点击的坐标点(image坐标系)
        self.close_drawing_flag = False
        self.source_puller = None
        self.clipboard = QApplication.clipboard()  # 剪贴板对象作为类属性

        self.fps = fps
        self.setWindowTitle("Draw ROI")
        self.setGeometry(300, 100, 1280, 720 + 30)
        self.setWindowIcon(self.style().standardIcon(QStyle.SP_FileDialogStart))

        # 创建菜单栏
        menubar = self.menuBar()
        fileMenu = menubar.addMenu('文件')
        aboutMenu = menubar.addMenu('关于')

        # 添加"打开/更改配置"菜单项
        openConfigAction = QAction('打开/更改配置', self)
        openConfigAction.triggered.connect(self.open_config)
        fileMenu.addAction(openConfigAction)
        # 添加“手动输入源”菜单项
        manualInputAction = QAction('手动输入源', self)
        manualInputAction.triggered.connect(self.manual_input_source)
        fileMenu.addAction(manualInputAction)
        # 添加退出菜单项
        exitAction = QAction('退出', self)
        exitAction.triggered.connect(self.simple_close)
        fileMenu.addAction(exitAction)
        # 添加"关于"的菜单项
        aboutAction = QAction('关于', self)
        aboutAction.triggered.connect(self.about_info)
        aboutMenu.addAction(aboutAction)
        # 添加"帮助"
        helpAction = QAction('帮助', self)
        helpAction.triggered.connect(self.help_info)
        aboutMenu.addAction(helpAction)
        # 创建下拉框
        self.comboBox = QComboBox(self)
        self.comboBox.setGeometry(self.width() - 400, 0, 400, self.menuBar().height() - 2)  # xywh
        self.prompt_text = "请选择一个源（视频或者图片）"
        self.comboBox.addItem(self.prompt_text)
        self.comboBox.setEditText(self.prompt_text)  # 设置为当前显示文本
        self.comboBox.activated.connect(self.on_combobox_activated)
        # 创建用于展示图片的 QLabel
        self.imageLabel = QLabel(self)
        self.imageLabel.setGeometry(0, self.menuBar().height(), self.width(), self.height() - self.menuBar().height())
        self.imageLabel.setStyleSheet("background-color: #aaaaaa;")
        self.imageLabel.setAlignment(Qt.AlignCenter)  # 居中显示图片
        # 创建一个自定义的透明 QLabel，用于绘制点
        self.transparentLabel = CustomLabel(self)
        self.transparentLabel.setGeometry(0, self.menuBar().height(), self.width(),
                                          self.height() - self.menuBar().height())
        self.transparentLabel.setStyleSheet("background-color: rgba(255, 179, 169, 0);")  # 透明背景
        self.transparentLabel.mousePressEvent = self.mouse_pressed  # 绑定鼠标点击事件

        # 创建一个线程来加载和展示图片
        threading.Thread(target=self.load_and_show_image, daemon=True).start()

        # 创建工具栏
        self.create_tool_bar()

    def init_source_puller(self, source_path):
        self.source_puller = SourcePuller(source_path)
        self.points_image = []  # 存储鼠标点击的坐标点(image坐标系)
        self.transparentLabel.points = []  # 清空点

    def open_config(self):
        options = QFileDialog.Options()
        config_path, _ = QFileDialog.getOpenFileName(
            self, "Open Config", ".a", "Config Files (*.json)", options=options
        )
        if config_path:
            with open(config_path, 'r') as f:
                self.config = json.load(f)
                print(self.config)
                # 清空下拉框
                self.comboBox.clear()
                self.comboBox.addItem(self.prompt_text)
                # 添加配置项到下拉框
                self.add_config_items_to_combobox(self.config)

    def manual_input_source(self):
        # 弹出输入对话框让用户输入图片或视频的地址
        # 同时让用户选择是输入图片还是视频
        item, ok = QInputDialog.getItem(self, '手动输入源', '请选择源类型:',
                                        ['图片', '视频'], 0, False)
        if ok and item:
            source_type = "图片" if item == "图片" else "视频"
            text, text_ok = QInputDialog.getText(self, f'输入{source_type}地址', f'请输入{source_type}文件的地址:')
            self.comboBox.clear()
            if text_ok and text:
                # 根据用户选择的类型处理输入的地址
                if source_type == "图片":
                    self.comboBox.addItem(f"images: {text}")
                elif source_type == "视频":
                    self.comboBox.addItem(f"videos: {text}")
                self.start_source_puller(self.comboBox.currentText())

    def simple_close(self):
        # 直接关闭窗口，不显示任何消息框
        self.close()  # 该方法会触发closeEvent事件，与直接点击X效果一致

    def add_config_items_to_combobox(self, config):
        # 根据config字典中的videos和images键添加项到下拉框
        if 'videos' in config:
            for video_path in config['videos']:
                self.comboBox.addItem(f"videos: {video_path}")
        if 'images' in config:
            for image_path in config['images']:
                self.comboBox.addItem(f"images: {image_path}")

    def on_combobox_activated(self):
        # 当下拉框选项被激活时执行的槽函数
        if self.comboBox.currentText() == self.prompt_text:
            # 如果用户选择了提示语，我们不进行任何操作，或者可以提示用户选择一个有效项
            pass  # 这里不执行任何操作
        else:
            # 用户选择了一个有效项，从下拉框中移除提示语
            self.comboBox.removeItem(self.comboBox.findText(self.prompt_text))
            # 处理选中的项
            item_text = self.comboBox.currentText()
            print(f"选中的项是: {item_text}")
            self.start_source_puller(item_text)
            self.clear_roi()

    def start_source_puller(self, source_path):
        # 根据选中的项创建一个SourcePuller对象: 将创建过程放到一个子线程，以避免阻塞
        thread_source = threading.Thread(target=self.init_source_puller, args=(source_path,), daemon=True)
        thread_source.start()

    def create_tool_bar(self):
        # 创建一个工具栏
        toolbar = QToolBar("底部工具栏")
        self.addToolBar(Qt.BottomToolBarArea, toolbar)  # 添加到顶部

        # 创建一个只显示文本的 QAction 作为标题
        title_action = QAction("轮廓绘制工具栏", self)
        title_action.setEnabled(False)  # 设置不可点击
        title_action.setCheckable(False)  # 设置不可选中
        toolbar.addAction(title_action)

        # 将 QAction 转换为 QWidget 并添加到工具栏
        title_widget = toolbar.widgetForAction(title_action)
        title_widget.setStyleSheet("color: gray; ")  # 设置标题颜色
        # 设置工具栏样式
        toolbar.setStyleSheet("QToolBar { border: 10px; }")  # 设置边框
        toolbar.setStyleSheet("""
        QToolBar {
            border: 1px solid #ffffff; /* 白色边框 */
            border-radius: 4px;
            background-color: rgba(255, 255, 255, 0.5); /* 半透明白色背景 */
        }
        """)  # 设置背景
        toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)  # 图标和文本并排显示

        # 创建一些按钮并添加到工具栏中
        end_action = QAction("闭合", self)
        end_action.triggered.connect(self.close_drawing)
        toolbar.addAction(end_action)
        clear_action = QAction("清空", self)
        clear_action.triggered.connect(self.clear_roi)
        toolbar.addAction(clear_action)
        save_action = QAction("保存", self)
        save_action.triggered.connect(self.save_roi)
        toolbar.addAction(save_action)

    def close_drawing(self):
        # 结束绘制的逻辑
        if len(self.transparentLabel.points) > 1 and not self.close_drawing_flag:
            if self.transparentLabel.points[0] != self.transparentLabel.points[-1]:
                self.transparentLabel.points.append(self.transparentLabel.points[0])  # 闭合区域
                self.transparentLabel.color = Qt.green  # 更改颜色
                self.transparentLabel.update()  # 重新绘制 CustomLabel
                self.close_drawing_flag = True

    def clear_roi(self):
        # 清空绘制的逻辑
        if len(self.transparentLabel.points) > 0:
            self.points_image = []  # 清空图像坐标系中的点
            self.transparentLabel.init_attributes()  # 重置属性
            self.transparentLabel.update()  # 重新绘制 CustomLabel
            self.close_drawing_flag = False  # 重置结束标识

    def save_roi(self):
        # 保存ROI：将点的坐标保存为json格式的字符串
        if len(self.points_image) > 0:
            self.close_drawing()  # 闭合轮廓并结束绘制
            roi_data = json.dumps(self.points_image, ensure_ascii=False)
            # 创建一个可交互的QMessageBox
            message_box = QMessageBox()
            message_box.setWindowTitle("ROI数据已生成")
            message_box.setText("点击【复制】按钮可保存到您的剪贴板！")
            message_box.setInformativeText(roi_data)
            message_box.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard)
            message_box.setStandardButtons(QMessageBox.NoButton)  # 移除所有标准按钮

            # 添加自定义的“复制”按钮
            copy_button = message_box.addButton("复制", QMessageBox.AcceptRole)
            message_box.buttonClicked.connect(lambda _: self.copy_to_clipboard(message_box))  # 使用lambda表达式传递message_box

            # 显示消息框
            message_box.exec_()

            # # 如果需要复制到剪贴板，可以使用以下代码：
            # clipboard = QApplication.clipboard()
            # clipboard.setText(roi_data)

            self.clear_roi()  # 清空绘制的轮廓点

    def copy_to_clipboard(self, message_box):
        # 复制文本到剪贴板并关闭消息框
        self.clipboard.setText(message_box.informativeText())
        message_box.accept()  # 关闭消息框

    def load_and_show_image(self):
        # 循环读取图片并展示
        while True:
            time.sleep(1 / self.fps)
            try:
                if self.source_puller is None:
                    continue
                ret, image = self.source_puller.pull_frame()
                if not ret:
                    continue
                # 将 cv2 图片转换为 RGB 格式
                image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

                # 将图片转换为 QImage 对象
                h, w, ch = image.shape
                bytes_per_line = ch * w
                qt_image = QImage(image.data, w, h, bytes_per_line, QImage.Format_RGB888)

                # 使用 QPixmap 包装 QImage 对象
                pixmap = QPixmap.fromImage(qt_image)
                if pixmap.isNull():
                    continue

                # 调整 QPixmap 大小以适应 QLabel
                self.scaled_pixmap = pixmap.scaled(self.imageLabel.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                # print(scaled_pixmap.size(), self.imageLabel.size())
                # 获取实际展示的图片在 self.imageLabel.size() 中的位置，self.imageLabel是居中展示的

                # 使用 QLabel 的 setPixmap 方法展示图片
                self.imageLabel.setPixmap(self.scaled_pixmap)
            except Exception as e:
                time.sleep(1)

    def mouse_pressed(self, event):
        if event.button() == Qt.LeftButton:
            if self.close_drawing_flag:
                return
            # 获取鼠标点击的坐标（self.imageLabel坐标系）
            QLabel_x = event.pos().x()
            QLabel_y = event.pos().y()

            print(f"QLabel坐标: x={QLabel_x}, y={QLabel_y}")
            if self.scaled_pixmap is not None:
                # 计算图像在 QLabel 中的居中偏移量
                xOffset = (self.transparentLabel.width() - self.scaled_pixmap.width()) / 2
                yOffset = (self.transparentLabel.height() - self.scaled_pixmap.height()) / 2
                # 将 QLabel 坐标系下的坐标转换为图像坐标系
                image_x = np.clip(QLabel_x - xOffset, 0, self.scaled_pixmap.width())
                image_y = np.clip(QLabel_y - yOffset, 0, self.scaled_pixmap.height())
                draw_x = np.clip(QLabel_x, xOffset, self.transparentLabel.width() - xOffset)
                draw_y = np.clip(QLabel_y, yOffset, self.transparentLabel.height() - yOffset)

                print(f"image坐标: x={image_x}, y={image_y}")
                self.transparentLabel.points.append(QPoint(int(draw_x), int(draw_y)))
                self.transparentLabel.update()  # 更新 CustomLabel 以显示新点
                self.points_image.append((
                    round(image_x / self.scaled_pixmap.width(), 4),
                    round(image_y / self.scaled_pixmap.height(), 4)
                ))  # 添加点到列表，并进行归一化
        elif event.button() == Qt.RightButton:
            # 如果鼠标右键被按下，则结束绘制
            self.close_drawing()
        elif event.button() == Qt.MiddleButton:
            self.clear_roi()

    def about_info(self):
        QMessageBox.information(self, 'About',
                                'ROI绘制小程序\n作者：@AICVHub\n主页：https://liwensong.blog.csdn.net\n版本：V1.0.0')

    def help_info(self):
        message = """
        <html><head><meta charset='utf-8'></head><body>
        <h3>使用帮助</h3>
        <p>欢迎使用本应用程序，以下是基本的使用步骤：</p>
        <ul>
            <li><strong>加载配置项：</strong>通过菜单栏选择“文件”->“打开/更改配置”。</li>
            <li><strong>选择源：</strong>在配置中选择所需的图片或视频流。</li>
            <li><strong>绘制ROI：</strong>使用鼠标进行操作：
                <ul style='list-style-type: disc;'>
                    <li>继续单击左键绘制。</li>
                    <li>单击鼠标右键闭合轮廓。</li>
                    <li>单击鼠标中键清空当前轮廓。</li>
                </ul>
            </li>
            <li><strong>控制绘制行为：</strong>利用工具栏上的按钮来开始、结束或清空绘制。</li>
        </ul>
        <p>如果需要更多帮助，请参阅用户手册或联系技术支持。</p>
        </body></html>
        """
        QMessageBox.information(self, '帮助', message)

    def resizeEvent(self, event):
        # 每次窗口大小变化时，更新相关组件的大小/位置
        # self.label.setGeometry(0, 0, self.width(), self.height())
        self.comboBox.setGeometry(self.width() - 400, 0, 400, self.menuBar().height() - 2)  # xywh
        self.imageLabel.setGeometry(0, self.menuBar().height(), self.width(), self.height() - self.menuBar().height())
        self.transparentLabel.setGeometry(0, self.menuBar().height(), self.width(),
                                          self.height() - self.menuBar().height())

        super().resizeEvent(event)  # 调用父类的resizeEvent

    def closeEvent(self, event):
        # 当用户尝试关闭窗口时，显示退出确认消息框
        reply = QMessageBox.question(self, '警告', '您确定要退出吗？',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            event.accept()  # 用户点击"Yes"，接受关闭事件
        else:
            event.ignore()  # 用户点击"No"，忽略关闭事件，窗口不关闭


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DrawROI()
    window.show()
    sys.exit(app.exec_())
