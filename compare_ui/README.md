# SubtitleCompare - VobSub/SRT 字幕比较校正工具

一个用于比较 VobSub（图像字幕）和 SRT（文本字幕）的图形界面工具，支持校正时间轴和文本内容。

## 功能特性

- **双栏对比界面**：左侧显示 VobSub 图像字幕，右侧显示可编辑的 SRT 文本字幕
- **智能配对**：自动检测时间偏移、缺失和多余的字幕条目
- **颜色标记**：
  - 绿色：正常匹配
  - 黄色：时间偏移
  - 红色：缺失条目
  - 灰色：多余条目
- **联动滚动**：点击一侧自动跳转到另一侧对应位置
- **编辑功能**：
  - 修改时间轴（开始/结束时间）
  - 编辑字幕文本
  - 添加/删除/复制条目
- **自动编码检测**：支持 UTF-8、GBK、ANSI 等编码自动识别

## 安装依赖

```bash
pip install -r requirements.txt
```

依赖：
- PyQt6 >= 6.4.0
- Pillow >= 9.0.0
- chardet >= 5.0.0

## 使用方法

### 启动应用

```bash
python compare_ui/main.py
```

### 基本操作

1. **导入 VobSub**：点击 "Import VobSub" 按钮选择 IDX 文件（会自动加载同目录的 SUB 文件）
2. **导入 SRT**：点击 "Import SRT" 按钮选择 SRT 文件
3. **自动比较**：导入后会自动执行比较，SRT 条目会根据匹配状态着色
4. **编辑字幕**：
   - 双击时间单元格可编辑时间
   - 直接点击文本单元格可编辑内容
   - 右键点击行可添加/删除/复制条目
5. **保存**：点击 "Save SRT" 保存修改后的字幕文件

### 快捷键

| 快捷键 | 功能 |
|--------|------|
| Ctrl+O | 打开 VobSub 文件 |
| Ctrl+I | 打开 SRT 文件 |
| Ctrl+S | 保存 SRT 文件 |
| Ctrl+Shift+S | 另存为 |
| Ctrl+Up | 上一个差异 |
| Ctrl+Down | 下一个差异 |
| Ctrl+N | 添加条目 |
| Ctrl+D | 删除条目 |
| Ctrl+R | 重新比较 |

## 项目结构

```
compare_ui/
├── main.py                 # 程序入口
├── requirements.txt        # 依赖列表
├── core/
│   ├── __init__.py
│   ├── models.py           # 数据模型（SubtitleEntry, VobSubEntry, SRTEntry）
│   ├── vobsub_parser.py    # IDX/SUB 解析器
│   └── srt_parser.py       # SRT 解析器
└── ui/
    ├── __init__.py
    ├── main_window.py      # 主窗口
    ├── vobsub_panel.py     # VobSub 左侧面板
    ├── srt_panel.py        # SRT 右侧面板
    └── styles.py           # QSS 样式表
```

## 技术说明

### VobSub 格式支持

- 解析 IDX 文件获取时间轴信息
- 支持从 SUB 文件提取图像数据
- 使用懒加载策略优化性能

### SRT 格式支持

- 自动检测文件编码（UTF-8/GBK/ANSI）
- 标准 SRT 格式解析和保存
- 支持多行字幕文本

### 配对算法

- 序列优先：第 N 行 VobSub 默认配对第 N 行 SRT
- 时间容错：检测时间差，标记偏移状态
- 断点续配：检测到缺失时自动调整后续配对

## 注意事项

1. 确保 IDX 和 SUB 文件在同一目录下且文件名相同
2. 大文件加载可能需要一些时间
3. 修改后请及时保存，关闭时会提示未保存的更改

## 与 xml_png_ocr_to_str.py 的关系

本工具是 `xml_png_ocr_to_str.py` 的配套工具：
- `xml_png_ocr_to_str.py`：将 VobSub (通过 BDSup2Sub 转换后的 XML+PNG) OCR 成 SRT
- `SubtitleCompare`：比较原始 VobSub 图像和生成的 SRT，进行人工校正
