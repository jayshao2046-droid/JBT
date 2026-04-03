from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from datetime import date
from typing import Any, Callable, Iterator, Mapping, Optional

try:
    from ..core.settings import Settings, get_settings
except ImportError:
    from core.settings import Settings, get_settings


class BacktestSessionConfigError(RuntimeError):
    pass


@dataclass(frozen=True)
class BacktestSessionConfig:
    job_id: str
    symbol: str
    start_date: date
    end_date: date
    initial_capital: float
    auth_username: str
    auth_password: str
    account_type: str = "sim"
    backtest_mode: str = "online"


@dataclass
class TqSdkSession:
    api: Any
    account: Any
    backtest: Any
    auth: Any
    config: BacktestSessionConfig


class TqSdkSessionManager:
    def __init__(
        self,
        *,
        settings: Optional[Settings] = None,
        api_factory: Optional[Callable[..., Any]] = None,
        auth_factory: Optional[Callable[..., Any]] = None,
        backtest_factory: Optional[Callable[..., Any]] = None,
        sim_factory: Optional[Callable[..., Any]] = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._api_factory = api_factory
        self._auth_factory = auth_factory
        self._backtest_factory = backtest_factory
        self._sim_factory = sim_factory

    def build_config_from_job(self, job: Any) -> BacktestSessionConfig:
        start_date = self._read_job_value(job, "start_date")
        end_date = self._read_job_value(job, "end_date")
        initial_capital = float(self._read_job_value(job, "initial_capital"))

        if end_date < start_date:
            raise BacktestSessionConfigError(
                "backtest session end_date must be greater than or equal to start_date"
            )
        if initial_capital <= 0:
            raise BacktestSessionConfigError("initial_capital must be greater than zero")
        if self._settings.backtest_mode != "online":
            raise BacktestSessionConfigError(
                f"unsupported backtest mode {self._settings.backtest_mode}; only online is allowed"
            )
        if self._settings.tqsdk_account_type != "sim":
            raise BacktestSessionConfigError(
                f"unsupported account type {self._settings.tqsdk_account_type}; only sim is allowed"
            )
        if not self._settings.tqsdk_auth_username or not self._settings.tqsdk_auth_password:
            raise BacktestSessionConfigError(
                "TQSDK_AUTH_USERNAME and TQSDK_AUTH_PASSWORD must be configured before formal backtest execution"
            )

        return BacktestSessionConfig(
            job_id=str(self._read_job_value(job, "job_id")),
            symbol=str(self._read_job_value(job, "symbol")),
            start_date=start_date,
            end_date=end_date,
            initial_capital=initial_capital,
            auth_username=self._settings.tqsdk_auth_username,
            auth_password=self._settings.tqsdk_auth_password,
            account_type=self._settings.tqsdk_account_type,
            backtest_mode=self._settings.backtest_mode,
        )

    def create_session(self, config: BacktestSessionConfig) -> TqSdkSession:
        self._ensure_factories()
        auth = self._auth_factory(config.auth_username, config.auth_password)
        sim_account = self._sim_factory(
            init_balance=config.initial_capital,
            account_id=config.job_id,
        )
        backtest = self._backtest_factory(
            start_dt=config.start_date,
            end_dt=config.end_date,
        )
        api = self._api_factory(
            account=sim_account,
            backtest=backtest,
            auth=auth,
            disable_print=True,
        )
        return TqSdkSession(
            api=api,
            account=sim_account,
            backtest=backtest,
            auth=auth,
            config=config,
        )

    @contextmanager
    def open_session(self, config: BacktestSessionConfig) -> Iterator[TqSdkSession]:
        session = self.create_session(config)
        try:
            yield session
        finally:
            self.close_session(session)

    def close_session(self, session: TqSdkSession) -> None:
        close = getattr(session.api, "close", None)
        if callable(close):
            close()

    def _ensure_factories(self) -> None:
        if (
            self._api_factory is not None
            and self._auth_factory is not None
            and self._backtest_factory is not None
            and self._sim_factory is not None
        ):
            return
        from tqsdk import TqApi, TqAuth, TqBacktest, TqSim

        self._api_factory = self._api_factory or TqApi
        self._auth_factory = self._auth_factory or TqAuth
        self._backtest_factory = self._backtest_factory or TqBacktest
        self._sim_factory = self._sim_factory or TqSim

    def _read_job_value(self, job: Any, field_name: str) -> Any:
        if isinstance(job, Mapping):
            if field_name not in job:
                raise BacktestSessionConfigError(f"missing job field {field_name}")
            return job[field_name]
        if not hasattr(job, field_name):
            raise BacktestSessionConfigError(f"missing job field {field_name}")
        return getattr(job, field_name)