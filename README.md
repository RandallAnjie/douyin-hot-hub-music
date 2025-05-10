# 抖音热门音乐榜

一个自动抓取抖音热门音乐榜单的工具，支持高潮片段提取和可视化展示。

**在线访问：[https://music.douyin.randallanjie.com/](https://music.douyin.randallanjie.com/)**

## 项目简介

本项目可以自动抓取抖音平台的热门音乐榜单数据，包括音乐基本信息、封面、音频文件和歌词。系统会自动分析并提取音乐的高潮片段，并提供美观的前端界面进行展示和播放。

## 主要功能

- 🎵 **热门音乐抓取**：自动抓取抖音热门音乐榜数据
- 🎧 **高潮片段识别**：智能识别并提取音乐高潮片段
- 📝 **歌词同步**：支持显示完整歌词和高潮片段歌词
- 🖼️ **美观界面**：响应式Web界面，支持PC和移动设备
- 🔄 **定时更新**：可配置定时任务自动更新榜单数据


## 安装步骤

### 环境要求

- Python 3.7+
- FFmpeg (用于音频处理)
- Git

### 安装过程

1. 克隆仓库

```bash
git clone https://github.com/yourusername/douyin-hot-hub-self.git
cd douyin-hot-hub-self
```

2. 安装依赖

```bash
pip install -r requirements.txt
```

3. 安装FFmpeg (如果尚未安装)

```bash
# MacOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get install ffmpeg

# Windows
# 请从官网下载并添加到环境变量
```

## 使用方法

### 基本使用

1. 运行数据抓取

```bash
python main.py
```

2. 启动Web服务器 (可选)

```bash
# 使用Python内置服务器
python -m http.server 8000

# 或使用其他Web服务器如Nginx/Apache
```

3. 访问前端界面

打开浏览器，访问 `http://localhost:8000`

### 配置定时更新

本项目使用GitHub Actions实现自动定时更新，无需手动配置本地的定时任务。


这样设置后，GitHub Actions会每小时自动运行一次数据抓取任务，无需本地计算机持续运行。您也可以在GitHub仓库的Actions页面手动触发更新。

## 项目结构

```
douyin-hot-hub-self/
├── main.py           # 主程序入口
├── douyin.py         # 抖音API接口实现
├── util.py           # 工具函数
├── template/         # 模板目录
├── archives/         # 历史数据存档
├── raw/              # 原始数据存储
├── assets/           # 音乐文件和元数据
│   ├── data.json     # 汇总的音乐数据
│   ├── music/        # 音频文件
│   ├── chorus/       # 高潮片段
│   ├── lyrics/       # 歌词文件
│   └── images/       # 封面图片
├── index.html        # 前端主页
└── static/           # 静态资源文件
    ├── js/           # JavaScript文件
    ├── css/          # 样式文件
    └── img/          # 图片资源
```

## 特性详解

### 高潮片段提取

系统能够智能分析音乐数据，提取高潮片段。当存在高潮段信息时，会自动截取对应时间的音频片段；当无法直接截取时，会自动判断原始音频是否已经是高潮片段。

### 歌词同步

支持LRC和JSON格式的歌词，并能根据播放内容(完整版或高潮片段)动态调整歌词显示，保持歌词与音乐的同步。对于高潮片段，会智能选择对应的歌词部分。

## 技术实现

- 后端: Python (网络请求、数据处理、文件操作)
- 前端: HTML, CSS, JavaScript (无框架，纯原生实现)
- 音频处理: FFmpeg
- 数据存储: JSON文件

## 贡献指南

欢迎提交Issue和Pull Request来改进这个项目!

## 许可证

[MIT License](LICENSE)
