from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # 基础服务
    decision_host: str = "0.0.0.0"
    decision_port: int = 8104
    decision_workers: int = 2
    decision_log_level: str = "info"
    decision_env: str = "development"

    # 研究窗口
    research_window_start: str = "09:00"
    research_window_end: str = "15:30"
    research_timezone: str = "Asia/Shanghai"

    # 执行门禁
    execution_gate_enabled: bool = True
    execution_gate_target: str = "sim-trading"
    live_trading_gate_locked: bool = True

    # 模型路由门禁
    model_router_require_backtest_cert: bool = True
    model_router_require_research_snapshot: bool = True

    # 服务集成
    backtest_service_url: str = "http://localhost:8103"
    sim_trading_url: str = "http://localhost:8101"
    data_service_url: str = "http://localhost:8105"
    data_service_timeout: int = 30
    decision_state_file: str = "./runtime/decision-state.json"

    @property
    def resolved_decision_state_file(self) -> Path:
        raw_path = Path(self.decision_state_file)
        if raw_path.is_absolute():
            return raw_path
        return (Path(__file__).resolve().parents[2] / raw_path).resolve()


def get_settings() -> Settings:
    return Settings()
