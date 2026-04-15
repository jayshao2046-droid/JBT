"""配置更新器 - 动态更新研究员配置

职责：
1. 更新数据源配置
2. 更新采集频率
3. 更新品种列表
"""
import logging
import yaml
from pathlib import Path
from typing import Dict, List

logger = logging.getLogger(__name__)


class ConfigUpdater:
    """配置更新器"""

    def __init__(self, config_path: str = "/Users/jayshao/JBT/services/data/configs/researcher_sources.yaml"):
        self.config_path = config_path

    def update_source_enabled(self, source_name: str, enabled: bool) -> bool:
        """更新数据源开关状态"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            # 更新配置
            for source in config.get('news_sources', []):
                if source['name'] == source_name:
                    source['enabled'] = enabled
                    break

            # 保存配置
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, allow_unicode=True)

            logger.info(f"Updated source {source_name}: enabled={enabled}")
            return True

        except Exception as e:
            logger.error(f"Error updating config: {e}")
            return False

    def update_source_interval(self, source_name: str, interval: int) -> bool:
        """更新数据源采集频率"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            # 更新配置
            for source in config.get('news_sources', []):
                if source['name'] == source_name:
                    source['interval'] = interval
                    break

            # 保存配置
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, allow_unicode=True)

            logger.info(f"Updated source {source_name}: interval={interval}")
            return True

        except Exception as e:
            logger.error(f"Error updating config: {e}")
            return False

    def add_source(self, source: Dict) -> bool:
        """添加新数据源"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            if 'news_sources' not in config:
                config['news_sources'] = []

            config['news_sources'].append(source)

            # 保存配置
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, allow_unicode=True)

            logger.info(f"Added source: {source['name']}")
            return True

        except Exception as e:
            logger.error(f"Error adding source: {e}")
            return False

    def remove_source(self, source_name: str) -> bool:
        """删除数据源"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            # 删除数据源
            config['news_sources'] = [
                s for s in config.get('news_sources', [])
                if s['name'] != source_name
            ]

            # 保存配置
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, allow_unicode=True)

            logger.info(f"Removed source: {source_name}")
            return True

        except Exception as e:
            logger.error(f"Error removing source: {e}")
            return False
