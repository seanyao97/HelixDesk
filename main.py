"""HelixDesk - 快速启动脚本"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from helixdesk.app import main

if __name__ == '__main__':
    main()