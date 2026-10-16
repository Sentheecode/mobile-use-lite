# 分阶段交付 — Mobile-Use Lite

| 字段 | 值 |
|------|-----|
| 文档版本 | v0.1（对齐 PRD v0.1） |
| 状态 | 设计候选 |
| 关联 | PRD 里程碑 M0–M4 · architecture · api |

## 文档修订

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.1 | 2026-10-16 | P0–P3 与 PRD 验收对齐；含开工清单（仍不写代码） |

**原则：** 项圈 1.0 优先；本旁线可暂停。每阶段先满足 PRD 验收再进下一阶段。

---

## P0 — 文档 + Schema + Mock 闭环 Demo

### 范围

- 齐套设计文档（本仓库 docs/ + README）。  
- 锁定动作 schema（api.md）。  
- **开工后（非本提交）：** Mock driver + 会话状态机 + Stub/可选真实模型，假截图序列跑到 `done`。  
- Sensitive gate：假登录/支付屏 → `waiting_human`。

### 成功标准

- 文档：PRD 验收 6.1 文档项完成（本阶段目标）。  
- 代码（未来）：mock 剧本可 `succeeded`；非法动作 → `E_SCHEMA`；超轮次 → `E_MAX_TURNS`。

### 交付物

| 交付物 | 状态 |
|--------|------|
| README / PRD / architecture / services / api / phases / risks | **本提交完成** |
| `schemas/action.schema.json` + fixtures 剧本 | 决策确认后开工 |
| mock 闭环可运行入口 | 决策确认后开工 |

### 非范围

- 真机 ADB、iOS VL、远程仓库、Cloud Agent。

---

## P1 — Android ADB 真机短任务

### 范围

- AdbDriver：截图、click/swipe/type/back/wait。  
- 一条可复现短路径：打开某 App → 3–8 步 → `done`。  
- 实机验证 Sensitive gate（至少人为构造登录页）。  
- 坐标换算在目标机分辨率目视合格。

### 成功标准

- PRD 6.2 清单全勾。  
- 同一剧本连续跑通 ≥2 次（允许中途人工确认）。

### 依赖

- Android 机 + ADB 调试。  
- 模型 API 密钥或可验收的 stub+少量真调用策略。  
- **不与项圈设备资源冲突时再借机器。**

### 非范围

- 跨 App 流程、DeepLink 编排、iOS 自动点击。

---

## P2 — 可选 iPhone 本地小 VL「看图建议」

### 范围

- iPhone 16 Pro 类设备：2B–4B 量化 VL（MLX / Core ML 选型开工时再定）。  
- 输出建议动作 JSON 或可读步骤；**默认人点确认**。  
- 可与 Lite 会话「建议模式」对齐；**不宣称控整机。**

### 成功标准

- PRD 6.3；文档明确能力边界。  

### 非范围

- iOS 沙盒外系统级控制、越狱、全自动支付。

### 排期

- **可选**；不阻塞 P1。项圈忙则整体延后。

---

## P3 — 明确不做（仅议题记账）

| 议题 | 态度 |
|------|------|
| 跨 App 长规划 | 不做 |
| DeepLink 编排 | 不做 |
| 商业 Mobile-Use 运行时依赖 | 不做 |
| 多租户云服务化 | 不做 |

若未来要做：新开 PRD 版本与立项，不在 v0.1 偷偷膨胀。

---

## 目录建议（与 architecture 一致）

```
mobile-use-lite/
  README.md
  docs/           # 当前唯一实质内容
  schemas/        # P0 代码阶段
  packages/       # session, agent, harness, model
  scripts/
  fixtures/
```

当前**不要**创建 packages/ 代码；确认决策点后再建。

---

## 下一步开工清单（仍不写代码）

1. **用户确认** PRD 文末 / 回报中的 3 个决策点。  
2. 冻结 api.md 六类动作（有异议只改文档）。  
3. 选定 P0 剧本主题（与 P1 短路径尽量同构）。  
4. 准备 fixtures 截图来源方式（自行截 / 合成标注）。  
5. 密钥与隐私：DeepSeek 等 Key 放本地环境变量，不进库。  
6. 排期：与项圈 1.0 看板对齐「旁线可暂停」标记。  
7. （可选）以后挂 Origin 时的仓库名与可见性——**现在不建远程**。  
8. 编码环境：默认 oc + 免费 DeepSeek；需要 Cursor 协作再说。  
9. Cloud Agent：保持关闭直到显式同意。  
10. 开工第一刀（决策后）：`action.schema.json` + mock 状态机，而非先调 UI。

---

## 阶段门禁

| 从 | 到 | 门禁 |
|----|----|------|
| 文档 | P0 代码 | 决策点确认 + PRD v0.1 无未决红线 |
| P0 | P1 | mock 验收通过 + Android 设备就绪 |
| P1 | P2 | 显式要做 iOS 建议；否则 backlog |
| * | P3 实现 | **禁止**；仅文档议题 |
