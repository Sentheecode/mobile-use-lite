# Mobile-Use Lite — 完整 PRD（v0.1）

> **读这一份就够。** 分册（architecture / services / api / phases / risks）仅作备份细表，日常执行以本文为准。  
> 状态：设计候选 · 旁线（项圈 1.0 优先）· 2026-10-16

---

## 0. 一句话

自研手机 GUI Agent 简版：**截图 → VL 分析 → 结构化动作 → harness 执行 → 新截图**。不依赖阿里云商业 Mobile-Use 运行时；编码优先 **oc + 免费 DeepSeek**；仓库以后可挂 Origin；**默认不开 Cloud Agent**。

---

## 1. 背景与边界

阿里云 Mobile-Use = 云端看图出 `tool_calls`（SSE），**真机执行在调用方**。我们自研同构闭环：自定动作 schema + mock/ADB harness。

| 做 | 不做 |
|----|------|
| 六类动作闭环、Sensitive gate、P0 mock → P1 Android 短路径 | 封装商业 Mobile-Use 为默认运行时 |
| 坐标 0–999 归一化再换像素 | iOS 控整机 / 越狱 |
| 支付·验证码·登录一律人确认 | 跨 App 长规划、DeepLink（P3 以后） |
| 旁线探索、可随时让路项圈 | 争主线排期、主动开 Cloud Agent |

---

## 2. 场景

| ID | 场景 | 阶段 |
|----|------|------|
| SC-1 | 假截图跑通状态机到 `done` | P0 |
| SC-2 | Android 开指定 App，3–8 步短路径 | P1 |
| SC-3 | 登录/支付样例屏 → 暂停等人 | P0 约定 / P1 实机 |
| SC-4 | iPhone 本地小 VL「看图建议」，人点确认 | P2 可选 |

反场景：自动支付、自动填验证码、跨无关 App 长程规划。

---

## 3. 功能需求（精简）

**会话**  
- FR-01 多轮：任务 + 当前截图（+可选历史元数据）  
- FR-02 每轮输出结构化动作；结束靠 `done` 或错误终止  
- FR-03 状态：`running` / `waiting_human` / `succeeded` / `failed` / `cancelled`  
- FR-04 Sensitive gate 解除后可继续  

**动作**（FR-10..14）  
`click` · `swipe` · `type` · `back` · `wait` · `done`；坐标整数 0–999；未知类型 → 明确错误，不静默忽略。

**Harness**  
- FR-20 P0 MockDriver（假截图剧本）  
- FR-21 P1 AdbDriver：截图 + 六类动作  
- FR-22 归一化→像素公式单测锁死  

**安全**  
- FR-30 识别/配置敏感屏 → `waiting_human`  
- FR-31 人确认或中止前不执行副作用  

**工程**  
- FR-40 契约以本文 + 备份 `api` 为准  
- FR-41 实现优先 oc；无明确同意不开 Cloud Agent  

非功能要点：P0 单轮 mock < 数秒级；密钥不进仓库；旁线可随时冻。

---

## 4. 架构（一张图说清）

```
操作者 → Session（状态机）
            ↓
         Agent（VL/Stub → 动作 JSON）
            ↓
         Harness（Mock / ADB）
            ↓
         设备截图 ──回灌──→ 下一轮
敏感屏 → waiting_human → 人确认 → 继续
```

四块：`session` · `agent` · `harness` · `model`（Stub / DeepSeek API / 日后本机 VL）。

建议目录（开工后）：

```
mobile-use-lite/
  docs/PRD-完整版.md   ← 你在读的这份
  schemas/             ← action JSON Schema
  src/session|agent|harness|model/
  fixtures/            ← P0 假截图剧本
```

---

## 5. 动作与内部接口（精华）

公共字段：`type`（必填）、`reason`（可选）。

```json
{"type":"click","x":512,"y":780,"reason":"点开始"}
{"type":"swipe","x1":500,"y1":800,"x2":500,"y2":200,"duration_ms":300}
{"type":"type","text":"hello"}
{"type":"back"}
{"type":"wait","ms":800}
{"type":"done","status":"succeeded"}
```

像素：`px = round(norm / 999 * (size_px - 1))`。  
单轮建议 1 个主动作 + 可选 `wait`；`done` 必须是该轮最后一项。

会话续轮：`session_id` + 上一动作执行结果 + **最新一张截图**。  
常见错误：`E_SCHEMA` · `E_MAX_TURNS` · `E_SENSITIVE` · `E_DEVICE` · `E_MODEL`。

可选：以后做 OpenAI-like / SSE 外壳，**不阻塞 P0**。细表见备份 `docs/api.md`。

---

## 6. 阶段与验收

| 阶段 | 做什么 | 过关线 |
|------|--------|--------|
| **P0** | Schema + Mock 闭环 + Sensitive 假屏 | 假剧本到 `done`；非法动作报错 |
| **P1** | Android ADB 一条短路径 | 同剧本连跑 ≥2 次（可含人工确认） |
| **P2** | iPhone 本机 2B–4B VL 建议模式 | 只建议、不宣称控整机 |
| **P3** | 跨 App / DeepLink | **明确不做**，进 backlog |

**待拍板（开工前）**  
1. P0：Stub 固定剧本（推荐）还是直接接 DeepSeek？  
2. P1：哪个 App + 哪条 3–8 步路径（避开登录墙）？  
3. P2：进近期还是 backlog？

---

## 7. 风险（只记会挡路的）

1. **抢项圈主线** → 冲突时冻本项目。  
2. **iOS 沙盒** → 不承诺控整机。  
3. **小 VL 点不准** → P0/P1 用 Stub/云 API 保工程；本机 VL 降级为建议。  
4. **误点支付** → Sensitive gate 默认严。  
5. **ADB/机子占用** → 不与项圈硬件调试抢设备。

---

## 8. 执行约定

1. 日常改需求：**只改本完整版**，再视需要同步分册备份。  
2. 编码：**oc + 免费 DeepSeek**；push 需确认；Origin 可挂。  
3. **无明确同意，不开 Cursor Cloud Agent。**  
4. 文档确认 + 上面 3 个拍板完成前，**不写业务代码**。

---

## 附录 · 术语

| 词 | 含义 |
|----|------|
| Agent 环 | 截图→推理→动作→执行→再截图 |
| Harness | 把动作落到 mock/ADB 的执行层 |
| 0–999 | 归一化坐标 |
| Sensitive gate | 敏感步暂停等人 |

分册备份：`docs/PRD.md` · `architecture.md` · `services.md` · `api.md` · `phases.md` · `risks.md`（细节查阅用，非日常入口）。
