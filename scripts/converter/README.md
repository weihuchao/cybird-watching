# 图片转RGB565转换器

这是一个基于Python开发的图片转RGB565格式转换工具，支持将PNG、JPG、JPEG等格式的图片转换为RGB565格式，适用于嵌入式系统显示应用。

## 功能特点

- ✅ 支持PNG、JPG、JPEG格式图片转换
- ✅ 批量目录处理功能
- ✅ 单文件转换功能
- ✅ 输出LVGL 9.x兼容的二进制RGB565格式
- ✅ 输出C数组格式（方便嵌入代码）
- ✅ 帧序列打包为bundle.bin格式
- ✅ 图片尺寸缩放功能
- ✅ 多线程并行处理
- ✅ 进度显示和错误处理
- ✅ 使用uv管理依赖

## 安装

### 1. 安装uv（如果未安装）

```bash
# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Linux/macOS
curl -LsSf https://astral.sh/uv/install.sh | sh

# Python
pip install -U uv
```

### 2. 安装项目依赖

```bash
cd scripts/converter
uv install
```

## 使用方法

### 查看帮助信息

```bash
uv run converter --help
```

### 单文件转换

#### 转换为二进制格式

```bash
# 基本用法
uv run converter single input.png output.rgb565

# 指定最大尺寸
uv run converter single input.png output.rgb565 --max-width 64 --max-height 64
```

#### 转换为C数组格式

```bash
# 基本用法
uv run converter single input.png output.c --format c_array

# 指定数组名称
uv run converter single input.png output.c --format c_array --array-name my_image

# 指定最大尺寸和数组名称
uv run converter single input.png output.c --format c_array --array-name logo --max-width 128 --max-height 128
```

### 批量转换

#### 批量转换为二进制格式

```bash
# 基本用法
uv run converter convert input_directory/ output_directory/

# 指定最大尺寸和线程数
uv run converter convert input_directory/ output_directory/ --max-width 64 --max-height 64 --workers 8
```

#### 批量转换为C数组格式

```bash
# 批量转换为C数组
uv run converter convert input_directory/ output_directory/ --format c_array

# 指定线程数
uv run converter convert input_directory/ output_directory/ --format c_array --workers 4
```

### 帧序列打包

将多个帧文件（1.bin, 2.bin, 3.bin...）打包为bundle.bin格式：

```bash
# 基本用法（默认120x120）
uv run converter pack frames_directory/ output/bundle.bin

# 指定帧尺寸
uv run converter pack frames_directory/ output/bundle.bin --width 128 --height 128
```

## 输出格式说明

### LVGL 9.x二进制格式

生成的.bin文件兼容LVGL 9.x图像格式：

**文件头部（32字节）**：
- `header_cf` (4字节)：包含magic number (0x37) 和color format (0x12 for RGB565)
- `flags` (4字节)：图像标志
- `width, height` (4字节)：图片宽度和高度
- `stride` (4字节)：行跨度（自动计算）
- `reserved` (8字节)：保留字段
- `data_size` (4字节)：像素数据大小

**像素数据**：
- RGB565格式像素数据（每像素2字节）
- 总文件大小 = 32字节 + (宽度 × 高度 × 2字节)

### C数组格式

生成的C文件包含：

1. 图片宽度常量：`const uint16_t [array_name]_width`
2. 图片高度常量：`const uint16_t [array_name]_height`
3. RGB565像素数据数组：`const uint16_t [array_name]_data[]`

使用示例：
```c
#include "your_image.c"

// 在代码中使用
extern const uint16_t your_image_data[];
extern const uint16_t your_image_width;
extern const uint16_t your_image_height;
```

### Bundle格式

用于动画帧序列的打包格式：

**Bundle头部（64字节）**：
- `magic` (4字节)：0x42495244 ("BIRD")
- `version` (2字节)：版本号
- `frame_count` (2字节)：帧数量
- `frame_width, frame_height` (4字节)：帧尺寸
- `frame_size` (4字节)：单帧大小
- `index_offset` (4字节)：索引表偏移
- `data_offset` (4字节)：数据区偏移
- `total_size` (4字节)：总文件大小
- `color_format` (1字节)：颜色格式（0x12 for RGB565）
- `reserved` (35字节)：保留

**帧索引表（N×12字节）**：
- 每帧包含：`offset` (4字节), `size` (4字节), `checksum` (4字节)

**帧数据区**：
- 所有帧的LVGL 9.x格式数据依次存储

## RGB565格式说明

RGB565是一种16位颜色格式：

- 红色：5位（0-31）
- 绿色：6位（0-63）
- 蓝色：5位（0-31）

格式布局：`RRRRRGGGGGGBBBBB`

## 支持的输入格式

- PNG（.png, .PNG）
- JPEG（.jpg, .JPG, .jpeg, .JPEG）

## 命令行参数

### 全局选项

- `--version`: 显示版本信息
- `--help`: 显示帮助信息

### 单文件转换选项 (`single`)

- `--max-width`: 最大宽度（像素）
- `--max-height`: 最大高度（像素）
- `--format`: 输出格式（binary 或 c_array）
- `--array-name`: C数组名称（仅用于c_array格式）

### 批量转换选项 (`convert`)

- `--max-width`: 最大宽度（像素）
- `--max-height`: 最大高度（像素）
- `--format`: 输出格式（binary 或 c_array）
- `--workers`: 并行处理线程数（默认4）

### 帧打包选项 (`pack`)

- `--width`: 帧宽度（像素，默认120）
- `--height`: 帧高度（像素，默认120）

## 示例

### 创建测试图片并转换

```bash
# 1. 创建测试图片（如果有create_test_image.py）
python create_test_image.py

# 2. 单文件转换为LVGL 9.x格式
uv run converter single test_input/red_gradient.png test_output/red_gradient.bin

# 3. 转换为C数组
uv run converter single test_input/green_gradient.jpg test_output/green_gradient.c --format c_array --array-name test_image

# 4. 批量转换
uv run converter convert test_input/ test_output_batch/

# 5. 批量转换为C数组
uv run converter convert test_input/ test_output_c/ --format c_array

# 6. 打包帧序列
uv run converter pack frames/ output/animation.bin --width 120 --height 120
```

## 技术实现

- **语言**: Python 3.12+
- **图像处理**: Pillow (PIL)
- **数值计算**: NumPy
- **并行处理**: concurrent.futures
- **命令行界面**: Click
- **进度显示**: tqdm
- **依赖管理**: uv
- **校验和**: zlib (CRC32)

## 项目结构

```
converter/
├── src/
│   └── converter/
│       ├── __init__.py          # 主程序入口和CLI（包含convert/single/pack命令）
│       ├── rgb565.py           # RGB565转换核心算法和bundle打包
│       └── batch_processor.py  # 批量处理功能
├── test_input/                 # 测试输入图片（可选）
├── test_output/                # 测试输出文件（可选）
├── .gitignore                  # Git忽略配置
├── .python-version             # Python版本
├── pyproject.toml             # 项目配置和依赖
├── uv.lock                    # uv依赖锁定文件
└── README.md                  # 使用说明
```

## 错误处理

- 不支持的图片格式会自动跳过
- 转换失败的文件会显示错误信息但不影响其他文件处理
- 输出目录自动创建
- 详细的错误信息和进度显示
- Bundle打包时自动验证帧文件格式和完整性
- CRC32校验确保数据完整性

## 性能特点

- 多线程并行处理提高转换速度
- 内存优化的逐像素转换算法
- 支持大尺寸图片的等比缩放
- 自动创建输出目录结构
- Bundle打包支持大量帧文件

## 应用场景

1. **单帧图像**：Logo、图标、静态图片显示
2. **动画序列**：使用bundle格式打包帧序列，适用于LVGL动画播放
3. **嵌入式开发**：生成C数组直接嵌入固件代码
4. **资源优化**：批量转换和压缩图片资源

## 许可证

本项目遵循MIT许可证。