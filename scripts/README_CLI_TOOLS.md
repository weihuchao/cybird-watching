# CybirdWatching CLI 快速启动工具

本目录包含了用于快速启动CybirdWatching CLI的批处理文件，让您无需手动输入长命令。

## 📁 文件说明

### 1. `cybird_cli.bat` - 快速启动交互模式
**最简单的启动方式，使用默认配置**

```bash
# 双击运行或命令行执行
cybird_cli.bat
```

- 使用默认端口：COM3
- 使用默认波特率：115200
- 直接进入交互模式

### 2. `cybird_cli_with_args.bat` - 带参数启动
**支持自定义端口和波特率**

```bash
# 使用默认配置
cybird_cli_with_args.bat

# 指定端口
cybird_cli_with_args.bat COM4

# 指定端口和波特率
cybird_cli_with_args.bat COM4 9600

# 显示帮助
cybird_cli_with_args.bat help
```

### 3. `cybird_send.bat` - 单命令发送
**快速发送单个命令到设备**

```bash
# 发送log命令（使用默认配置）
cybird_send.bat "log"

# 发送status命令到COM4
cybird_send.bat "status" COM4

# 发送命令并指定端口和波特率
cybird_send.bat "log lines 50" COM4 9600

# 显示用法说明
cybird_send.bat
```

### 4. `cybird_bird.bat` - 观鸟专用工具
**专门用于观鸟功能的快捷工具**

```bash
# 触发小鸟动画
cybird_bird.bat trigger

# 查看观鸟统计
cybird_bird.bat stats

# 显示可用小鸟列表
cybird_bird.bat list

# 重置统计数据
cybird_bird.bat reset

# 在指定端口操作
cybird_bird.bat trigger COM4

# 显示帮助
cybird_bird.bat help
```

## 🚀 快速开始

### 首次使用
1. 确保已安装 [uv](https://docs.astral.sh/uv/)
2. 将ESP32设备连接到电脑
3. 双击 `cybird_cli.bat` 启动交互模式

### 常用操作

```bash
# 启动交互模式
cybird_cli.bat

# 快速查看设备状态
cybird_send.bat "status"

# 查看最新日志
cybird_send.bat "log"

# 查看最后50行日志
cybird_send.bat "log lines 50"

# 清空日志
cybird_send.bat "log clear"

# 🐦 观鸟功能 (通用方式)
cybird_send.bat "bird trigger"    # 手动触发小鸟动画
cybird_send.bat "bird stats"      # 查看观鸟统计
cybird_send.bat "bird list"       # 显示可用小鸟列表
cybird_send.bat "bird reset"      # 重置统计数据

# 🐦 观鸟功能 (专用工具，更简洁)
cybird_bird.bat trigger           # 手动触发小鸟动画
cybird_bird.bat stats             # 查看观鸟统计
cybird_bird.bat list              # 显示可用小鸟列表
cybird_bird.bat reset             # 重置统计数据
cybird_bird.bat trigger COM4      # 在COM4端口触发小鸟

# 如果设备在COM4端口
cybird_cli_with_args.bat COM4
```

## ⚙️ 自定义配置

如果您经常使用不同的端口，可以修改bat文件中的默认值：

1. 右键编辑 `cybird_cli.bat`
2. 找到默认端口配置
3. 修改为您的常用端口

## 🛠️ 故障排除

### 常见问题

1. **"找不到cybird_watching_cli目录"**
   - 确保bat文件位于scripts目录中
   - 检查cybird_watching_cli文件夹是否存在

2. **"未找到uv包管理器"**
   - 安装uv: https://docs.astral.sh/uv/
   - 确保uv已添加到系统PATH

3. **设备连接失败**
   - 检查设备是否正确连接
   - 确认端口号（Windows通常是COM3, COM4等）
   - 检查设备是否被其他程序占用

4. **中文显示乱码**
   - bat文件已设置UTF-8编码 (chcp 65001)
   - 如果仍有问题，可能是终端字体不支持

### 调试模式

如果遇到问题，可以：

1. 使用详细参数启动：
   ```bash
   cybird_cli_with_args.bat COM4 115200
   ```

2. 先测试基本通信：
   ```bash
   cybird_send.bat "help"
   ```

3. 查看设备信息：
   ```bash
   cybird_send.bat "status"
   ```

## 💡 使用技巧

1. **创建桌面快捷方式**
   - 右键 `cybird_cli.bat` → 发送到桌面快捷方式
   - 双击桌面快捷方式即可快速启动

2. **添加到PATH**
   - 将scripts目录添加到系统PATH
   - 可在任何位置直接运行 `cybird_cli.bat`

3. **常用命令收藏**
   - 创建不同的bat文件用于常用命令
   - 例如：`cybird_log.bat`, `cybird_status.bat` 等

## 📝 示例

### 日常使用流程

```bash
# 1. 启动交互模式
cybird_cli.bat

# 2. 在交互模式中使用命令：
[ON] CybirdWatching> status        # 查看状态
[ON] CybirdWatching> log           # 查看日志
[ON] CybirdWatching> bird trigger  # 触发小鸟动画
[ON] CybirdWatching> bird stats    # 查看观鸟统计
[ON] CybirdWatching> quit          # 退出
```

### 快速检查

```bash
# 快速状态检查
cybird_send.bat "status"

# 如果状态正常，查看日志
cybird_send.bat "log lines 20"

# 测试观鸟功能
cybird_bird.bat trigger
cybird_bird.bat stats
```

### 不同设备切换

```bash
# 设备1 (COM3)
cybird_cli_with_args.bat COM3

# 设备2 (COM4)
cybird_cli_with_args.bat COM4
```

这些工具让您可以更方便地使用CybirdWatching CLI，无需记住复杂的命令行参数！