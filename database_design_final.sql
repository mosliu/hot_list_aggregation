-- 热榜聚合智能体数据库设计（最终版本）
-- 基于现有 hot_news_base 表，新增事件聚合相关表
-- 避免与现有表名冲突，使用新的表名

-- 聚合事件主表（避免与现有events表冲突）
CREATE TABLE `aggregated_events` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT COMMENT '事件主键',
  `title` varchar(255) NOT NULL COMMENT '事件标题',
  `description` text COMMENT '事件描述',
  `event_type` varchar(50) DEFAULT NULL COMMENT '事件类型：政治、经济、社会、科技等',
  `sentiment` varchar(20) DEFAULT NULL COMMENT '情感倾向：positive、negative、neutral',
  `entities` text COMMENT '实体信息JSON：人物、组织、地点等',
  `regions` text COMMENT '地域信息JSON：国家、省份、城市等',
  `keywords` text COMMENT '关键词JSON数组',
  `confidence_score` decimal(5,4) DEFAULT NULL COMMENT '聚合置信度分数',
  `news_count` int(11) DEFAULT 0 COMMENT '关联新闻数量',
  `first_news_time` datetime DEFAULT NULL COMMENT '最早新闻时间',
  `last_news_time` datetime DEFAULT NULL COMMENT '最新新闻时间',
  `status` tinyint(4) DEFAULT 1 COMMENT '状态：1-正常，2-已合并，3-已删除',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_event_type` (`event_type`),
  KEY `idx_sentiment` (`sentiment`),
  KEY `idx_status` (`status`),
  KEY `idx_created_at` (`created_at`),
  KEY `idx_first_news_time` (`first_news_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='聚合事件主表';

-- 新闻聚合事件关联表
CREATE TABLE `news_aggregated_event_relations` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT COMMENT '关联主键',
  `news_id` int(11) unsigned NOT NULL COMMENT '新闻ID，关联hot_news_base.id',
  `event_id` int(11) unsigned NOT NULL COMMENT '事件ID，关联aggregated_events.id',
  `confidence_score` decimal(5,4) DEFAULT NULL COMMENT '关联置信度分数',
  `relation_type` varchar(20) DEFAULT 'primary' COMMENT '关联类型：primary-主要，secondary-次要',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_news_event` (`news_id`, `event_id`),
  KEY `idx_news_id` (`news_id`),
  KEY `idx_event_id` (`event_id`),
  KEY `idx_confidence_score` (`confidence_score`),
  CONSTRAINT `fk_news_agg_event_news` FOREIGN KEY (`news_id`) REFERENCES `hot_news_base` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_news_agg_event_event` FOREIGN KEY (`event_id`) REFERENCES `aggregated_events` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='新闻聚合事件关联表';

-- 聚合事件标签表
CREATE TABLE `aggregated_event_labels` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT COMMENT '标签主键',
  `event_id` int(11) unsigned NOT NULL COMMENT '事件ID，关联aggregated_events.id',
  `label_type` varchar(50) NOT NULL COMMENT '标签类型：sentiment、entity、region、category等',
  `label_value` varchar(255) NOT NULL COMMENT '标签值',
  `confidence` decimal(5,4) DEFAULT NULL COMMENT '标签置信度',
  `source` varchar(50) DEFAULT 'ai' COMMENT '标签来源：ai、manual、rule',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_event_id` (`event_id`),
  KEY `idx_label_type` (`label_type`),
  KEY `idx_label_value` (`label_value`),
  KEY `idx_confidence` (`confidence`),
  CONSTRAINT `fk_agg_event_labels_event` FOREIGN KEY (`event_id`) REFERENCES `aggregated_events` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='聚合事件标签表';

-- 聚合事件历史关联表
CREATE TABLE `aggregated_event_history_relations` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT COMMENT '关联主键',
  `parent_event_id` int(11) unsigned NOT NULL COMMENT '父事件ID',
  `child_event_id` int(11) unsigned NOT NULL COMMENT '子事件ID',
  `relation_type` varchar(50) NOT NULL COMMENT '关联类型：continuation-延续，evolution-演化，merge-合并',
  `confidence_score` decimal(5,4) DEFAULT NULL COMMENT '关联置信度',
  `description` text COMMENT '关联描述',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_parent_event` (`parent_event_id`),
  KEY `idx_child_event` (`child_event_id`),
  KEY `idx_relation_type` (`relation_type`),
  CONSTRAINT `fk_agg_event_history_parent` FOREIGN KEY (`parent_event_id`) REFERENCES `aggregated_events` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_agg_event_history_child` FOREIGN KEY (`child_event_id`) REFERENCES `aggregated_events` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='聚合事件历史关联表';

-- 任务处理日志表
CREATE TABLE `task_processing_logs` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT COMMENT '日志主键',
  `task_type` varchar(50) NOT NULL COMMENT '任务类型：news_aggregation、event_labeling、history_linking',
  `task_id` varchar(100) DEFAULT NULL COMMENT '任务ID，用于追踪批次',
  `start_time` datetime NOT NULL COMMENT '开始时间',
  `end_time` datetime DEFAULT NULL COMMENT '结束时间',
  `status` varchar(20) NOT NULL COMMENT '状态：running、completed、failed、cancelled',
  `total_count` int(11) DEFAULT 0 COMMENT '总处理数量',
  `success_count` int(11) DEFAULT 0 COMMENT '成功数量',
  `failed_count` int(11) DEFAULT 0 COMMENT '失败数量',
  `error_message` text COMMENT '错误信息',
  `config_snapshot` text COMMENT '配置快照',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_task_type` (`task_type`),
  KEY `idx_task_id` (`task_id`),
  KEY `idx_status` (`status`),
  KEY `idx_start_time` (`start_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='任务处理日志表';