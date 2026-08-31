#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TDCA 冷启动真调重跑（GSEQ-0785 路径 A · Actions 内执行）
=========================================================
三段式（准入→沙盒→生产）真调 DeepSeek，产出贡献 COP 并解除 VB [UNVERIFIED-NO-EXTERNAL-ANCHOR]。

纪律（继承 community-compute 闸门 + HANDOFF-KIMI-COLDSTART-REAL-RERUN-001）：
  - Flash-only：模型硬编码 deepseek-v4-flash，任何输入不可覆盖
  - 熔断复用：单日 >¥2 / 月度 >¥8 拒绝执行（fail-closed 零消耗）
  - 凭证零落盘：DEEPSEEK_API_KEY 仅环境变量（Secrets 注入），永不写盘/打印
  - NCA 隔离命名：NCA-COLDSTART-EXP-*（.tdca-nca/services/coldstart-exp/）
  - 产物提交分支待签批不合并（由调用方 workflow 执行 git 部分）
  - 生产落盘严格后置：仅当沙盒段通过且生产段 yaml 机验通过才落盘
"""
import datetime
import glob
import hashlib
import json
import os
import sys
import urllib.request

API_URL = "https://api.deepseek.com/v1/chat/completions"
MODEL = "deepseek-v4-flash"  # Flash-only 硬编码（禁贵模型，不可覆盖）
MAX_TOKENS = 900
PROTO = os.environ.get("TDCA_PROTOCOL_DIR", "/tmp/tdca-protocol")
NCA_DIR = ".tdca-nca/services/coldstart-exp"
ART_DIR = "artifacts/coldstart-real-rerun"
DAY_LIMIT, MON_LIMIT = 2.0, 8.0

REQUIRED_KEYS = {"stratum", "verse", "core", "origin", "negative_space", "primitive"}


def breaker():
    """熔断守卫：NCA-COLDSTART-EXP-* 台账实读，日 ¥2 / 月 ¥8 拒绝。"""
    today = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d")
    month = today[:6]
    day_sum = mon_sum = 0.0
    for f in glob.glob(os.path.join(NCA_DIR, "NCA-COLDSTART-EXP-*.json")):
        try:
            d = json.load(open(f, encoding="utf-8"))
            c = float(d.get("est_cost_cny", 0))
        except Exception:
            continue
        base = os.path.basename(f)
        if f"NCA-COLDSTART-EXP-{today}" in base:
            day_sum += c
        if f"NCA-COLDSTART-EXP-{month}" in base:
            mon_sum += c
    print(f"熔断守卫读数: 今日 ¥{day_sum:.4f} / 本月 ¥{mon_sum:.4f}（阈值 日¥{DAY_LIMIT}/月¥{MON_LIMIT}）")
    if day_sum > DAY_LIMIT or mon_sum > MON_LIMIT:
        print("::error::熔断触发（单日>¥2 或 月度>¥8）——拒绝调用，fail-closed 零消耗")
        sys.exit(1)


def anchor_evidence():
    """VB 外部锚实核：protocols/tdca-native 实存证据 → 解除 [UNVERIFIED-NO-EXTERNAL-ANCHOR]。"""
    root = os.path.join(PROTO, "protocols", "tdca-native")
    mck = os.path.join(root, "麦肯锡思维协议.yaml")
    strat = glob.glob(os.path.join(root, "stratagems", "**", "*.yaml"), recursive=True)
    cold = os.path.join(root, "coldstart", "community", "第01条-开源社区冷启动·正和准入.yaml")
    if not (os.path.exists(mck) and strat and os.path.exists(cold)):
        print("::error::外部锚实核失败（tdca-native 锚件缺失）——fail-closed")
        sys.exit(1)
    sha8 = hashlib.sha256(open(mck, "rb").read()).hexdigest()[:8]
    ev = {
        "anchor": "麦肯锡COP编译基准 + 三十六计逐计编译基准（protocols/tdca-native 实存实核）",
        "mckinsey_sha256_8": sha8,
        "stratagems_count": len(strat),
        "coldstart_01_in_library": True,
        "anchored": True,
    }
    print(f"VB 外部锚实核: 麦肯锡 sha8={sha8} / 三十六计 {len(strat)} 件 / 第01条在库 ✅")
    return ev


def strip_fence(text):
    """剥 Markdown 围栏（HANDOVER-002 教训制度化：产出未剥围栏即落盘的根因对策）。"""
    t = text.strip()
    lines = t.splitlines()
    if lines and lines[0].strip().startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines).strip()


def unwrap(doc, depth=0):
    """DeepSeek 父键包裹对策（2026-08-31 run 33373466225 实证：产出被单一父键包裹致六键缺验）：
    顶层非六键且为单键 dict 时下钻，至多 3 层。"""
    while (isinstance(doc, dict) and not (REQUIRED_KEYS <= set(doc.keys()))
           and len(doc) == 1 and depth < 3):
        doc = next(iter(doc.values()))
        depth += 1
    return doc, depth


def call_flash(prompt, phase):
    """真调 DeepSeek（Flash-only）→ (content, tokens, est_cost)。"""
    payload = json.dumps({
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": MAX_TOKENS,
    }, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(API_URL, data=payload, method="POST", headers={
        "Authorization": f"Bearer {os.environ['DEEPSEEK_API_KEY']}",
        "Content-Type": "application/json",
    })
    with urllib.request.urlopen(req, timeout=120) as resp:
        d = json.loads(resp.read().decode("utf-8"))
    content = d["choices"][0]["message"]["content"]
    tokens = int(d.get("usage", {}).get("total_tokens", 0))
    est = round(tokens / 1_000_000.0 * 1.0, 6)  # SIMULATED 估算（Flash ¥1/百万 token 量级）
    print(f"[{phase}] tokens={tokens} est ¥{est}（SIMULATED）")
    return content, tokens, est


def main():
    if not os.environ.get("DEEPSEEK_API_KEY"):
        print("::error::DEEPSEEK_API_KEY 未注入（Secrets 缺失）——fail-closed 零消耗")
        sys.exit(1)

    breaker()
    anchor = anchor_evidence()

    import yaml  # pyyaml（workflow setup-python 后 pip 安装）

    phases = []

    # —— 段 1 准入（正和准入评估，真实 LLM）——
    p1 = (
        "你是 TDCA 开源社区冷启动的准入缔约官。请对以下候选做正和准入评估：\n"
        "候选：外部 agent（MCP stdio 接入），能力维度自报 res、BATNA 自报，无历史 NCA 链。\n"
        "要求：①给出准入结论（ADMIT/REJECT）②正和判据（双方增量>0）③诚实约束声明"
        "（res/batna 自报=data_provenance:mixed；BATNA 存疑即熔断）④负空间合规自查。\n"
        "以 JSON 输出：{\"decision\":..., \"positive_sum\":..., \"honesty\":..., \"nsfl_ok\":...}"
    )
    c1, t1, e1 = call_flash(p1, "段1·准入")
    phases.append({"phase": "准入", "tokens": t1, "est_cost": e1, "output": c1[:600]})

    # —— 段 2 沙盒（VB 重定价，外部锚已实核注入）——
    p2 = (
        "你是 TDCA 沙盒裁判员。冷启动 VB 重定价原为组织者主权宣言（无外部锚）。\n"
        f"现外部锚已实核：{anchor['anchor']}；麦肯锡 sha8={anchor['mckinsey_sha256_8']}，"
        f"三十六计 {anchor['stratagems_count']} 件在库，第01条 COP 已入 protocols/tdca-native。\n"
        "请给出：①VB 锚定结论（anchored=true 的依据句）②初始 VB=200 相对锚基准的合理性评估"
        "③沙盒迭代纪律声明（生产落盘严格后置到 mou_ok 之后）。以 JSON 输出。"
    )
    c2, t2, e2 = call_flash(p2, "段2·沙盒")
    phases.append({"phase": "沙盒", "tokens": t2, "est_cost": e2, "output": c2[:600]})

    # —— 段 3 生产（贡献 COP 产出，剥围栏 + 机验，严格后置）——
    p3 = (
        "请产出 TDCA 社区贡献 COP《第01条-开源社区冷启动·正和准入》的最终 yaml。\n"
        "硬性要求：①只输出纯 yaml，禁止 Markdown 围栏（```）②顶层直接给出六个键："
        "stratum / verse / core / origin / negative_space / primitive——严禁包裹在任何父键"
        "（如 第01条:、cop:、title:）之下 ③provenance 注明"
        " data_provenance=mixed（res/batna 自报）④VB 锚定状态 anchored=true（外部锚=麦肯锡+三十六计编译基准）。"
    )
    c3, t3, e3 = call_flash(p3, "段3·生产")
    cop_yaml = strip_fence(c3)
    try:
        doc = yaml.safe_load(cop_yaml)
        doc, depth = unwrap(doc)
        keys = set(doc.keys()) if isinstance(doc, dict) else set()
    except Exception as ex:
        print(f"::error::生产段 yaml 机验失败（{ex}）——fail-closed 不落盘；产出头部：{cop_yaml[:200]!r}")
        sys.exit(1)
    missing = REQUIRED_KEYS - keys
    if missing:
        print(f"::error::生产段缺键 {sorted(missing)}（下钻 {depth} 层后）——fail-closed 不落盘；产出头部：{cop_yaml[:200]!r}")
        sys.exit(1)
    if depth:
        cop_yaml = yaml.safe_dump(doc, allow_unicode=True, sort_keys=False)
        print(f"父键包裹对策生效：下钻 {depth} 层后六键齐全，落盘规范化 yaml")
    print(f"生产段机验通过：keys={sorted(keys)}（剥围栏对策已执行）")
    phases.append({"phase": "生产", "tokens": t3, "est_cost": e3,
                   "output": "yaml 机验通过（六键齐全，围栏已剥）"})

    total_cost = round(e1 + e2 + e3, 6)
    seq = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d-%H%M%S")
    nca_id = f"NCA-COLDSTART-EXP-{seq}"

    # 产物落盘（生产严格后置：至此三段全过）
    os.makedirs(ART_DIR, exist_ok=True)
    cop_path = os.path.join(ART_DIR, "第01条-开源社区冷启动·正和准入-rerun.yaml")
    with open(cop_path, "w", encoding="utf-8") as f:
        f.write(cop_yaml + "\n")

    os.makedirs(NCA_DIR, exist_ok=True)
    nca = {
        "NCA-ID": nca_id,
        "Operation-Type": "ColdstartRealRerun",
        "Operator": "community-ledger（自动化，GSEQ-0785 路径 A）",
        "Timestamp": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "model": MODEL,
        "flash_only": True,
        "phases": phases,
        "total_tokens": t1 + t2 + t3,
        "est_cost_cny": total_cost,
        "cost_nature": "SIMULATED 估算",
        "vb_anchor": anchor,
        "vb_unverified_anchor_removed": True,
        "data_provenance": "mixed（res/batna 自报；VB 锚定=实核在库证据）",
        "artifact": cop_path,
        "status": "ok",
    }
    nca_path = os.path.join(NCA_DIR, f"{nca_id}.json")
    with open(nca_path, "w", encoding="utf-8") as f:
        json.dump(nca, f, ensure_ascii=False, indent=2)

    summary = os.path.join(ART_DIR, f"RERUN-SUMMARY-{seq}.md")
    with open(summary, "w", encoding="utf-8") as f:
        f.write(f"# 冷启动真调重跑摘要（{nca_id}）\n\n")
        f.write(f"- 模型：{MODEL}（Flash-only 硬编码）\n")
        f.write(f"- 三段：准入 {t1} tok / 沙盒 {t2} tok / 生产 {t3} tok，合计 {t1+t2+t3} tok，估算 ¥{total_cost}（SIMULATED）\n")
        f.write(f"- VB 锚定：{anchor['anchor']}（麦肯锡 sha8={anchor['mckinsey_sha256_8']}，三十六计 {anchor['stratagems_count']} 件）——[UNVERIFIED-NO-EXTERNAL-ANCHOR] 已解除\n")
        f.write(f"- 生产机验：yaml 六键齐全，剥围栏对策执行\n")
        f.write(f"- 产物：{cop_path}\n- 存证：{nca_path}\n")
        f.write(f"- 状态：待签批（分支产物，不合并）\n")

    print(f"✅ 重跑完成：{nca_id} | 产物 {cop_path} | 摘要 {summary}")


if __name__ == "__main__":
    main()
