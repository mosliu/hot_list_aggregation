-- 数据库迁移脚本：为hot_aggr_events表添加category字段
-- 执行时间：2025-09-29
-- 说明：为EVENT_AGGREGATION_TEMPLATE新增的category字段添加数据库支持

-- 检查字段是否已存在，如果不存在则添加
SET @sql = (
    SELECT IF(
        (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
         WHERE TABLE_SCHEMA = DATABASE() 
         AND TABLE_NAME = 'hot_aggr_events' 
         AND COLUMN_NAME = 'category') = 0,
        'ALTER TABLE `hot_aggr_events` ADD COLUMN `category` varchar(50) DEFAULT NULL COMMENT ''事件分类'' AFTER `description`;',
        'SELECT ''Category field already exists'' as message;'
    )
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 验证字段添加结果
SELECT 
    COLUMN_NAME,
    DATA_TYPE,
    CHARACTER_MAXIMUM_LENGTH,
    IS_NULLABLE,
    COLUMN_DEFAULT,
    COLUMN_COMMENT
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_SCHEMA = DATABASE() 
AND TABLE_NAME = 'hot_aggr_events' 
AND COLUMN_NAME IN ('category', 'entities')
ORDER BY ORDINAL_POSITION;