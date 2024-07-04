---
typora-root-url: data
---

# ROI-Drawing-APP
Based on PyQT5; Drawing a ROI on frame. 一款基于PyQT5开发的ROI绘制小程序。

![](/draw_roi.gif)

## 如何使用：

### 直接运行，不需配置环境：

从release下载：https://github.com/AICVHub/ROI-Drawing-APP/releases

### 源码运行，需要配置环境：

- **Python环境**：
  - PyQt5                     5.15.10
  - PyQt5-Qt5                 5.15.2
  - opencv-python-headless    4.10.0.84

## 软件使用流程：

1. 加载配置项：通过菜单栏选择“文件”->“打开/更改配置”。 
2. 选择源：在配置中选择所需的图片或视频流。 
3. 绘制ROI：使用鼠标进行操作： 
   - 继续单击左键绘制。 
   - 单击鼠标右键闭合轮廓。 
   - 单击鼠标中键清空当前轮廓。 
4. 控制绘制行为：利用工具栏上的按钮来开始、结束或清空绘制。 