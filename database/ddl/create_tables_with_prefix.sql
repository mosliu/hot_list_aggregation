-- 热榜聚合系统数据表创建脚本
-- 所有表名添加 hot_aggr_ 前缀

-- 1. 新闻处理状态表
CREATE TABLE IF NOT EXISTS `hot_aggr_news_processing_status` (
    `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '状态主键',
    `news_id` INT NOT NULL UNIQUE COMMENT '新闻ID',
    `processing_stage` VARCHAR(50) NOT NULL DEFAULT 'pending' COMMENT '处理阶段',
    `last_processed_at` DATETIME COMMENT '最后处理时间',
    `retry_count` INT DEFAULT 0 COMMENT '重试次数',
    `error_message` TEXT COMMENT '错误信息',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    FOREIGN KEY (`news_id`) REFERENCES `hot_news_base`(`id`) ON DELETE CASCADE,
    INDEX `idx_news_id` (`news_id`),
    INDEX `idx_processing_stage` (`processing_stage`),
    INDEX `idx_last_processed_at` (`last_processed_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='新闻处理状态表';

-- 2. 事件主表
CREATE TABLE IF NOT EXISTS `hot_aggr_events` (
    `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '事件主键',
    `title` VARCHAR(255) NOT NULL COMMENT '事件标题',
    `description` TEXT COMMENT '事件描述',
    `event_type` VARCHAR(50) COMMENT '事件类型',
    `sentiment` VARCHAR(20) COMMENT '情感倾向',
    `entities` TEXT COMMENT '实体信息JSON',
    `regions` TEXT COMMENT '地域信息JSON',
    `keywords` TEXT COMMENT '关键词JSON数组',
    `confidence_score` DECIMAL(5,4) COMMENT '聚合置信度分数',
    `news_count` INT DEFAULT 0 COMMENT '关联新闻数量',
    `first_news_time` DATETIME COMMENT '最早新闻时间',
    `last_news_time` DATETIME COMMENT '最新新闻时间',
    `status` INT DEFAULT 1 COMMENT '状态：1-正常，2-已合并，3-已删除',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX `idx_title` (`title`),
    INDEX `idx_event_type` (`event_type`),
    INDEX `idx_sentiment` (`sentiment`),
    INDEX `idx_status` (`status`),
    INDEX `idx_created_at` (`created_at`),
    INDEX `idx_first_news_time` (`first_news_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='事件主表';

-- 3. 新闻事件关联表
CREATE TABLE IF NOT EXISTS `hot_aggr_news_event_relations` (
    `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '关联主键',
    `news_id` INT NOT NULL COMMENT '新闻ID',
    `event_id` INT NOT NULL COMMENT '事件ID',
    `confidence_score` DECIMAL(5,4) COMMENT '关联置信度分数',
    `relation_type` VARCHAR(20) DEFAULT 'primary' COMMENT '关联类型',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    FOREIGN KEY (`news_id`) REFERENCES `hot_news_base`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`event_id`) REFERENCES `hot_aggr_events`(`id`) ON DELETE CASCADE,
    UNIQUE KEY `uk_news_event` (`news_id`, `event_id`),
    INDEX `idx_news_id` (`news_id`),
    INDEX `idx_event_id` (`event_id`),
    INDEX `idx_relation_type` (`relation_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='新闻事件关联表';

-- 4. 事件标签表
CREATE TABLE IF NOT EXISTS `hot_aggr_event_labels` (
    `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '标签主键',
    `event_id` INT NOT NULL COMMENT '事件ID',
    `label_type` VARCHAR(50) NOT NULL COMMENT '标签类型',
    `label_value` VARCHAR(255) NOT NULL COMMENT '标签值',
    `confidence` DECIMAL(5,4) COMMENT '标签置信度',
    `source` VARCHAR(50) DEFAULT 'ai' COMMENT '标签来源',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    FOREIGN KEY (`event_id`) REFERENCES `hot_aggr_events`(`id`) ON DELETE CASCADE,
    INDEX `idx_event_id` (`event_id`),
    INDEX `idx_label_type` (`label_type`),
    INDEX `idx_label_value` (`label_value`),
    INDEX `idx_source` (`source`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='事件标签表';

-- 5. 事件历史关联表
CREATE TABLE IF NOT EXISTS `hot_aggr_event_history_relations` (
    `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '关联主键',
    `parent_event_id` INT NOT NULL COMMENT '父事件ID',
    `child_event_id` INT NOT NULL COMMENT '子事件ID',
    `relation_type` VARCHAR(50) NOT NULL COMMENT '关联类型',
    `confidence_score` DECIMAL(5,4) COMMENT '关联置信度',
    `description` TEXT COMMENT '关联描述',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    FOREIGN KEY (`parent_event_id`) REFERENCES `hot_aggr_events`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`child_event_id`) REFERENCES `hot_aggr_events`(`id`) ON DELETE CASCADE,
    INDEX `idx_parent_event_id` (`parent_event_id`),
    INDEX `idx_child_event_id` (`child_event_id`),
    INDEX `idx_relation_type` (`relation_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='事件历史关联表';

-- 6. 处理日志表
CREATE TABLE IF NOT EXISTS `hot_aggr_processing_logs` (
    `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '日志主键',
    `task_type` VARCHAR(50) NOT NULL COMMENT '任务类型',
    `task_id` VARCHAR(100) COMMENT '任务ID',
    `start_time` DATETIME NOT NULL COMMENT '开始时间',
    `end_time` DATETIME COMMENT '结束时间',
    `status` VARCHAR(20) NOT NULL COMMENT '状态',
    `total_count` INT DEFAULT 0 COMMENT '总处理数量',
    `success_count` INT DEFAULT 0 COMMENT '成功数量',
    `failed_count` INT DEFAULT 0 COMMENT '失败数量',
    `error_message` TEXT COMMENT '错误信息',
    `config_snapshot` TEXT COMMENT '配置快照',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX `idx_task_type` (`task_type`),
    INDEX `idx_task_id` (`task_id`),
    INDEX `idx_status` (`status`),
    INDEX `idx_start_time` (`start_time`),
    INDEX `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='处理日志表';

-- 创建表完成提示
SELECT 'All tables with hot_aggr_ prefix created successfully!' as message;