# 图片转RGB565转换器

这是一个基于Python开发的图片转RGB565格式转换工具，支持将PNG、JPG、JPEG等格式的图片转换为RGB565格式，适用于嵌入式系统显示应用。

## 功能特点

- ✅ 支持PNG、JPG、JPEG格式图片转换
- ✅ 批量目录处理功能
- ✅ 单文件转换功能
- ✅ 输出二进制RGB565格式
- ✅ 输出C数组格式（方便嵌入代码）
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

## 输出格式说明

### 二进制格式

- 文件开头存储图片尺寸信息（2字节宽度 + 2字节高度）
- 后续存储RGB565格式的像素数据（每个像素2字节）
- 总文件大小 = 4字节 + (宽度 × 高度 × 2字节)

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

## 示例

### 创建测试图片并转换

```bash
# 1. 创建测试图片
python create_test_image.py

# 2. 单文件转换测试
uv run converter single test_input/red_gradient.png test_output/red_gradient.rgb565

# 3. 转换为C数组
uv run converter single test_input/green_gradient.jpg test_output/green_gradient.c --format c_array --array-name test_image

# 4. 批量转换
uv run converter convert test_input/ test_output_batch/

# 5. 批量转换为C数组
uv run converter convert test_input/ test_output_c/ --format c_array
```

## 技术实现

- **语言**: Python 3.12+
- **图像处理**: Pillow (PIL)
- **并行处理**: concurrent.futures
- **命令行界面**: Click
- **进度显示**: tqdm
- **依赖管理**: uv

## 项目结构

```
converter/
├── src/
│   └── converter/
│       ├── __init__.py          # 主程序入口和CLI
│       ├── rgb565.py           # RGB565转换核心算法
│       └── batch_processor.py  # 批量处理功能
├── test_input/                 # 测试输入图片
├── test_output/                # 测试输出文件
├── create_test_image.py       # 测试图片生成脚本
├── pyproject.toml             # 项目配置
└── README.md                  # 使用说明
```

## 错误处理

- 不支持的图片格式会自动跳过
- 转换失败的文件会显示错误信息但不影响其他文件处理
- 输出目录自动创建
- 详细的错误信息和进度显示

## 性能特点

- 多线程并行处理提高转换速度
- 内存优化的逐像素转换算法
- 支持大尺寸图片的等比缩放
- 自动创建输出目录结构

## 许可证

本项目遵循MIT许可证。