# Security Policy — tdca-community-playground

## 社区算力 Key 条款

- 本仓库配置的社区体验 Key（`COMMUNITY_API_KEY`，GitHub Secrets 托管，配置后永不回显）**仅限本仓库官方 GitHub Actions 容器调用**。
- 任何第三方插件、Fork 副本或外部脚本对该 Key 的调用尝试，后果自负；Key 一经泄露即吊销换新。
- **熔断守卫（fail-closed）**：工作流内置前置守卫——单日消耗 >¥5 或月度 >¥20 自动拒绝执行；主仓库 daily-obs 每日独立观察，超限即告警并人工吊销。
- 消耗记账为模拟态（SIMULATED）：匿名审计（ID92），台账公开可查 `.tdca-nca/services/community/`，真实结算接口开通前不产生真实现金流。

## 漏洞报告

发现安全问题请开 Issue 说明「存在安全问题待对接」（**勿在 Issue 中披露细节**），维护者将私下联系；确认 ≤48h，修复 ≤90 天（与主仓库 SECURITY 口径一致）。
