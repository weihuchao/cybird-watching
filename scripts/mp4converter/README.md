# MP4转RGB565转换器

将MP4视频转换为LVGL 9.x兼容的RGB565格式图像帧序列的专业工具，专为CybirdWatching项目设计。

## 核心功能

- **双格式输出**: 支持RGB565(.bin)和PNG格式输出
- **自动抠图**: 智能去除绿底，生成透明背景图片
- **智能帧采样**: 支持按帧率或帧数采样，均匀分布算法
- **图像处理**: 智能缩放、尺寸调整、质量优化
- **水印去除**: 基础区域填充，去除指定区域水印
- **Bundle打包**: 将多帧打包为单个bundle.bin文件，减少文件数量
- **回文模式**: 自动生成正向+倒序的帧序列，用于循环播放效果
- **批量处理**: 多线程并行处理，进度跟踪
- **完全兼容**: 与LVGL 9.x和现有converter无缝集成

## 安装

```bash
uv sync
```

## 快速开始

### 基本用法

#### 1. 处理单个视频 - RGB565格式（默认）
```bash
# 基础转换 - 使用原始帧率
mp4-converter process video.mp4 output_frames/

# 指定帧率采样 - 每秒提取10帧
mp4-converter process video.mp4 output_frames/ --frame-rate 10

# 指定提取帧数 - 提取20帧
mp4-converter process video.mp4 output_frames/ --frame-count 20

# 缩放分辨率到120x120
mp4-converter process video.mp4 output_frames/ --resize 120x120

# 去除左上角水印
mp4-converter process video.mp4 output_frames/ --watermark-region "0,0,50,50"
```

#### 2. 输出PNG格式
```bash
# 输出PNG格式，不转换为RGB565
mp4-converter process video.mp4 output_frames/ --output-format png

# PNG格式 + 自动抠图（去除绿底）
mp4-converter process video.mp4 output_frames/ --output-format png --chroma-key

# PNG格式 + 缩放 + 抠图 + 去水印
mp4-converter process green_screen.mp4 output/ \
    --output-format png \
    --chroma-key \
    --resize 200x200 \
    --watermark-region "10,10,100,30"
```

#### 3. 批量处理
```bash
# 批量处理，输出RGB565格式
mp4-converter batch videos/ output/ --workers 8

# 批量处理 + 自动抠图
mp4-converter batch green_videos/ transparent_output/ \
    --output-format png \
    --chroma-key \
    --frame-rate 5 \
    --workers 4

# 批量处理 + Bundle打包（减少文件数量）
mp4-converter batch videos/ output/ \
    --output-format rgb565 \
    --pack-bundle \
    --frame-count 30 \
    --workers 4

# 批量处理 + 回文模式（创建循环播放效果）
mp4-converter batch videos/ output/ \
    --frame-count 40 \
    --palindrome \
    --workers 4

# 完整示例：抠图 + 缩放 + 回文模式
mp4-converter batch green_videos/ output/ \
    --output-format png \
    --chroma-key \
    --resize 120x120 \
    --frame-count 30 \
    --palindrome \
    --workers 4

# 混合处理，遇到错误继续
mp4-converter batch mixed_videos/ output/ \
    --frame-rate 10 \
    --resize 120x120 \
    --continue-on-error
```

#### 4. 查看视频信息
```bash
mp4-converter info video.mp4
```

## 功能详解

### 输出格式选择

```bash
# RGB565格式（默认）- 用于嵌入式显示
mp4-converter process video.mp4 rgb565_output/

# PNG格式 - 用于图片处理/预览
mp4-converter process video.mp4 png_output/ --output-format png
```

**输出文件命名:**
- 默认格式: `1.bin`, `2.bin`, `3.bin`...
- PNG格式: `1.png`, `2.png`, `3.png`...

### 自动抠图功能

智能检测并去除绿幕背景，生成透明背景图片。

```bash
# 自动检测绿幕并去除
mp4-converter process greenscreen.mp4 output/ --output-format png --chroma-key

# 批量处理绿幕视频
mp4-converter batch green_screen_videos/ transparent_frames/ \
    --output-format png \
    --chroma-key \
    --workers 4
```

**抠图特性:**
- 智能检测绿色幕布（HSV色彩空间）
- 多层阈值处理，精确边缘检测
- 边缘羽化处理，抗锯齿
- 色彩溢出抑制，减少绿边问题
- 透明背景输出（PNG格式）

**技术优势:**
- 使用HSV色彩空间进行更精确的绿色检测
- 多层阈值处理，避免误判
- 智能边缘清理，减少绿边残留
- 温和的色彩抑制，保持边缘完整性

### Bundle打包功能

将多个帧文件打包为单个`bundle.bin`文件，大幅减少文件数量，便于存储和传输。

```bash
# 打包为bundle.bin（单个文件）
mp4-converter batch videos/ output/ \
    --output-format rgb565 \
    --pack-bundle \
    --frame-count 30

# 自定义bundle尺寸（需要在代码中配置）
# 默认: 120x120
```

**适用场景:**
- 嵌入式设备存储空间有限
- 需要减少文件系统负担
- 批量传输大量帧数据

**工作原理:**
1. 提取并处理视频帧
2. 转换为RGB565格式的单独.bin文件
3. 使用converter的pack命令打包为bundle.bin
4. 自动清理临时的单独.bin文件

### 回文模式（Palindrome）

自动生成正向+倒序的帧序列，实现流畅的循环播放效果。

```bash
# 启用回文模式
mp4-converter batch videos/ output/ \
    --frame-count 40 \
    --palindrome

# 回文模式 + 抠图 + 缩放
mp4-converter batch green_videos/ output/ \
    --output-format png \
    --chroma-key \
    --resize 120x120 \
    --frame-count 30 \
    --palindrome
```

**工作原理:**
- 提取N帧（例如40帧：1-40）
- 自动创建倒序帧（39-1）
- 最终生成2N-1帧（79帧：1-40-1）
- 适用于循环播放动画，实现流畅的来回效果

**应用场景:**
- 循环播放动画（如呼吸灯效果）
- 往返运动效果
- 减少动画制作工作量

### 帧采样策略

```bash
# 按帧率采样 - 每秒提取5帧
mp4-converter process video.mp4 output/ --frame-rate 5

# 按帧数采样 - 均匀提取20帧
mp4-converter process video.mp4 output/ --frame-count 20

# 使用原始帧率（提取所有帧）
mp4-converter process video.mp4 output/
```

**采样算法:**
- 帧率采样：等间隔时间采样
- 帧数采样：均匀分布算法，确保覆盖整个视频
- 原始帧率：提取所有帧，适合短视频

### 图像处理

```bash
# 缩放到固定尺寸
mp4-converter process video.mp4 output/ --resize 120x120

# 限制最大宽度
mp4-converter process video.mp4 output/ --resize w120

# 限制最大高度
mp4-converter process video.mp4 output/ --resize h120

# 限制最大尺寸（保持宽高比）
mp4-converter process video.mp4 output/ --max-width 200 --max-height 200
```

### 水印去除

```bash
# 去除指定区域的水印（x,y,width,height）
mp4-converter process video.mp4 output/ --watermark-region "10,10,100,50"

# 结合其他功能
mp4-converter process video.mp4 output/ \
    --watermark-region "0,0,50,50" \
    --resize 120x120 \
    --frame-rate 10
```

### 并行处理

```bash
# 使用8个并行线程
mp4-converter batch videos/ output/ --workers 8

# 默认使用4个线程
mp4-converter batch videos/ output/
```

**性能优化:**
- 多线程并行处理，充分利用CPU
- 智能任务调度
- 实时进度显示
- 内存优化，避免OOM

### RGB565格式选项

```bash
# 二进制格式（默认）
mp4-converter process video.mp4 output/ --rgb565-format binary

# C数组格式（用于嵌入代码）
mp4-converter process video.mp4 output/ --rgb565-format c_array

# C数组格式 + 自定义数组名
mp4-converter process video.mp4 output/ \
    --rgb565-format c_array \
    --array-name my_animation
```

## 完整示例

### 示例1: 制作嵌入式动画（Bundle打包）
```bash
# 提取30帧，缩放到120x120，打包为bundle.bin
mp4-converter batch animations/ output/ \
    --output-format rgb565 \
    --frame-count 30 \
    --resize 120x120 \
    --pack-bundle \
    --workers 4
```

### 示例2: 处理绿幕素材（PNG + 抠图）
```bash
# 批量处理绿幕视频，输出透明背景PNG
mp4-converter batch green_videos/ transparent_output/ \
    --output-format png \
    --chroma-key \
    --frame-rate 10 \
    --resize 200x200 \
    --workers 6
```

### 示例3: 创建循环动画（回文模式）
```bash
# 提取40帧并创建回文效果（共79帧）
mp4-converter batch loop_videos/ output/ \
    --frame-count 40 \
    --palindrome \
    --resize 120x120 \
    --workers 4
```

### 示例4: 完整流程（抠图 + 去水印 + 回文）
```bash
# 绿幕视频去背景、去水印、创建循环效果
mp4-converter process greenscreen.mp4 final_output/ \
    --output-format png \
    --chroma-key \
    --watermark-region "10,10,100,30" \
    --resize 120x120 \
    --frame-count 30 \
    --palindrome
```

### 示例5: 生产环境批量处理
```bash
# 批量处理，错误继续，最大并行度
mp4-converter batch production_videos/ output/ \
    --output-format rgb565 \
    --frame-rate 8 \
    --resize 120x120 \
    --pack-bundle \
    --workers 8 \
    --continue-on-error
```