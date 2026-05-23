# 7zBatchCompressionScript

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey)]()
[![License](https://img.shields.io/badge/License-MIT-green)]()

轻量级 Python/Tkinter 桌面工具，基于 7-Zip CLI（`7z.exe`）实现批量文件压缩，支持预设管理、后台异步压缩、密码加密与完整性验证。

## 特性

- **零外部依赖** — 仅用 Python 标准库（可选 `tkinterdnd2` 启用拖放）
- **双模式压缩** — 合并打包 / 逐个独立压缩
- **预设管理器** — 创建、编辑、删除、导出、导入、设为默认
- **后台异步执行** — UI 不卡顿，支持随时取消
- **实时进度窗口** — 进度条、逐文件详情表、完整日志、支持导出
- **完整性验证** — 可选压缩后自动 SHA256 校验 + 7z 自检
- **主题切换** — 现代风格 / Windows 原生风格
- **密码安全** — 机器绑定加密存储 + stdin 传入（避免进程列表泄漏）
- **全中文界面**

## 环境要求

| 依赖 | 说明 |
|------|------|
| **Python** | ≥ 3.10 |
| **7-Zip** | 必须安装，自动检测 PATH 或 `C:\Program Files\7-Zip\7z.exe` |

可选安装：

```bash
pip install tkinterdnd2    # 启用文件拖放
```

## 快速开始

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install tkinterdnd2     # 可选
python main.py
```

## 项目结构

```
main.py                     # 入口
src/
├── app.py                  # 应用启动（组装所有模块）
├── models.py               # CompressPreset 数据模型
├── crypto.py               # 密码加密 / 解密（PBKDF2）
├── dnd.py                  # tkdnd 拖放扩展加载（可选）
├── core/
│   ├── archive_service.py      # 7z 命令构建 + 子进程执行（stdin 传密码）
│   ├── compression_service.py  # 压缩流程编排（压缩 -> 验证 -> 删除）
│   ├── settings_service.py     # JSON 持久化（密码自动加密）
│   └── progress_events.py      # 事件总线（UI 与后台线程通信）
├── utils/
│   ├── filesystem.py       # 文件操作（SHA256、路径计算、删除）
│   ├── formats.py          # 大小 / 时间格式化
│   └── parsers.py          # 7z 进度解析
└── ui/
    ├── main_window.py      # 主窗口
    ├── widgets.py          # FileListFrame 文件列表
    ├── dialogs.py          # PresetDialog / ManagePresetsDialog / SettingsDialog
    ├── progress_window.py  # 进度窗口（进度条 + 文件表 + 日志）
    └── theme.py            # 主题定义
```

## 模块依赖

```
models.py (无依赖)
  ^ crypto.py (无依赖)
  ^ archive_service.py (依赖 models)
  ^ compression_service.py (依赖 archive_service + models + utils/*)
  ^ settings_service.py (依赖 models + crypto)
  ^ ui/* (依赖 core/* + models)
  ^ app.py (组装 core + ui)
```

## 功能说明

### 压缩模式

| 模式 | 说明 | 适用场景 |
|------|------|----------|
| **合并** | 所有文件打包为单个 .7z | 归档、备份 |
| **独立** | 每个源文件单独压缩 | 批量分发、逐文件加密 |

### 输出路径

- 与源文件同目录
- 自定义目录
- 每次询问

### 预设管理

- 支持任意数量的预设，每个预设包含所有压缩参数
- 可设为默认预设，启动时自动选中
- 支持导出为 `.json` 文件、导入共享
- 支持拖放 `.json` 文件导入

### 文件列表

- 右键菜单：编辑预设 / 设为默认 / 导出 / 删除
- `Delete` 键快速移除选中项
- 可选拖放添加文件

### 进度窗口

- 实时进度条 + 状态文字
- 逐文件详情表（文件名、用时、原大小、压缩后大小、压缩比）
- 完整日志面板，支持导出为 `.txt`

## 安全设计

### 密码存储

密码以 **PBKDF2 + XOR 流加密** 存储在 `%APPDATA%\7zBatchCompressionScript\presets.json` 中，密钥派生自主机名、MAC 地址等机器特征。不同机器间无法解密。

### 命令行保护

密码通过 **stdin** 传入 7z 进程（`7z a -p ...`），不在进程列表的命令行参数中出现。UI 日志中密码被替换为 `***`。

### 导出预设

导出时密码保持明文，便于跨机器分享。

## 数据存储

```
%APPDATA%\7zBatchCompressionScript\
├── config.json              # 配置（7z 路径、主题、窗口位置）
└── presets.json             # 预设列表（密码已加密）
```

## 开发

```powershell
python main.py    # 启动 GUI
```

### 设计原则

- **持久化边界加密** — `settings_service.py` 在序列化/反序列化时加解密密码
- **命令构建与执行分离** — `archive_service.py` 只负责参数拼接和子进程
- **事件驱动 UI 更新** — `ProgressEventBus` 解耦后台线程与 Tkinter 界面

---

## 参与贡献

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/xxx`)
3. 提交更改 (`git commit -m 'feat: 添加xxx'`)
4. 推送分支 (`git push origin feature/xxx`)
5. 提交 Pull Request
