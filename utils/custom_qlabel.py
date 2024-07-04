from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QPainter, QPen


class CustomLabel(QLabel):
    def __init__(self, parent=None):
        super(CustomLabel, self).__init__(parent)
        self.init_attributes()

    def init_attributes(self):
        self.points = []
        self.color = Qt.red
        self.line_width = 4
        self.radius = 6

    def paintEvent(self, event):
        painter = QPainter(self)
        if not painter.isActive():
            return

        painter.setRenderHint(QPainter.Antialiasing)
        pen = QPen(self.color, self.line_width)  # 设置颜色/宽度
        painter.setPen(pen)

        # 绘制所有点
        for point in self.points:
            # 绘制较大的点，以便更容易看到
            painter.drawEllipse(point, self.radius, self.radius)  # 绘制半径为10的圆来表示点
        # 绘制线段
        if len(self.points) > 1:
            for i in range(1, len(self.points)):
                painter.drawLine(self.points[i - 1], self.points[i])
