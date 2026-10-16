# 接口约定 — Mobile-Use Lite

| 字段 | 值 |
|------|-----|
| 文档版本 | v0.1（对齐 PRD v0.1） |
| 状态 | 设计候选 |
| 关联 | PRD FR-10..14 · services · architecture |

## 文档修订

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.1 | 2026-10-16 | 首版：内部 API、动作 schema、会话协议、错误码、可选 SSE 兼容 |

本阶段**只定契约，不实现**。日后代码必须以本文为单源语义；若实现偏离，先改文档再改代码。

---

## 1. 约定总则

- 内部交换格式：**JSON**，UTF-8。  
- 坐标：**整数 0–999**（含），相对当前截图宽/高；`(0,0)` 为左上。  
  - 像素换算：`px_x = round(x / 999 * (width_px - 1))`（实现须单测锁死，避免 off-by-one 争议）。  
- 时间戳：ISO 8601；对外展示按用户时区 Asia/Shanghai。  
- 动作列表：单轮可含 **1..N** 个动作；建议 P0 单轮 1 个主动作 + 可选 `wait`，降低复合失败面。  
- `done` 与其它动作互斥：若出现 `done`，应为该轮最后一个动作，且其后不得再执行副作用动作。

---

## 2. 动作 Schema

### 2.1 公共字段

```json
{
  "type": "click",
  "reason": "可选：模型简述为何做此步"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| type | string | 是 | 枚举见下 |
| reason | string | 否 | 人类可读；日志可截断 |

### 2.2 click

```json
{
  "type": "click",
  "x": 512,
  "y": 780,
  "reason": "点击「开始」按钮"
}
```

| 字段 | 约束 |
|------|------|
| x, y | 整数 0–999 |

### 2.3 swipe

```json
{
  "type": "swipe",
  "x1": 500,
  "y1": 800,
  "x2": 500,
  "y2": 200,
  "duration_ms": 300,
  "reason": "上滑列表"
}
```

| 字段 | 约束 |
|------|------|
| x1,y1,x2,y2 | 整数 0–999 |
| duration_ms | 正整数；默认 300 |

### 2.4 type

```json
{
  "type": "type",
  "text": "hello",
  "reason": "搜索框输入"
}
```

| 字段 | 约束 |
|------|------|
| text | 字符串；P0 假定可打印 ASCII/常见 Unicode；密码场景必须先过 Sensitive gate |

### 2.5 back

```json
{
  "type": "back",
  "reason": "返回上一页"
}
```

无额外字段。ADB 映射为 BACK keyevent；mock 按剧本处理。

### 2.6 wait

```json
{
  "type": "wait",
  "duration_ms": 1500,
  "reason": "等待加载"
}
```

| 字段 | 约束 |
|------|------|
| duration_ms | 正整数；建议封顶（如 10000）防滥用 |

### 2.7 done

```json
{
  "type": "done",
  "success": true,
  "message": "已到达目标页",
  "reason": "任务完成"
}
```

| 字段 | 约束 |
|------|------|
| success | boolean |
| message | 可选摘要 |

### 2.8 单轮输出包（Agent → Session）

```json
{
  "actions": [
    { "type": "click", "x": 100, "y": 200, "reason": "打开菜单" }
  ],
  "sensitive_hint": false,
  "notes": "可选模型旁白"
}
```

| 字段 | 说明 |
|------|------|
| actions | 数组；校验失败则整包拒绝 |
| sensitive_hint | 模型自报敏感；**session 仍可独立启发式加严** |
| notes | 不执行 |

---

## 3. 截图入参

### 3.1 引用对象

```json
{
  "screenshot_ref": "fixtures/p0/turn_003.png",
  "width_px": 1179,
  "height_px": 2556,
  "captured_at": "2026-10-16T13:00:00+08:00",
  "source": "mock"
}
```

| 字段 | 说明 |
|------|------|
| screenshot_ref | 本地路径或内容寻址 ID |
| width_px / height_px | driver 提供；agent/model 可只传图 |
| source | `mock` \| `adb` \| `ios_local` |

### 3.2 交给模型时

- 内部：`screenshot_ref` + 由 model 适配层读文件。  
- OpenAI-like：image 用 base64 data URL 或厂商要求的 URL（**默认不上传公网图床**）。

---

## 4. 会话续轮协议

### 4.1 创建会话

`POST /internal/sessions`（逻辑端点；P0 可为函数调用）

请求：

```json
{
  "goal": "打开设置并进入关于手机",
  "driver": "mock",
  "driver_opts": { "script_id": "settings_about_v1" },
  "model_profile": "stub",
  "max_turns": 20
}
```

响应：

```json
{
  "session_id": "ses_01HXYZ",
  "status": "created"
}
```

### 4.2 启动 / 跑一轮

`POST /internal/sessions/{id}/start` → 进入 `running`，拉截图，调 agent，经 gate，调 harness，写 turn。

`POST /internal/sessions/{id}/step` — 可选：单步调试。

### 4.3 人工确认

当 `status == waiting_human`：

```json
POST /internal/sessions/{id}/human
{
  "decision": "approve",
  "actor": "senthee",
  "comment": "确认是测试账号登录"
}
```

`decision`：`approve` | `reject`。  
`reject` → `cancelled`（或可配置为 failed；**v0.1 定为 cancelled**）。

### 4.4 查询

`GET /internal/sessions/{id}`

```json
{
  "session_id": "ses_01HXYZ",
  "status": "running",
  "goal": "...",
  "turn_count": 3,
  "max_turns": 20,
  "last_screenshot_ref": "....",
  "pending_sensitive": null,
  "turns": [
    {
      "index": 1,
      "actions": [{ "type": "click", "x": 10, "y": 20 }],
      "results": [{ "ok": true }],
      "screenshot_after": "..."
    }
  ]
}
```

### 4.5 取消

`POST /internal/sessions/{id}/cancel` → `cancelled`。

### 4.6 续轮上下文（给 Agent）

每轮 agent 输入逻辑结构：

```json
{
  "goal": "...",
  "turn_index": 4,
  "history_summary": [
    { "actions": ["click"], "ok": true }
  ],
  "screenshot": { "screenshot_ref": "...", "width_px": 1080, "height_px": 2400 },
  "device": { "platform": "android", "driver": "adb" }
}
```

历史可只保留最近 K 轮全文 + 更早摘要，防上下文爆炸（K 默认 5，配置项）。

---

## 5. Harness 内部接口（逻辑）

```text
device_info() -> { platform, width_px, height_px, serial? }
screenshot() -> ScreenshotRef
execute(actions: Action[]) -> { results: ActionResult[], screenshot: ScreenshotRef }
```

`ActionResult`：

```json
{
  "ok": true,
  "error_code": null,
  "message": null,
  "meta": { "px_x": 540, "px_y": 1200 }
}
```

---

## 6. 错误码

| 码 | 含义 | 典型来源 |
|----|------|----------|
| `E_OK` | 成功（通常用 ok:true，不必带码） | — |
| `E_SCHEMA` | 动作 JSON 不符合 schema | agent |
| `E_COORD_RANGE` | 坐标越界 | agent 校验 / harness |
| `E_MODEL_TIMEOUT` | 模型超时 | model |
| `E_MODEL_AUTH` | 鉴权失败 | model |
| `E_MODEL_RATE` | 限流 | model |
| `E_PARSE` | 模型输出无法解析 | agent |
| `E_SENSITIVE_BLOCK` | 未确认的敏感动作被拦 | session |
| `E_DRIVER` | 执行失败（ADB 断开等） | harness |
| `E_SCREENSHOT` | 截图失败 | harness |
| `E_MAX_TURNS` | 超过最大轮次 | session |
| `E_CANCELLED` | 用户取消 / 拒绝敏感 | session |
| `E_INTERNAL` | 未知内部错 | any |

会话进入 `failed` 时，响应带 `error_code` + `detail`。

---

## 7. Sensitive gate 事件

触发后 session 置 `waiting_human`，并附：

```json
{
  "pending_sensitive": {
    "reason": "heuristic:login_screen",
    "blocked_actions": [{ "type": "type", "text": "***" }],
    "screenshot_ref": "..."
  }
}
```

启发式来源（v0.1 约定，实现可渐进）：

- 任务 goal 含支付/验证码/登录等关键词。  
- 模型 `sensitive_hint: true`。  
- （P1+）简单 UI 文案/模板匹配。

明文密码不得写入 `blocked_actions` 的持久日志；展示可用掩码。

---

## 8. 可选：OpenAI-like / SSE 兼容

**目的：** 对照商业 Mobile-Use「SSE + tool_calls」，降低以后换云推理的摩擦。**非 P0 必做。**

### 8.1 tool 定义示例（概念）

将内部动作映射为 tools，例如 `mobile_click`、`mobile_swipe`… 参数与第 2 节字段同构。

### 8.2 SSE 事件（可选适配层）

| event | data 含义 |
|-------|-----------|
| `session.updated` | 状态变更 |
| `action.proposed` | 模型提出的动作 |
| `action.executed` | harness 结果 |
| `human.required` | 进入 waiting_human |
| `error` | 错误码 |
| `done` | 会话终态 |

商业 API 的字段名不必逐字相同；适配层负责映射。**主路径仍以内部 JSON 协议为准。**

---

## 9. 版本与兼容

- 动作 `type` 枚举增补：小版本 + 文档；旧执行器遇未知 type → `E_SCHEMA`。  
- 删除/改语义：升 PRD 与本 api 版本，并在 phases 标明破坏性变更。  
- v0.1 **锁定六类动作**；扩展放到 P1 后单独评审（例如 `keyevent`、`open_app`）。

---

## 10. 变更同步

改 schema 或错误码 → bump api.md → 更新 PRD 验收条目与 fixtures 说明（phases）。
