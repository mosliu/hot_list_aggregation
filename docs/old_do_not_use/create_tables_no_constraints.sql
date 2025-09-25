-- 热点新闻聚合系统数据库表结构（无外键约束版本）
-- 创建时间: 2024-01-24
-- 说明: 去除外键约束，提高插入性能，通过应用层维护数据一致性

-- 设置字符集
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ============================================================================
-- 新闻基础表 (hot_news_base)
-- 存储从各个平台抓取的原始新闻数据
-- ============================================================================
CREATE TABLE IF NOT EXISTS `hot_news_base` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `title` varchar(500) NOT NULL DEFAULT '' COMMENT '新闻标题',
  `content` text COMMENT '新闻内容',
  `summary` varchar(1000) DEFAULT '' COMMENT '新闻摘要',
  `url` varchar(1000) DEFAULT '' COMMENT '新闻链接',
  `source` varchar(100) DEFAULT '' COMMENT '新闻来源',
  `author` varchar(100) DEFAULT '' COMMENT '作者',
  `type` varchar(50) DEFAULT '' COMMENT '新闻类型',
  `category` varchar(50) DEFAULT '' COMMENT '新闻分类',
  `tags` varchar(500) DEFAULT '' COMMENT '标签，逗号分隔',
  `hot_score` decimal(10,2) DEFAULT '0.00' COMMENT '热度分数',
  `view_count` bigint DEFAULT '0' COMMENT '浏览量',
  `comment_count` bigint DEFAULT '0' COMMENT '评论数',
  `like_count` bigint DEFAULT '0' COMMENT '点赞数',
  `share_count` bigint DEFAULT '0' COMMENT '分享数',
  `publish_time` datetime DEFAULT NULL COMMENT '发布时间',
  `add_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '添加时间',
  `update_time` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `status` tinyint DEFAULT '1' COMMENT '状态：0-删除，1-正常，2-待审核',
  `processed` tinyint DEFAULT '0' COMMENT '是否已处理：0-未处理，1-已处理',
  `event_id` bigint DEFAULT NULL COMMENT '关联的事件ID（软关联）',
  `platform` varchar(50) DEFAULT '' COMMENT '来源平台',
  `platform_id` varchar(100) DEFAULT '' COMMENT '平台内ID',
  `language` varchar(10) DEFAULT 'zh' COMMENT '语言',
  `region` varchar(100) DEFAULT '' COMMENT '地域标签',
  `keywords` varchar(500) DEFAULT '' COMMENT '关键词，逗号分隔',
  `sentiment` varchar(20) DEFAULT '' COMMENT '情感倾向：positive/negative/neutral',
  `confidence` decimal(5,4) DEFAULT '0.0000' COMMENT '置信度',
  PRIMARY KEY (`id`),
  KEY `idx_add_time` (`add_time`),
  KEY `idx_type` (`type`),
  KEY `idx_source` (`source`),
  KEY `idx_status` (`status`),
  KEY `idx_processed` (`processed`),
  KEY `idx_event_id` (`event_id`),
  KEY `idx_platform` (`platform`),
  KEY `idx_publish_time` (`publish_time`),
  KEY `idx_hot_score` (`hot_score`),
  KEY `idx_region` (`region`),
  KEY `idx_title` (`title`(100))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='新闻基础表';

-- ============================================================================
-- 事件表 (events)
-- 存储聚合后的事件信息
-- ============================================================================
CREATE TABLE IF NOT EXISTS `events` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `title` varchar(500) NOT NULL DEFAULT '' COMMENT '事件标题',
  `summary` text COMMENT '事件摘要',
  `description` text COMMENT '事件详细描述',
  `event_type` varchar(50) DEFAULT '' COMMENT '事件类型：政治/经济/社会/科技/体育/娱乐/自然灾害/事故/国际/其他',
  `category` varchar(50) DEFAULT '' COMMENT '事件分类',
  `tags` varchar(500) DEFAULT '' COMMENT '标签，逗号分隔',
  `keywords` varchar(500) DEFAULT '' COMMENT '关键词，逗号分隔',
  `region` varchar(100) DEFAULT '' COMMENT '地域标签',
  `location` varchar(200) DEFAULT '' COMMENT '具体地点',
  `start_time` datetime DEFAULT NULL COMMENT '事件开始时间',
  `end_time` datetime DEFAULT NULL COMMENT '事件结束时间',
  `priority` varchar(20) DEFAULT 'medium' COMMENT '优先级：low/medium/high/urgent',
  `status` varchar(20) DEFAULT 'active' COMMENT '状态：active/closed/merged/deleted',
  `confidence` decimal(5,4) DEFAULT '0.0000' COMMENT '聚合置信度',
  `hot_score` decimal(10,2) DEFAULT '0.00' COMMENT '热度分数',
  `view_count` bigint DEFAULT '0' COMMENT '浏览量',
  `news_count` int DEFAULT '0' COMMENT '关联新闻数量',
  `sentiment` varchar(20) DEFAULT '' COMMENT '整体情感倾向',
  `impact_level` varchar(20) DEFAULT '' COMMENT '影响级别：local/regional/national/international',
  `source_diversity` int DEFAULT '0' COMMENT '来源多样性（不同来源数量）',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `created_by` varchar(100) DEFAULT 'system' COMMENT '创建者',
  `updated_by` varchar(100) DEFAULT 'system' COMMENT '更新者',
  `merged_from` varchar(500) DEFAULT '' COMMENT '合并来源事件ID，逗号分隔',
  `merged_to` bigint DEFAULT NULL COMMENT '合并到的目标事件ID',
  `auto_generated` tinyint DEFAULT '1' COMMENT '是否自动生成：0-人工创建，1-自动生成',
  `reviewed` tinyint DEFAULT '0' COMMENT '是否已审核：0-未审核，1-已审核',
  `reviewer` varchar(100) DEFAULT '' COMMENT '审核人',
  `review_time` datetime DEFAULT NULL COMMENT '审核时间',
  `review_notes` text COMMENT '审核备注',
  PRIMARY KEY (`id`),
  KEY `idx_event_type` (`event_type`),
  KEY `idx_region` (`region`),
  KEY `idx_priority` (`priority`),
  KEY `idx_status` (`status`),
  KEY `idx_created_at` (`created_at`),
  KEY `idx_updated_at` (`updated_at`),
  KEY `idx_hot_score` (`hot_score`),
  KEY `idx_start_time` (`start_time`),
  KEY `idx_confidence` (`confidence`),
  KEY `idx_auto_generated` (`auto_generated`),
  KEY `idx_reviewed` (`reviewed`),
  KEY `idx_merged_to` (`merged_to`),
  KEY `idx_title` (`title`(100))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='事件表';

-- ============================================================================
-- 新闻事件关联表 (news_event_relations)
-- 存储新闻与事件的多对多关联关系
-- ============================================================================
CREATE TABLE IF NOT EXISTS `news_event_relations` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `news_id` bigint NOT NULL COMMENT '新闻ID',
  `event_id` bigint NOT NULL COMMENT '事件ID',
  `relation_type` varchar(20) DEFAULT 'primary' COMMENT '关联类型：primary-主要关联，secondary-次要关联，reference-引用关联',
  `confidence` decimal(5,4) DEFAULT '0.0000' COMMENT '关联置信度',
  `weight` decimal(5,4) DEFAULT '1.0000' COMMENT '权重',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `created_by` varchar(100) DEFAULT 'system' COMMENT '创建者',
  `notes` varchar(500) DEFAULT '' COMMENT '关联备注',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_news_event` (`news_id`, `event_id`),
  KEY `idx_news_id` (`news_id`),
  KEY `idx_event_id` (`event_id`),
  KEY `idx_relation_type` (`relation_type`),
  KEY `idx_confidence` (`confidence`),
  KEY `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='新闻事件关联表';

-- ============================================================================
-- 事件合并历史表 (event_merge_history)
-- 记录事件合并的历史操作
-- ============================================================================
CREATE TABLE IF NOT EXISTS `event_merge_history` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `source_event_ids` varchar(500) NOT NULL COMMENT '源事件ID列表，逗号分隔',
  `target_event_id` bigint NOT NULL COMMENT '目标事件ID',
  `merge_type` varchar(20) DEFAULT 'manual' COMMENT '合并类型：manual-手动，auto-自动',
  `merge_reason` text COMMENT '合并原因',
  `confidence` decimal(5,4) DEFAULT '0.0000' COMMENT '合并置信度',
  `operator` varchar(100) DEFAULT 'system' COMMENT '操作人',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `rollback_data` json COMMENT '回滚数据（JSON格式）',
  `status` varchar(20) DEFAULT 'completed' COMMENT '状态：completed-已完成，rollback-已回滚',
  PRIMARY KEY (`id`),
  KEY `idx_target_event_id` (`target_event_id`),
  KEY `idx_merge_type` (`merge_type`),
  KEY `idx_created_at` (`created_at`),
  KEY `idx_operator` (`operator`),
  KEY `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='事件合并历史表';

-- ============================================================================
-- 处理日志表 (processing_logs)
-- 记录系统处理过程的日志
-- ============================================================================
CREATE TABLE IF NOT EXISTS `processing_logs` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `process_type` varchar(50) NOT NULL COMMENT '处理类型：news_aggregation/event_merge/manual_review等',
  `batch_id` varchar(100) DEFAULT '' COMMENT '批次ID',
  `input_count` int DEFAULT '0' COMMENT '输入数量',
  `success_count` int DEFAULT '0' COMMENT '成功数量',
  `failed_count` int DEFAULT '0' COMMENT '失败数量',
  `duration` decimal(10,3) DEFAULT '0.000' COMMENT '处理时长（秒）',
  `start_time` datetime DEFAULT NULL COMMENT '开始时间',
  `end_time` datetime DEFAULT NULL COMMENT '结束时间',
  `status` varchar(20) DEFAULT 'running' COMMENT '状态：running/completed/failed/cancelled',
  `error_message` text COMMENT '错误信息',
  `parameters` json COMMENT '处理参数（JSON格式）',
  `result_summary` json COMMENT '结果摘要（JSON格式）',
  `operator` varchar(100) DEFAULT 'system' COMMENT '操作人',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_process_type` (`process_type`),
  KEY `idx_batch_id` (`batch_id`),
  KEY `idx_status` (`status`),
  KEY `idx_start_time` (`start_time`),
  KEY `idx_created_at` (`created_at`),
  KEY `idx_operator` (`operator`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='处理日志表';

-- ============================================================================
-- 系统配置表 (system_configs)
-- 存储系统配置信息
-- ============================================================================
CREATE TABLE IF NOT EXISTS `system_configs` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `config_key` varchar(100) NOT NULL COMMENT '配置键',
  `config_value` text COMMENT '配置值',
  `config_type` varchar(20) DEFAULT 'string' COMMENT '配置类型：string/int/float/bool/json',
  `description` varchar(500) DEFAULT '' COMMENT '配置描述',
  `category` varchar(50) DEFAULT 'general' COMMENT '配置分类',
  `is_active` tinyint DEFAULT '1' COMMENT '是否启用',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `updated_by` varchar(100) DEFAULT 'system' COMMENT '更新者',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_config_key` (`config_key`),
  KEY `idx_category` (`category`),
  KEY `idx_is_active` (`is_active`),
  KEY `idx_updated_at` (`updated_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='系统配置表';

-- ============================================================================
-- 插入默认配置数据
-- ============================================================================
INSERT INTO `system_configs` (`config_key`, `config_value`, `config_type`, `description`, `category`) VALUES
('llm_batch_size', '10', 'int', '大模型批处理大小', 'llm'),
('llm_max_concurrent', '3', 'int', '大模型最大并发数', 'llm'),
('recent_events_count', '50', 'int', '获取最近事件数量', 'aggregation'),
('event_summary_days', '7', 'int', '事件摘要天数范围', 'aggregation'),
('aggregation_confidence_threshold', '0.7', 'float', '聚合置信度阈值', 'aggregation'),
('auto_merge_enabled', 'false', 'bool', '是否启用自动合并', 'merge'),
('auto_merge_threshold', '0.85', 'float', '自动合并置信度阈值', 'merge'),
('cache_ttl', '3600', 'int', '缓存过期时间（秒）', 'cache'),
('max_news_per_event', '100', 'int', '每个事件最大新闻数', 'aggregation'),
('min_news_for_event', '2', 'int', '创建事件最少新闻数', 'aggregation')
ON DUPLICATE KEY UPDATE 
  `config_value` = VALUES(`config_value`),
  `updated_at` = CURRENT_TIMESTAMP;

-- 恢复外键检查
SET FOREIGN_KEY_CHECKS = 1;

-- 创建完成提示
SELECT 'Database tables created successfully without foreign key constraints!' as message;