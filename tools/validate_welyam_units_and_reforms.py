"""用实际脚本 AST 检查单位校准与政改替换边界，不替代 EU4 引擎实测。"""
from __future__ import annotations

from build_welyam_tier2 import build


class Model:
    def __init__(self, effects, triggers, *, wave=18, regular=0, rebels=0, controller="A13"):
        self.effects, self.triggers = effects, triggers
        self.wave, self.regular, self.rebels = wave, regular, rebels
        self.controller = controller
        self.variables = {}
        self.flags = {"gcd_welyam_fixed_rebels_due": 0, "gcd_welyam_rebel_clock": 0}
        self.reforms = set()
        self.level, self.adm = 2, 100
        self.gov = "monarchy"
        self.operations = []
        self.spawn_calls = 0
        self.disaster = True

    def condition(self, node):
        k, v = node.key, node.value
        if k in {"trigger", "limit", "AND"}:
            return all(self.condition(c) for c in node.children())
        if k == "OR":
            return any(self.condition(c) for c in node.children())
        if k == "NOT":
            return not all(self.condition(c) for c in node.children())
        if k in self.triggers:
            return all(self.condition(c) for c in self.triggers[k].children())
        if k == "num_of_units_in_province":
            assert node.scalar("who") == "REB"
            return self.rebels >= float(node.scalar("amount"))
        if k == "units_in_province":
            return self.regular + self.rebels >= float(v)
        if k == "check_variable":
            return all(self.variables.get(c.key, 0) >= float(c.value) for c in node.children())
        if k == "owned_by":
            return v == "A13"
        if k == "controlled_by":
            return v == self.controller
        if k == "is_city":
            return v == "yes"
        if k == "can_spawn_rebels":
            return v == "noble_rebels"
        if k == "has_reform":
            return v in self.reforms
        if k == "government":
            return v == self.gov
        if k == "reform_level":
            return self.level >= int(v)
        if k == "adm_power":
            return self.adm >= int(v)
        if k == "has_disaster":
            return self.disaster
        if k == "has_country_flag":
            return v in self.flags
        if k == "tag":
            return v == "A13"
        raise AssertionError(f"未支持的校验条件：{k}")

    def execute(self, block):
        branch = None
        for n in block.children():
            k, v = n.key, n.value
            if k == "if":
                branch = self.condition(n.children("limit")[0])
                if branch:
                    self.execute(n)
            elif k == "else":
                if not branch:
                    self.execute(n)
                branch = None
            elif k in {"limit", "name", "ai_chance"}:
                continue
            elif k == "while":
                loops = 0
                while self.condition(n.children("limit")[0]):
                    loops += 1
                    assert loops <= 1024, "单位循环未能收敛"
                    self.execute(n)
            elif k in {"set_variable", "change_variable"}:
                for c in n.children():
                    self.variables[c.key] = (self.variables.get(c.key, 0) if k == "change_variable" else 0) + float(c.value)
            elif k == "spawn_rebels":
                assert n.scalar("type") == "noble_rebels" and n.scalar("size") == "3"
                self.rebels += self.wave
                self.spawn_calls += 1
            elif k == "kill_units":
                assert n.scalar("who") == "REB", "不能删除玩家/其他国家的单位"
                amount = n.scalar("amount")
                self.rebels = max(0, self.rebels - int(amount)) if amount else 0
            elif k == "random_owned_province":
                if self.condition(n.children("limit")[0]):
                    self.execute(n)
            elif k == "owner":
                self.execute(n)
            elif k == "set_country_flag":
                self.flags[v] = 730
            elif k == "clr_country_flag":
                self.flags.pop(v, None)
            elif k == "remove_government_reform":
                self.reforms.discard(v)
                self.operations.append((k, v))
            elif k == "add_government_reform":
                self.reforms.add(v)
                self.operations.append((k, v))
            elif k in self.effects:
                self.execute(self.effects[k])
            else:
                raise AssertionError(f"未支持的校验效果：{k}")


def validate(effects, triggers, missions, events, anb):
    # 原生生成数量随引擎而变；输入多种生成结果后，新脚本都必须校准成 12 团。
    for wave in range(1, 81):
        model = Model(effects, triggers, wave=wave)
        model.execute(effects["gcd_welyam_try_spawn_fixed_rebels_effect"])
        assert model.rebels == 12 and model.regular == 0, wave
        assert "gcd_welyam_fixed_rebels_due" not in model.flags
        # 生成器不能改写安排事件的时钟日期。
        assert model.flags["gcd_welyam_rebel_clock"] == 0
    # 无部队生成/异常巨大数量应有上限并回收本次生成，不能死循环或留下错误规模。
    for wave in (0, 600):
        model = Model(effects, triggers, wave=wave)
        model.execute(effects["gcd_welyam_try_spawn_fixed_rebels_effect"])
        assert model.rebels == 0
        assert "gcd_welyam_fixed_rebels_due" in model.flags
        assert "gcd_welyam_fixed_rebels_failed" in model.flags
    # 既有玩家军队、既有叛军和敌方控制的省份不参与校准。
    for regular, rebels, controller in ((10, 0, "A13"), (0, 7, "A13"), (0, 0, "A50")):
        model = Model(effects, triggers, regular=regular, rebels=rebels, controller=controller)
        model.execute(effects["gcd_welyam_try_spawn_fixed_rebels_effect"])
        assert model.regular == regular and model.rebels == rebels and model.spawn_calls == 0
        assert "gcd_welyam_fixed_rebels_due" in model.flags
    # 隐藏事件在任务二完成/灾难结束后到达，也必须清队列并不生成部队。
    option = events["gcd_welyam.91"].children("option")[0]
    for ended, stopped in ((False, False), (False, True), (True, False)):
        model = Model(effects, triggers)
        model.flags["gcd_welyam_rebel_event_queued"] = 0
        model.disaster = not ended
        if stopped:
            model.flags["gcd_welyam_rebel_spawn_stopped"] = 0
        model.execute(option)
        assert model.rebels == (0 if ended or stopped else 12)
        assert "gcd_welyam_rebel_event_queued" not in model.flags

    # 读取真实二级列表，所有 94 个选择都必须归一到目标，其他层不受影响。
    _, metadata = build(anb)
    second_tier = set(metadata["reforms"])
    normalize = effects["gcd_welyam_normalize_tier2_effect"]
    assert {n.value for n in normalize.walk() if n.key == "remove_government_reform"} == second_tier - {"empower_magnate_council"}
    for chosen in second_tier:
        model = Model(effects, triggers)
        other_tiers = {"feudalism_reform", "expanded_royal_court_reform"}
        assert not other_tiers & second_tier
        model.reforms = other_tiers | {chosen}
        model.execute(normalize)
        assert model.reforms == other_tiers | {"empower_magnate_council"}, chosen
        if chosen == "empower_magnate_council":
            assert not model.operations

    trigger = missions["a13_5_2"].children("trigger")[0]
    assert not any(n.key == "government_rank" for n in trigger.walk())
    for level, allowed in ((1, False), (2, True), (5, True)):
        model = Model(effects, triggers)
        model.level = level
        assert model.condition(trigger) == allowed
    # 日志指出的无效指令不能复发，议会改革点数仍是 25。
    assert not any(n.key == "add_reform_progress" for event in events.values() for n in event.walk())
    assert any(n.key == "change_government_reform_progress" and n.value == "25"
               for n in events["gcd_welyam.10"].walk())
