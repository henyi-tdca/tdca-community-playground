# Security Policy — tdca-community-playground

## 使用即同意

使用本仓库的社区算力体验（community-compute 工作流），即表示你知悉并接受：

1. **协议准入**：每次调用前必须通过 TDCA 协议准入校验（AgentCard + enforce_check + 公理 6 反函数验证）——未过即拒，零消耗，无例外（fail-closed）。
2. **匿名审计**：每次调用生成匿名 NCA-COMMUNITY 存证（ID92，不含任何个人身份），台账公开可查 `.tdca-nca/services/community/`。
3. **模拟态记账**：消耗记账为模拟态（SIMULATED，NCA 确权 + ERI 权重），真实结算/税务接口开通前不产生真实现金流；每一笔模拟记账都是正式账本记录，接口开通后凭账本转实际结算。
4. **熔断**：单日 >¥2 / 月度 >¥8 自动拒绝执行；超限触发人工吊销换新。

## 社区算力 Key 条款

- 本仓库配置的社区体验 Key（`COMMUNITY_API_KEY`，GitHub Secrets 托管，配置后永不回显）**仅限本仓库官方 GitHub Actions 容器调用**。
- 任何第三方插件、Fork 副本或外部脚本对该 Key 的调用尝试，后果自负；Key 一经泄露即吊销换新。
- 模型仅限 Flash（代码层硬编码不可覆盖）。

## 漏洞报告

发现安全问题请开 Issue 说明「存在安全问题待对接」（**勿在 Issue 中披露细节**），维护者将私下联系；确认 ≤48h，修复 ≤90 天（与主仓库 SECURITY 口径一致）。
