-- 创建新的事件表和关联表（无外键约束，无索引）
-- 适用于权限受限的数据库环境

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ============================================================================
-- 新事件表 (events_new)
-- 存储聚合后的事件信息（无索引版本）
-- ============================================================================
CREATE TABLE IF NOT EXISTS `events_new` (
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
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='新事件表（无索引版本）';

-- ============================================================================
-- 新闻事件关联表 (news_event_relations_new)
-- 存储新闻与事件的多对多关联关系（无索引版本）
-- ============================================================================
CREATE TABLE IF NOT EXISTS `news_event_relations_new` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `news_id` bigint NOT NULL COMMENT '新闻ID',
  `event_id` bigint NOT NULL COMMENT '事件ID',
  `relation_type` varchar(20) DEFAULT 'primary' COMMENT '关联类型：primary-主要关联，secondary-次要关联，reference-引用关联',
  `confidence` decimal(5,4) DEFAULT '0.0000' COMMENT '关联置信度',
  `weight` decimal(5,4) DEFAULT '1.0000' COMMENT '权重',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `created_by` varchar(100) DEFAULT 'system' COMMENT '创建者',
  `notes` varchar(500) DEFAULT '' COMMENT '关联备注',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='新闻事件关联表（无索引版本）';

-- 恢复外键检查
SET FOREIGN_KEY_CHECKS = 1;

-- 创建完成提示
SELECT 'New tables created successfully without indexes!' as message;