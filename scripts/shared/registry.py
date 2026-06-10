#!/usr/bin/env python3
"""模块注册表：所有模块在此注册，编排器从中推导上下游依赖。"""

from __future__ import annotations
from typing import Dict, List, Optional
from scripts.shared.contract import ModuleContract


class ModuleRegistry:
    """模块注册表

    所有模块在 __init__.py 中通过 register() 注册到这里。
    编排器通过 get_downstream() / get_upstream() 推导依赖关系，
    不再需要硬编码 next_states。
    """

    def __init__(self):
        self._modules: Dict[str, ModuleContract] = {}

    def register(self, contract: ModuleContract):
        """注册一个模块"""
        if contract.name in self._modules:
            raise ValueError(f"模块 '{contract.name}' 已注册")
        self._modules[contract.name] = contract

    def get(self, name: str) -> Optional[ModuleContract]:
        """按名称获取模块契约"""
        return self._modules.get(name)

    @property
    def all(self) -> Dict[str, ModuleContract]:
        """获取所有模块"""
        return dict(self._modules)

    def get_downstream(self, module_name: str) -> List[str]:
        """返回消费此模块产出的所有下游模块"""
        contract = self._modules.get(module_name)
        if not contract:
            return []
        provides_keys = set(contract.provides.keys())
        downstream = []
        for name, other in self._modules.items():
            if name == module_name:
                continue
            for key in other.consumes:
                if key in provides_keys:
                    downstream.append(name)
                    break
        return downstream

    def get_upstream(self, module_name: str) -> List[str]:
        """返回此模块依赖的所有上游模块"""
        contract = self._modules.get(module_name)
        if not contract:
            return []
        providers = set()
        for key, spec in contract.consumes.items():
            for name, other in self._modules.items():
                if name == module_name:
                    continue
                if key in other.provides:
                    providers.add(name)
        return sorted(providers)

    def get_stage_order(self) -> List[str]:
        """拓扑排序：按依赖关系返回模块执行顺序"""
        # 简单的层次排序：没有上游的排前面
        ordered = []
        remaining = set(self._modules.keys())

        while remaining:
            # 找到所有上游都已排序的模块
            batch = set()
            for name in remaining:
                deps = set(self.get_upstream(name))
                if not deps.intersection(remaining):
                    batch.add(name)
            if not batch:
                # 有循环依赖，强制按剩余顺序
                batch = remaining.copy()
            ordered.extend(sorted(batch))
            remaining -= batch

        return ordered

    def validate_all(self) -> List[str]:
        """校验所有模块契约的一致性，返回警告列表"""
        warnings = []
        for name, contract in self._modules.items():
            for key, spec in contract.consumes.items():
                # 检查 consume 的字段是否有某个模块 provide
                found = False
                for other_name, other in self._modules.items():
                    if other_name == name:
                        continue
                    if key in other.provides:
                        found = True
                        break
                if not found and spec.required:
                    warnings.append(
                        f"模块 '{name}' 消费字段 '{key}'，但没有任何模块产出它"
                    )
        return warnings


# 全局单例
_registry: Optional[ModuleRegistry] = None


def get_registry() -> ModuleRegistry:
    global _registry
    if _registry is None:
        _registry = ModuleRegistry()
    return _registry


def reset_registry():
    """测试用：重置注册表"""
    global _registry
    _registry = None
