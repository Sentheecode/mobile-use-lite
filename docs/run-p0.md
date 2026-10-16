# 跑通 P0（Stub + Mock）

纯本地、无网络、无真机。依赖：Python ≥ 3.10，标准库即可。

## 准备

```bash
cd /workspace/mobile-use-lite   # 或你的仓库路径
export PYTHONPATH=src
```

也可：`pip install -e .` 后直接用 `python -m mobile_use_lite` / `mobile-use-lite`。

## 剧本

| 命令 | 期望 |
|------|------|
| `--script fixtures/p0/script_happy.json` | `status: succeeded`，exit 0 |
| `--script fixtures/p0/script_sensitive.json` | 停在 `waiting_human`，exit 4 |
| 同上 + `--approve` | 自动过 Sensitive gate → `succeeded` |
| 同上 + `--reject` | `cancelled`，exit 3 |
| `--illegal-demo` | `E_SCHEMA`，exit 2 |
| `--script fixtures/p0/script_invalid.json` | Stub 吐非法 type → `failed` / `E_SCHEMA`，exit 2 |

## 示例

```bash
# 快乐路径 → done
PYTHONPATH=src python3 -m mobile_use_lite --script fixtures/p0/script_happy.json

# 敏感假屏：先停住
PYTHONPATH=src python3 -m mobile_use_lite --script fixtures/p0/script_sensitive.json

# 敏感假屏：CLI 自动批准后跑完
PYTHONPATH=src python3 -m mobile_use_lite --script fixtures/p0/script_sensitive.json --approve

# 敏感假屏：拒绝 → cancelled
PYTHONPATH=src python3 -m mobile_use_lite --script fixtures/p0/script_sensitive.json --reject

# 非法动作校验
PYTHONPATH=src python3 -m mobile_use_lite --illegal-demo

# 坐标公式自检
PYTHONPATH=src python3 -m mobile_use_lite.coords
```

可选 `--json` 打印完整会话；`--goal` 覆盖剧本 goal（含「登录|支付|验证码|login|pay|password」时也会触发 gate）。

## 目录要点

- `schemas/` — action / turn JSON Schema（文档契约）
- `src/mobile_use_lite/` — schema 校验、coords、MockDriver、StubAgent、Session
- `fixtures/p0/` — 假截图剧本（引用 png 路径即可，P0 不读真实像素）

下一步 P1：换 AdbDriver，接真机短路径（本仓库旁线，不抢项圈设备）。
