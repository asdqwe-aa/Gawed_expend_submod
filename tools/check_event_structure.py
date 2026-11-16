"""检查自有 EU4 事件的必要选项和 immediate 调用环；不执行游戏。"""
from __future__ import annotations

from pdx_script import Node


def errors(events: Node, effects: Node) -> list[str]:
    definitions = {n.key: n for n in effects.children()}
    problems = []

    def event_calls(block: Node, stack=()):
        targets = set()
        for child in block.children():
            for node in child.walk():
                if node.key == "country_event" and isinstance(node.value, list):
                    target = node.scalar("id")
                    if target:
                        targets.add(target)
                elif node.key in definitions:
                    if node.key in stack:
                        problems.append(f"scripted effect 立即递归：{' -> '.join(stack + (node.key,))}")
                    else:
                        targets.update(event_calls(definitions[node.key], stack + (node.key,)))
        return targets

    graph = {}
    for event in events.children("country_event"):
        event_id = event.scalar("id")
        if not event.children("option"):
            problems.append(f"{event_id} 缺少必需的 option，hidden 事件也不例外")
        graph[event_id] = set()
        for block in event.children("immediate"):
            graph[event_id].update(event_calls(block))

    def visit(event_id, stack):
        if event_id in stack:
            problems.append(f"immediate 事件调用环：{' -> '.join(stack + (event_id,))}")
            return
        for target in graph.get(event_id, ()):
            if target in graph:
                visit(target, stack + (event_id,))
    for event_id in graph:
        visit(event_id, ())
    return sorted(set(problems))
