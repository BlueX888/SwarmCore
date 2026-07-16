# Example Screenshots（本地 / CI 产物）

本目录用于存放 `examples/b-design-system-tailadmin-radix` 真实运行效果的视觉 QA 截图，**不提交到 Git 仓库**。

## 生成

```bash
pip install playwright
playwright install chromium
python3 create-design-system/scripts/capture_preview_screenshots.py b-design-system-tailadmin-radix
```

## 用途

- 本地人工复查 desktop / tablet / mobile、light / dark
- GitHub Actions PR 工作流上传为 artifact（`design-system-preview.yml`）
- 记录在 `docs/spec/b-design-system-tailadmin-radix/shards/preview-qa.md`（只写路径与结论，不提交 PNG）

## 注意

- 不要把 `*.png` / `*.jpg` 加入 git
- 根目录 `.gitignore` 已忽略 `**/preview-screenshots/**`（本 README 除外）
