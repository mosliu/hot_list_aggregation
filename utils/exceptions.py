"""自定义异常类"""


class HotListAggregationError(Exception):
    """热榜聚合系统基础异常类"""
    
    def __init__(self, message: str, error_code: str = None, details: dict = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)
    
    def __str__(self) -> str:
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message


class DatabaseError(HotListAggregationError):
    """数据库相关错误"""
    
    def __init__(self, message: str, query: str = None, params: dict = None):
        super().__init__(
            message=message,
            error_code="DB_ERROR",
            details={"query": query, "params": params}
        )


class AIServiceError(HotListAggregationError):
    """AI服务相关错误"""
    
    def __init__(self, message: str, model: str = None, api_response: dict = None):
        super().__init__(
            message=message,
            error_code="AI_ERROR",
            details={"model": model, "api_response": api_response}
        )


class ConfigurationError(HotListAggregationError):
    """配置相关错误"""
    
    def __init__(self, message: str, config_key: str = None):
        super().__init__(
            message=message,
            error_code="CONFIG_ERROR",
            details={"config_key": config_key}
        )


class ProcessingError(HotListAggregationError):
    """处理过程相关错误"""
    
    def __init__(self, message: str, stage: str = None, item_id: str = None):
        super().__init__(
            message=message,
            error_code="PROCESSING_ERROR",
            details={"stage": stage, "item_id": item_id}
        )


class ValidationError(HotListAggregationError):
    """数据验证错误"""
    
    def __init__(self, message: str, field: str = None, value: str = None):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            details={"field": field, "value": value}
        )


class ExternalAPIError(HotListAggregationError):
    """外部API调用错误"""
    
    def __init__(self, message: str, api_name: str = None, status_code: int = None):
        super().__init__(
            message=message,
            error_code="EXTERNAL_API_ERROR",
            details={"api_name": api_name, "status_code": status_code}
        )


class RateLimitError(HotListAggregationError):
    """API限流错误"""
    
    def __init__(self, message: str, retry_after: int = None):
        super().__init__(
            message=message,
            error_code="RATE_LIMIT_ERROR",
            details={"retry_after": retry_after}
        )


class SchedulerError(HotListAggregationError):
    """任务调度错误"""
    
    def __init__(self, message: str, job_id: str = None, scheduler_name: str = None):
        super().__init__(
            message=message,
            error_code="SCHEDULER_ERROR",
            details={"job_id": job_id, "scheduler_name": scheduler_name}
        )


class TaskExecutionError(HotListAggregationError):
    """任务执行错误"""
    
    def __init__(self, message: str, task_name: str = None, task_id: str = None):
        super().__init__(
            message=message,
            error_code="TASK_EXECUTION_ERROR",
            details={"task_name": task_name, "task_id": task_id}
        )


# 为了兼容性，添加一些别名
ServiceError = HotListAggregationError
DataValidationError = ValidationError