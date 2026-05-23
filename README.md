# 7zBatchCompressionScript

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey)]()

🖥️ 一款轻量级 Python/Tkinter 桌面工具，基于 7-Zip CLI 实现高效、稳定的批量文件压缩。完全依赖 Python 标准库，开箱即用，支持后台异步处理与灵活的预设管理。

## ✨ 核心特性
- 🚀 **高效稳定**：直接调用官方 `7z.exe`/`7za.exe`，支持全部 7-Zip 压缩算法与级别
- 📦 **零强制依赖**：仅使用 Python 标准库（`tkinter`, `threading`, `json` 等），无需额外安装第三方包
- ⚡ **后台异步**：压缩任务在独立线程运行，UI 全程流畅响应，支持随时取消
- 🎛️ **灵活模式**：支持「合并压缩」与「独立压缩」，输出路径可自定义或每次询问
- 💾 **预设持久化**：配置以 JSON 形式保存至 `%APPDATA%`，一键复用常用参数
- 🖱️ **可选拖放**：集成 `tkinterdnd2`，未安装时自动降级为按钮添加，无缝兼容
- 🌐 **全中文界面**：专为中文用户设计，交互逻辑符合直觉

## 📸 界面预览
<!-- 建议在此处插入 1~2 张 GUI 运行截图 -->
> 💡 提示：在项目根目录创建 `screenshots/` 文件夹，替换下方占位符即可自动渲染。
> `![主界面](screenshots/main_window.png)`

## 📦 环境准备
### 必装依赖
1. **Python 3.8+**
2. **7-Zip**：必须已安装。程序启动时会自动检测系统 `PATH` 或默认路径 `C:\Program Files\7-Zip\7z.exe`。
   - 官方下载：https://www.7-zip.org/

### 可选依赖
- `tkinterdnd2`：启用文件拖放功能。未安装时不影响核心功能，将自动使用按钮添加。
  ```bash
  pip install tkinterdnd2
  ```

## 🚀 快速开始
```powershell
# 1. 克隆项目
git clone https://github.com/你的用户名/7zBatchCompressionScript.git
cd 7zBatchCompressionScript

# 2. 创建并激活虚拟环境
python -m venv .venv
.\.venv\Scripts\Activate.ps1  # Windows PowerShell

# 3. 安装可选依赖（如需拖放）
pip install tkinterdnd2

# 4. 启动程序
python main.py
```

## 📂 项目结构
| 路径 | 说明 |
|------|------|
| `main.py` | 程序入口 |
| `src/models.py` | `CompressPreset` 数据模型 + 常量（压缩级别、算法列表等） |
| `src/archiver.py` | 7-Zip 交互层：`find_7z` 发现、`build_7z_command` 构建、`run_7z` 执行 |
| `src/task.py` | `CompressionTask` 后台线程编排（压缩 → 验证 → 清理） |
| `src/settings.py` | `Settings` — JSON 配置持久化管理 |
| `src/dnd.py` | `tkdnd` Tcl 扩展加载器（可选依赖） |
| `src/ui/main_window.py` | `MainWindow` 主窗口逻辑 + `run_app` 启动器 |
| `src/ui/widgets.py` | `FileListFrame` 自定义文件列表组件 |
| `src/ui/dialogs.py` | `PresetDialog`、`SettingsDialog`、`ManagePresetsDialog` |

## 🔗 模块依赖关系
```
models.py (无依赖)
  ↑
archiver.py (依赖 models)
  ↑
task.py      (依赖 models + archiver)
  ↑
settings.py  (依赖 models)
  ↑
ui/*         (依赖 task + settings)
```
> 💡 **设计原则**：核心逻辑与 UI 完全解耦，便于后续单元测试、迁移至其他 GUI 框架或封装为 CLI 工具。

## ⚙️ 功能说明
### 压缩模式
| 模式 | 说明 | 适用场景 |
|------|------|----------|
| **合并模式** | 所有选中文件打包为单个压缩包 | 归档零散文件、备份数据集 |
| **独立模式** | 每个源文件单独生成一个压缩包 | 批量分发、单文件加密压缩 |

### 输出路径策略
- 📍 **与源文件同目录**：快速生成，适合临时打包
- 📁 **自定义目录**：集中管理输出结果，支持一键选择文件夹
- ❓ **每次询问**：灵活控制每次压缩的目标位置

### 数据存储路径
所有用户配置与预设均保存在系统独立目录，不污染项目源码：
- Windows: `%APPDATA%\7zBatchCompressionScript\presets.json`

## 🛠 开发者指南
### 架构亮点
- **命令构建与执行分离**：`archiver.py` 仅负责 CLI 参数拼接与子进程调用，易于替换或测试
- **线程安全更新**：`task.py` 通过标准队列与 Tkinter `after()` 机制安全刷新 UI，彻底避免跨线程崩溃
- **降级兼容策略**：拖放功能按需加载，保障无 `tkinterdnd2` 环境下的基础可用性

### 参与贡献
1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/你的功能`)
3. 提交更改 (`git commit -m 'feat: 添加XXX功能'`)
4. 推送分支 (`git push origin feature/你的功能`)
5. 提交 Pull Request

> 📝 请遵循 PEP 8 代码规范，并在提交前运行基础测试。

## 🗺️ 后续计划
- [ ] 测试项目,没有后续计划

---
⭐ 如果这个项目对你有帮助，欢迎 **Star** 支持！  
🐛 遇到 Bug 或有功能建议？请提交 [Issues](https://github.com/unstrve/7zBatchCompressionScript/issues) 或发起 Pull Request。
