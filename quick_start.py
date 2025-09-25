#!/usr/bin/env python3
"""
热点新闻聚合系统快速启动脚本
提供简化的命令行界面，方便用户快速使用系统功能
"""

import sys
import subprocess
from datetime import datetime, timedelta
from loguru import logger

def print_banner():
    """打印系统横幅"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                   热点新闻聚合系统                           ║
║                 Hot News Aggregation System                  ║
║                                                              ║
║  🚀 快速启动脚本 - 让新闻聚合变得简单                        ║
╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def show_menu():
    """显示主菜单"""
    menu = """
📋 请选择操作模式：

1. 📊 查看系统统计 (最近7天)
2. ⚡ 增量处理 (最近6小时新闻)
3. 🔄 增量处理 (最近24小时新闻)
4. 📝 按类型处理 (指定新闻类型)
5. 🔧 自定义处理 (自定义参数)
6. 🧪 运行系统测试
7. 📖 查看帮助文档
8. 🚪 退出系统

请输入选项编号 (1-8): """
    
    return input(menu).strip()

def run_command(cmd_args):
    """执行命令并显示结果"""
    try:
        logger.info(f"执行命令: python {' '.join(cmd_args)}")
        result = subprocess.run(
            [sys.executable] + cmd_args,
            capture_output=False,
            text=True
        )
        return result.returncode == 0
    except Exception as e:
        logger.error(f"命令执行失败: {e}")
        return False

def get_statistics():
    """获取系统统计"""
    print("\n📊 获取系统统计信息...")
    return run_command(["main_processor.py", "--mode", "stats", "--days", "7"])

def incremental_6h():
    """增量处理 - 6小时"""
    print("\n⚡ 处理最近6小时的新闻...")
    return run_command(["main_processor.py", "--mode", "incremental", "--hours", "6"])

def incremental_24h():
    """增量处理 - 24小时"""
    print("\n🔄 处理最近24小时的新闻...")
    return run_command(["main_processor.py", "--mode", "incremental", "--hours", "24"])

def process_by_type():
    """按类型处理"""
    print("\n📝 按类型处理新闻")
    print("常见类型: 科技, 财经, 体育, 娱乐, 社会, 国际, 政治")
    news_type = input("请输入新闻类型: ").strip()
    
    if not news_type:
        print("❌ 新闻类型不能为空")
        return False
    
    print(f"\n处理类型为 '{news_type}' 的新闻...")
    return run_command(["main_processor.py", "--mode", "by_type", "--news_type", news_type])

def custom_process():
    """自定义处理"""
    print("\n🔧 自定义处理参数")
    
    # 选择模式
    print("处理模式:")
    print("1. full - 全量处理")
    print("2. incremental - 增量处理")
    print("3. by_type - 按类型处理")
    
    mode_choice = input("选择模式 (1-3): ").strip()
    mode_map = {"1": "full", "2": "incremental", "3": "by_type"}
    
    if mode_choice not in mode_map:
        print("❌ 无效的模式选择")
        return False
    
    mode = mode_map[mode_choice]
    cmd_args = ["main_processor.py", "--mode", mode]
    
    # 根据模式添加参数
    if mode == "full":
        start_time = input("开始时间 (YYYY-MM-DD HH:MM:SS, 回车使用默认): ").strip()
        end_time = input("结束时间 (YYYY-MM-DD HH:MM:SS, 回车使用默认): ").strip()
        
        if start_time:
            cmd_args.extend(["--start_time", start_time])
        if end_time:
            cmd_args.extend(["--end_time", end_time])
            
    elif mode == "incremental":
        hours = input("处理最近几小时 (默认6): ").strip() or "6"
        cmd_args.extend(["--hours", hours])
        
    elif mode == "by_type":
        news_type = input("新闻类型: ").strip()
        if not news_type:
            print("❌ 新闻类型不能为空")
            return False
        cmd_args.extend(["--news_type", news_type])
    
    # 可选参数
    batch_size = input("批处理大小 (默认10): ").strip()
    if batch_size:
        cmd_args.extend(["--batch_size", batch_size])
    
    model = input("LLM模型 (默认gpt-3.5-turbo): ").strip()
    if model:
        cmd_args.extend(["--model", model])
    
    no_progress = input("不显示进度 (y/N): ").strip().lower()
    if no_progress == 'y':
        cmd_args.append("--no_progress")
    
    print(f"\n执行自定义处理...")
    return run_command(cmd_args)

def run_tests():
    """运行系统测试"""
    print("\n🧪 运行系统测试...")
    return run_command(["test_scripts/test_main_processor.py"])

def show_help():
    """显示帮助文档"""
    print("\n📖 系统帮助文档")
    print("="*60)
    
    help_text = """
🎯 系统功能说明:

1. 📊 系统统计: 查看最近几天的处理统计信息
2. ⚡ 增量处理: 处理最近几小时的新闻数据
3. 📝 按类型处理: 只处理指定类型的新闻
4. 🔧 自定义处理: 完全自定义处理参数

🔧 配置文件:
- .env: 系统环境配置
- config/settings_new.py: 详细配置参数

📁 重要文件:
- main_processor.py: 主处理器
- services/: 核心服务模块
- models/: 数据模型定义
- docs/: 详细文档

🚀 快速开始:
1. 确保配置了 .env 文件
2. 启动 Redis 服务
3. 运行系统测试验证环境
4. 开始处理新闻数据

📞 获取更多帮助:
- 查看 docs/SYSTEM_IMPLEMENTATION_COMPLETE.md
- 运行: python main_processor.py --help
    """
    
    print(help_text)
    input("\n按回车键返回主菜单...")

def main():
    """主函数"""
    print_banner()
    
    while True:
        try:
            choice = show_menu()
            
            if choice == "1":
                get_statistics()
            elif choice == "2":
                incremental_6h()
            elif choice == "3":
                incremental_24h()
            elif choice == "4":
                process_by_type()
            elif choice == "5":
                custom_process()
            elif choice == "6":
                run_tests()
            elif choice == "7":
                show_help()
            elif choice == "8":
                print("\n👋 感谢使用热点新闻聚合系统！")
                break
            else:
                print("\n❌ 无效的选项，请重新选择")
            
            if choice in ["1", "2", "3", "4", "5", "6"]:
                input("\n按回车键返回主菜单...")
                
        except KeyboardInterrupt:
            print("\n\n👋 用户中断，退出系统")
            break
        except Exception as e:
            logger.error(f"系统错误: {e}")
            print(f"\n❌ 系统错误: {e}")
            input("按回车键继续...")

if __name__ == "__main__":
    main()