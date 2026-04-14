"""采集源注册表 — 三层配置：代码定义 → YAML 覆盖 → 数据库热配"""

import os
import yaml
from typing import List, Dict, Any, Optional

from ..models import SourceConfig


class SourceRegistry:
    """采集源注册表"""

    def __init__(self, yaml_path: Optional[str] = None):
        """
        初始化注册表

        Args:
            yaml_path: YAML 配置文件路径（可选）
        """
        self.yaml_path = yaml_path
        self._sources: Dict[str, SourceConfig] = {}
        self._load_default_sources()
        if yaml_path and os.path.exists(yaml_path):
            self._load_yaml_sources()

    def _load_default_sources(self):
        """加载代码定义的默认源"""
        # 这里只定义骨架，实际源在 YAML 中配置
        pass

    def _load_yaml_sources(self):
        """从 YAML 加载源配置"""
        with open(self.yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            sources = data.get("sources", [])
            for src in sources:
                config = SourceConfig(**src)
                self._sources[config.source_id] = config

    def get_source(self, source_id: str) -> Optional[SourceConfig]:
        """获取单个采集源"""
        return self._sources.get(source_id)

    def get_all_sources(self) -> List[SourceConfig]:
        """获取所有采集源"""
        return list(self._sources.values())

    def get_active_sources(self, segment: Optional[str] = None) -> List[SourceConfig]:
        """
        获取活跃采集源

        Args:
            segment: 时段过滤（盘前/午间/盘后/夜盘），None 表示不过滤

        Returns:
            活跃源列表
        """
        sources = [src for src in self._sources.values() if src.enabled]

        if segment:
            sources = [src for src in sources if segment in src.schedule]

        # 按优先级排序（高优先级在前）
        sources.sort(key=lambda x: x.priority, reverse=True)

        return sources

    def add_source(self, config: SourceConfig):
        """添加采集源"""
        self._sources[config.source_id] = config

    def update_source(self, source_id: str, updates: Dict[str, Any]):
        """更新采集源配置"""
        if source_id in self._sources:
            current = self._sources[source_id]
            updated_data = current.dict()
            updated_data.update(updates)
            self._sources[source_id] = SourceConfig(**updated_data)

    def remove_source(self, source_id: str):
        """删除采集源"""
        if source_id in self._sources:
            del self._sources[source_id]

    def reload_from_yaml(self):
        """重新从 YAML 加载"""
        self._sources.clear()
        self._load_default_sources()
        if self.yaml_path and os.path.exists(self.yaml_path):
            self._load_yaml_sources()
