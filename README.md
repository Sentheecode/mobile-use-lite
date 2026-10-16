# Mobile-Use Lite

自研手机 GUI Agent 简版：截图 → VL/Stub → 动作 → harness → 再截图。旁线；项圈 1.0 优先。

**主文档：** [docs/PRD-完整版.md](docs/PRD-完整版.md)  
**P0 怎么跑：** [docs/run-p0.md](docs/run-p0.md)

## 当前进度：P0 Stub 闭环

已实现（无网络、无真机）：

- 六类动作 schema 校验（`click` / `swipe` / `type` / `back` / `wait` / `done`）
- MockDriver 假截图剧本
- StubAgent 按帧吐固定动作
- Session 状态机 + Sensitive gate（`waiting_human`）

```bash
cd /workspace/mobile-use-lite
PYTHONPATH=src python3 -m mobile_use_lite --script fixtures/p0/script_happy.json
```

## 执行约定

1. 编码优先 oc + 免费 DeepSeek；仓库可挂 Origin；**push 需确认**。  
2. 无明确同意，不开 Cursor Cloud Agent。  
3. 日常改需求只改完整版 PRD。

分册备份在 `docs/`（architecture / services / api / phases / risks / 旧 PRD）。
