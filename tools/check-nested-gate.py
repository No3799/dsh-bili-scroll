#!/usr/bin/env python3
"""check-nested-gate.py —— 「在有意思的评论下 @ 你」那道质量闸门的回归检查。

**不联网、不连账号**：只 import vendored 的 mcp_server，直接对 `_nested_gate()` 喂用例。

这道闸门存在的理由（为什么不能交给模型自己判断）：
模型对「有意思」的标准太宽 —— 一句「大肥鱼」「笑死」在它眼里也算有趣，
结果就是往人堆里挤；而热评底下本来就一堆人抢答，回进去最像机器人。
所以这里用**可判定**的规则兜底：

  ① 那条评论已有 > 20 条回复        → 不挤（挤进去没人看得见）
  ② 那条留言像 AI / 机器人发的      → 不回（跟机器人对话没意义）
  ③ 楼里在对骂（人身攻击）          → 不进（只会变成拱火）
  ④ 楼里在抵触玩梗（"讨厌X""别刷了"）→ 不进（会被当成同一类人）
  ⑤ 留言去标点 < 10 字              → 不进（基本是梗或情绪）
  ⑥ 命中梗词 且 < 20 字             → 不进（玩梗）
  ⑦ 基本是重复字符                  → 不进（刷屏）
  ⑧ 整楼抽样 > 60% 是梗 / 短句      → 不进（这楼已经变味）
  （没传 parent_text → 直接拒，等于强制模型把原文交出来）

用法：
    <家目录>/.venv/Scripts/python.exe tools/check-nested-gate.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'vendor', 'bilibili-mcp'))

from mcp_server import _nested_gate  # noqa: E402

GOOD = "我在那条路住过三年，视频里第二家店去年就关门了"
JUNK_THREAD = "大肥鱼\n笑死\n典\n绷不住了\n哈哈哈哈"
OK_THREAD = ("这个价格是含税的吧？\n对，我上个月买过，含税 219\n"
             "那家店周末要排队两小时\n我周六去的，十点就没号了")

# (留言, 回复数, 楼中楼抽样, 期望放行?, 这条在验什么)
CASES = [
    (GOOD, 0, "", True, "正常留言，没有楼"),
    (GOOD, 3, "", True, "楼里 3 条，还好"),
    (GOOD, 20, "", True, "刚好 20 条（>20 才拒）"),
    (GOOD, 21, "", False, "① 21 条 → 不往里挤"),

    ("作为AI，我觉得这条视频很有意义，值得一看", 0, "", False, "② 自称 AI"),
    ("由AI生成：这条视频讲了三件事", 0, "", False, "② 标注 AI 生成"),
    ("我是机器人，正在学习中，请多关照", 0, "", False, "② 自称机器人"),
    ("AI总结：本期重点在于供应链成本", 0, "", False, "② AI 总结"),
    ("你觉得 DeepSeek 和 GPT 哪个好用", 0, "", True, "② 真人在讨论 AI，不该误伤"),

    ("讨厌大肥鱼，这梗还没完没了了", 3, "", False, "④ 留言在抵触玩梗"),
    (GOOD, 5, "别刷大肥鱼了行不行\n烦死了\n这梗早就烂了", False, "④ 楼里在抵触玩梗"),
    (GOOD, 5, "你有病吧\n闭嘴", False, "③ 楼里在对骂"),
    (GOOD, 5, "我讨厌这个观点\n但他说得有道理", True, "④ 只是意见不同（没梗）→ 可以进"),

    (GOOD, 5, JUNK_THREAD, False, "⑧ 整楼全是梗"),
    (GOOD, 5, OK_THREAD, True, "⑧ 整楼在正常讨论"),
    ("大肥鱼", 2, "", False, "⑤/⑥ 留言本身就是梗"),
    ("这里说错了，2023 款才有这个接口", 8, JUNK_THREAD, False, "留言够格但楼烂了"),
    ("", 5, "", False, "没传原文 → 拒"),
    ("aaaaaaaaaaaaaaaaaaaa", 0, "", False, "⑦ 重复字符"),
]

fail = 0
for text, rcount, sample, should_pass, why in CASES:
    got = _nested_gate(text, rcount, sample)
    passed = (got == "")
    ok = (passed == should_pass)
    if not ok:
        fail += 1
    tag = "放行" if passed else "拒绝"
    print(('  ✓ ' if ok else '  ✗ ') + '[' + tag + '] ' + why
          + ('' if ok else '   ← 期望' + ('放行' if should_pass else '拒绝') + '：' + got))

print('\n✓ 闸门 %d 项全过' % len(CASES) if fail == 0 else '\n✗ %d 项不符' % fail)
sys.exit(0 if fail == 0 else 1)
