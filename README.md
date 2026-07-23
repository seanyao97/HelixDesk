# HelixDesk 🧬

> 精简版电子实验记录本 (ELN) — 仿 Vara 研算，专为生物医学实验室设计。
> 提供 **Python 桌面版** 和 **Web 版** 两种方式使用。

## 版本

| 版本 | 技术栈 | 使用方式 |
|------|--------|----------|
| **Web 版** | HTML + CSS + JS + localStorage | 双击 `web/index.html` 或在浏览器打开 |
| **桌面版** | Python + PySide6 + SQLite | `pip install -r requirements.txt && python main.py` |

## 功能

- 📅 **计划表** — 月历视图，展示每日实验和待办事项
- 🧪 **实验管理** — 项目分组、实验卡片、步骤时间线、结果记录
- ⚙️ **参数管理** — 名称/值/单位，关联实验
- 📝 **运行日志** — 每次运行的观察/偏差/结论，版本追踪
- 🧫 **材料库** — 标签式材料管理
- 📥 **导出** — Markdown 导出 / JSON 数据备份
- 🔍 **搜索** — 全文搜索实验、材料

## 快速开始

### Web 版（推荐）

```bash
git clone https://github.com/seanyao97/HelixDesk.git
cd HelixDesk/web
# 双击 index.html 即可
```

### 桌面版

```bash
pip install PySide6
python main.py
```

## 技术栈

| 层 | Web 版 | 桌面版 |
|---|--------|--------|
| GUI | 浏览器 | PySide6 (Qt6) |
| 数据 | localStorage | SQLite3 |
| 语言 | JavaScript | Python 3.12+ |

## 数据存储

- **Web 版**: 浏览器 localStorage，支持 JSON 导入/导出备份
- **桌面版**: `%APPDATA%/HelixDesk/helixdesk.db`，支持自定义路径