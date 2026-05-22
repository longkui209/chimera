"""
Chimera 错误处理与恢复模块

统一的错误分类、恢复策略、日志格式。
"""

import sys
import traceback
from enum import Enum
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime


class ErrorSeverity(Enum):
    """错误严重级别"""
    DEBUG = 0      # 调试信息
    INFO = 1       # 信息
    WARNING = 2    # 警告（可恢复）
    ERROR = 3      # 错误（部分功能受影响）
    CRITICAL = 4   # 致命（流水线中断）


class ErrorCategory(Enum):
    """错误分类"""
    FILE_NOT_FOUND = "file_not_found"
    PERMISSION_DENIED = "permission_denied"
    ENGINE_NOT_SUPPORTED = "engine_not_supported"
    EXTRACTION_FAILED = "extraction_failed"
    SKELETON_MISMATCH = "skeleton_mismatch"
    FORMAT_CONVERSION_FAILED = "format_conversion_failed"
    INJECTION_FAILED = "injection_failed"
    VALIDATION_FAILED = "validation_failed"
    DAG_TIMEOUT = "dag_timeout"
    DAG_CIRCULAR = "dag_circular"
    NETWORK_ERROR = "network_error"
    AI_MODEL_ERROR = "ai_model_error"
    CONFIG_ERROR = "config_error"
    UNKNOWN = "unknown"


@dataclass
class ChimeraError:
    """Chimera 统一错误"""
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    agent: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    traceback: Optional[str] = None
    recovery_hint: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category.value,
            "severity": self.severity.name,
            "message": self.message,
            "agent": self.agent,
            "details": self.details,
            "recovery_hint": self.recovery_hint,
            "timestamp": self.timestamp,
        }


class ErrorHandler:
    """
    Chimera 错误处理器

    提供：
    - 统一的错误捕获和分类
    - 自动恢复策略建议
    - 流水线熔断决策
    """

    # 恢复策略映射
    RECOVERY_STRATEGIES: Dict[ErrorCategory, Dict[str, Any]] = {
        ErrorCategory.FILE_NOT_FOUND: {
            "action": "skip_or_retry",
            "retry_count": 1,
            "can_continue": False,
            "hint": "检查文件路径是否正确，确认游戏库已挂载",
        },
        ErrorCategory.PERMISSION_DENIED: {
            "action": "skip",
            "retry_count": 0,
            "can_continue": False,
            "hint": "检查文件权限，可能需要 sudo 或 chmod",
        },
        ErrorCategory.ENGINE_NOT_SUPPORTED: {
            "action": "skip",
            "retry_count": 0,
            "can_continue": False,
            "hint": "该引擎尚未支持，请在 config.py 注册新的 EngineProfile",
        },
        ErrorCategory.EXTRACTION_FAILED: {
            "action": "retry_with_fallback",
            "retry_count": 2,
            "can_continue": True,
            "hint": "尝试使用备用提取工具（umodel → FModel → QuickBMS）",
        },
        ErrorCategory.SKELETON_MISMATCH: {
            "action": "ai_guided_fallback",
            "retry_count": 1,
            "can_continue": True,
            "hint": "骨架不匹配，降级到 AI_GUIDED 重定向策略",
        },
        ErrorCategory.FORMAT_CONVERSION_FAILED: {
            "action": "intermediate_format",
            "retry_count": 2,
            "can_continue": True,
            "hint": "尝试通过 FBX/glTF 中间格式转换",
        },
        ErrorCategory.INJECTION_FAILED: {
            "action": "rollback_and_retry",
            "retry_count": 1,
            "can_continue": False,
            "hint": "注入失败，自动回滚后重试",
        },
        ErrorCategory.VALIDATION_FAILED: {
            "action": "warn_and_continue",
            "retry_count": 0,
            "can_continue": True,
            "hint": "验证未通过但迁移可能仍可用，建议人工复核",
        },
        ErrorCategory.DAG_TIMEOUT: {
            "action": "retry_with_backoff",
            "retry_count": 3,
            "can_continue": True,
            "hint": "Agent 超时，增加 DAG_TIMEOUT 或检查资源",
        },
        ErrorCategory.DAG_CIRCULAR: {
            "action": "abort",
            "retry_count": 0,
            "can_continue": False,
            "hint": "DAG 存在循环依赖，检查 depends_on 配置",
        },
        ErrorCategory.AI_MODEL_ERROR: {
            "action": "retry_with_fallback",
            "retry_count": 2,
            "can_continue": True,
            "hint": "AI 模型错误，尝试切换备用模型",
        },
        ErrorCategory.CONFIG_ERROR: {
            "action": "abort",
            "retry_count": 0,
            "can_continue": False,
            "hint": "配置错误，检查 config.py 和环境变量",
        },
    }

    @classmethod
    def classify(cls, exception: Exception, agent: str = None) -> ChimeraError:
        """自动分类异常"""
        exc_type = type(exception).__name__
        exc_msg = str(exception)

        # 文件错误
        if isinstance(exception, FileNotFoundError):
            return ChimeraError(
                category=ErrorCategory.FILE_NOT_FOUND,
                severity=ErrorSeverity.ERROR,
                message=exc_msg,
                agent=agent,
                traceback=traceback.format_exc(),
                recovery_hint=cls.RECOVERY_STRATEGIES[ErrorCategory.FILE_NOT_FOUND]["hint"],
            )

        # 权限错误
        if isinstance(exception, PermissionError):
            return ChimeraError(
                category=ErrorCategory.PERMISSION_DENIED,
                severity=ErrorSeverity.ERROR,
                message=exc_msg,
                agent=agent,
                traceback=traceback.format_exc(),
                recovery_hint=cls.RECOVERY_STRATEGIES[ErrorCategory.PERMISSION_DENIED]["hint"],
            )

        # 超时
        if "timeout" in exc_msg.lower() or isinstance(exception, TimeoutError):
            return ChimeraError(
                category=ErrorCategory.DAG_TIMEOUT,
                severity=ErrorSeverity.WARNING,
                message=exc_msg,
                agent=agent,
                recovery_hint=cls.RECOVERY_STRATEGIES[ErrorCategory.DAG_TIMEOUT]["hint"],
            )

        # 网络错误
        if any(kw in exc_msg.lower() for kw in ["connection", "network", "http", "socket"]):
            return ChimeraError(
                category=ErrorCategory.NETWORK_ERROR,
                severity=ErrorSeverity.WARNING,
                message=exc_msg,
                agent=agent,
                recovery_hint="检查网络连接和 API 端点",
            )

        # 通用
        return ChimeraError(
            category=ErrorCategory.UNKNOWN,
            severity=ErrorSeverity.ERROR,
            message=exc_msg,
            agent=agent,
            traceback=traceback.format_exc(),
            details={"exception_type": exc_type},
        )

    @classmethod
    def get_recovery_strategy(cls, category: ErrorCategory) -> Optional[Dict]:
        """获取恢复策略"""
        return cls.RECOVERY_STRATEGIES.get(category)

    @classmethod
    def should_abort(cls, error: ChimeraError) -> bool:
        """判断是否应该中止流水线"""
        if error.severity == ErrorSeverity.CRITICAL:
            return True
        strategy = cls.RECOVERY_STRATEGIES.get(error.category, {})
        return not strategy.get("can_continue", False)


class SafeExecutor:
    """
    安全执行器

    包装任何函数调用，自动捕获异常并分类。
    """

    def __init__(self, agent_name: str = "unknown"):
        self.agent_name = agent_name
        self.errors: list[ChimeraError] = []

    def execute(self, fn: Callable, *args, **kwargs) -> tuple:
        """
        安全执行函数

        Returns:
            (result, error): 成功时 error 为 None
        """
        try:
            result = fn(*args, **kwargs)
            return result, None
        except Exception as e:
            error = ErrorHandler.classify(e, self.agent_name)
            self.errors.append(error)
            return None, error

    def has_errors(self) -> bool:
        return len(self.errors) > 0

    def has_critical(self) -> bool:
        return any(
            ErrorHandler.should_abort(e) for e in self.errors
        )

    def summary(self) -> Dict[str, Any]:
        return {
            "agent": self.agent_name,
            "total_errors": len(self.errors),
            "critical": sum(1 for e in self.errors if ErrorHandler.should_abort(e)),
            "errors": [e.to_dict() for e in self.errors],
        }
