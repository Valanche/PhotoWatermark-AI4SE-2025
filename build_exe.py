# PhotoWatermark-AI4SE 打包脚本
# 使用 PyInstaller 创建 Windows 可执行文件

import os
import sys
import subprocess
import shutil

def create_executable():
    """创建可执行文件"""
    print("开始创建 PhotoWatermark-AI4SE 可执行文件...")
    
    # 获取项目根目录
    project_root = os.path.dirname(os.path.abspath(__file__))
    print(f"项目根目录: {project_root}")
    
    # 切换到项目根目录
    os.chdir(project_root)
    
    # PyInstaller 命令参数
    cmd = [
        "pyinstaller",
        "--name", "PhotoWatermark-AI4SE",
        "--windowed",  # 不显示控制台窗口
        "--onefile",   # 打包成单个可执行文件
        "--clean",     # 清理临时文件
        "--distpath", "dist",  # 指定输出目录
        "--workpath", "build", # 指定构建目录
        "--specpath", "build", # 指定 spec 文件目录

        "photowatermark/main.py"  # 主入口文件
    ]
    
    print("正在执行 PyInstaller 命令...")
    print(" ".join(cmd))
    
    try:
        # 执行 PyInstaller 命令
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("PyInstaller 执行完成!")
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print("PyInstaller 执行失败!")
        print(f"错误代码: {e.returncode}")
        print(f"错误输出: {e.stderr}")
        return False
    except Exception as e:
        print(f"执行过程中发生错误: {str(e)}")
        return False

def main():
    """主函数"""
    print("=" * 50)
    print("PhotoWatermark-AI4SE 打包工具")
    print("=" * 50)
    
    # 创建可执行文件
    success = create_executable()
    
    if success:
        print("\n" + "=" * 50)
        print("打包完成!")
        print("可执行文件位置: dist/PhotoWatermark-AI4SE.exe")
        print("=" * 50)
        
        # 检查生成的文件
        exe_path = os.path.join("dist", "PhotoWatermark-AI4SE.exe")
        if os.path.exists(exe_path):
            size = os.path.getsize(exe_path)
            print(f"文件大小: {size / (1024*1024):.2f} MB")
        else:
            print("警告: 未找到生成的可执行文件!")
    else:
        print("\n" + "=" * 50)
        print("打包失败!")
        print("=" * 50)
        sys.exit(1)

if __name__ == "__main__":
    main()