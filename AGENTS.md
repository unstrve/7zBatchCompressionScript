# 7zBatchCompressionScript

轻量级 Python/tkinter 桌面工具，基于 7-Zip CLI（`7z.exe` / `7za.exe`）实现批量文件压缩。

## 快速开始

```powershell
.\.venv\Scripts\Activate.ps1
python main.py
```

## 项目结构

| 路径 | 说明 |
|------|------|
| `main.py` | 入口文件 |
| `src/models.py` | `CompressPreset` 数据模型 + 常量（压缩级别、算法列表等）|
| `src/archiver.py` | 7-Zip 交互层：`find_7z` 发现、`build_7z_command` 构建命令、`run_7z` 执行进程 |
| `src/task.py` | `CompressionTask` 后台线程编排压缩流程（压缩 → 验证 → 删除）|
| `src/settings.py` | `Settings`—JSON 持久化存储于 `%APPDATA%\7zBatchCompressionScript\` |
| `src/dnd.py` | tkdnd Tcl 扩展加载，可选依赖 |
| `src/ui/main_window.py` | `MainWindow` 主窗口 + `run_app` 启动 |
| `src/ui/widgets.py` | `FileListFrame` 文件列表组件 |
| `src/ui/dialogs.py` | `PresetDialog`、`SettingsDialog`、`ManagePresetsDialog` 对话框 |

## 依赖关系

```
models.py (无依赖)
  ↑ archiver.py (依赖 models)
  ↑ task.py (依赖 models + archiver)
  ↑ settings.py (依赖 models)
  ↑ ui/* (依赖 task + settings)
```

## 关键命令

```powershell
python main.py          # 启动 GUI
```

## 重要约束

- **必须安装 7-Zip**，需在 `PATH` 中或位于 `C:\Program Files\7-Zip\7z.exe`。运行时会自动检测。
- **`tkinterdnd2` 可选**。未安装时使用「添加文件」「添加文件夹」按钮代替拖放。
- 压缩在 **后台线程** 中运行，UI 保持响应，支持取消。
- 预设以 JSON 格式存储在 `%APPDATA%\7zBatchCompressionScript\presets.json`。
- 合并模式 = 打包成一个压缩包；独立模式 = 每个源文件单独压缩。
- 输出模式：与源文件同目录、自定义目录、每次询问。
- 仅依赖 Python 标准库（可选依赖 `tkinterdnd2`）。
- 所有用户界面文本均为中文。
