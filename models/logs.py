"""日志相关数据模型 - 重定向到 hot_aggr_models.py"""

# 此文件已废弃，所有日志相关模型已迁移到 models/hot_aggr_models.py
# 为了保持向后兼容性，这里提供重定向导入

from .hot_aggr_models import HotAggrProcessingLog

# 向后兼容的别名
ProcessingLog = HotAggrProcessingLog

__all__ = ['ProcessingLog', 'HotAggrProcessingLog']