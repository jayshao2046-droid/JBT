"""EmailImporter 单元测试 — TASK-0063 CF2"""
from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock

from services.decision.src.publish.email_importer import EmailImporter


# ── fixtures ───────────────────────────────────────────────────
VALID_YAML = """
name: test_strategy
symbol: rb2510
exchange: SHFE
direction: long
""".strip()

INVALID_YAML = "name: \n  bad: [unterminated"

MISSING_FIELDS_YAML = """
foo: bar
""".strip()


def _mock_import_success(data, *, repo=None):
    return {
        "strategy_id": "strat-abc123",
        "status": "imported",
        "message": "策略导入成功",
        "validation_errors": [],
        "strategy_data": data,
    }


def _mock_import_validation_failed(data, *, repo=None):
    return {
        "strategy_id": None,
        "status": "validation_failed",
        "message": "策略验证未通过",
        "validation_errors": ["缺少必填字段: name"],
        "strategy_data": None,
    }


# ── _extract_yaml_blocks ──────────────────────────────────────
class TestExtractYamlBlocks:
    def test_single_block(self):
        text = "hello\n```yaml\nname: a\n```\nbye"
        blocks = EmailImporter._extract_yaml_blocks(text)
        assert len(blocks) == 1
        assert "name: a" in blocks[0]

    def test_multiple_blocks(self):
        text = "```yaml\nblock1\n```\ntext\n```yaml\nblock2\n```"
        blocks = EmailImporter._extract_yaml_blocks(text)
        assert len(blocks) == 2

    def test_no_blocks(self):
        blocks = EmailImporter._extract_yaml_blocks("no yaml here")
        assert blocks == []

    def test_case_insensitive(self):
        text = "```YAML\nname: test\n```"
        blocks = EmailImporter._extract_yaml_blocks(text)
        assert len(blocks) == 1


# ── import_from_email ─────────────────────────────────────────
class TestImportFromEmail:
    @patch(
        "services.decision.src.publish.email_importer.import_strategy",
        side_effect=_mock_import_success,
    )
    @patch(
        "services.decision.src.publish.email_importer.get_import_repository",
        return_value=MagicMock(),
    )
    def test_single_yaml_success(self, _repo, _imp):
        imp = EmailImporter()
        body = f"请导入策略：\n```yaml\n{VALID_YAML}\n```\n谢谢"
        result = imp.import_from_email("策略导入", body, "user@test.com")
        assert result.status == "success"
        assert result.channel == "email"
        assert len(result.strategy_ids) == 1
        assert result.raw_yaml_count == 1
        assert result.errors == []

    @patch(
        "services.decision.src.publish.email_importer.import_strategy",
        side_effect=_mock_import_success,
    )
    @patch(
        "services.decision.src.publish.email_importer.get_import_repository",
        return_value=MagicMock(),
    )
    def test_multiple_yaml_blocks(self, _repo, _imp):
        imp = EmailImporter()
        body = f"```yaml\n{VALID_YAML}\n```\n中间文字\n```yaml\n{VALID_YAML}\n```"
        result = imp.import_from_email("批量导入", body, "user@test.com")
        assert result.status == "success"
        assert len(result.strategy_ids) == 2
        assert result.raw_yaml_count == 2

    def test_empty_body_no_yaml(self):
        imp = EmailImporter()
        result = imp.import_from_email("空邮件", "没有YAML", "x@y.com")
        assert result.status == "failed"
        assert result.raw_yaml_count == 0
        assert "未找到 YAML 代码块" in result.errors[0]

    @patch(
        "services.decision.src.publish.email_importer.import_strategy",
        side_effect=_mock_import_validation_failed,
    )
    @patch(
        "services.decision.src.publish.email_importer.get_import_repository",
        return_value=MagicMock(),
    )
    def test_invalid_yaml_in_email(self, _repo, _imp):
        imp = EmailImporter()
        body = f"```yaml\n{MISSING_FIELDS_YAML}\n```"
        result = imp.import_from_email("坏策略", body, "x@y.com")
        assert result.status == "failed"
        assert len(result.errors) == 1

    @patch(
        "services.decision.src.publish.email_importer.import_strategy",
    )
    @patch(
        "services.decision.src.publish.email_importer.get_import_repository",
        return_value=MagicMock(),
    )
    def test_partial_success(self, _repo, mock_import):
        mock_import.side_effect = [
            _mock_import_success({}),
            _mock_import_validation_failed({}),
        ]
        imp = EmailImporter()
        body = f"```yaml\n{VALID_YAML}\n```\n```yaml\n{MISSING_FIELDS_YAML}\n```"
        result = imp.import_from_email("混合", body, "x@y.com")
        assert result.status == "partial"
        assert len(result.strategy_ids) == 1
        assert len(result.errors) == 1


# ── import_from_dashboard ─────────────────────────────────────
class TestImportFromDashboard:
    @patch(
        "services.decision.src.publish.email_importer.import_strategy",
        side_effect=_mock_import_success,
    )
    @patch(
        "services.decision.src.publish.email_importer.get_import_repository",
        return_value=MagicMock(),
    )
    def test_dashboard_success(self, _repo, _imp):
        imp = EmailImporter()
        result = imp.import_from_dashboard(VALID_YAML)
        assert result.status == "success"
        assert result.channel == "dashboard"
        assert len(result.strategy_ids) == 1

    def test_dashboard_empty_content(self):
        imp = EmailImporter()
        result = imp.import_from_dashboard("")
        assert result.status == "failed"
        assert "YAML 内容为空" in result.errors[0]

    def test_dashboard_whitespace_only(self):
        imp = EmailImporter()
        result = imp.import_from_dashboard("   \n  ")
        assert result.status == "failed"


# ── get / list history ────────────────────────────────────────
class TestHistory:
    def test_get_result_found(self):
        imp = EmailImporter()
        r = imp.import_from_email("x", "no yaml", "a@b.com")
        assert imp.get_result(r.import_id) is r

    def test_get_result_not_found(self):
        imp = EmailImporter()
        assert imp.get_result("nonexistent") is None

    @patch(
        "services.decision.src.publish.email_importer.import_strategy",
        side_effect=_mock_import_success,
    )
    @patch(
        "services.decision.src.publish.email_importer.get_import_repository",
        return_value=MagicMock(),
    )
    def test_list_all_and_filter(self, _repo, _imp):
        imp = EmailImporter()
        imp.import_from_email("e", f"```yaml\n{VALID_YAML}\n```", "a@b.com")
        imp.import_from_dashboard(VALID_YAML)

        all_results = imp.list_results()
        assert len(all_results) == 2

        email_only = imp.list_results(channel="email")
        assert len(email_only) == 1
        assert email_only[0].channel == "email"

        dash_only = imp.list_results(channel="dashboard")
        assert len(dash_only) == 1
        assert dash_only[0].channel == "dashboard"
