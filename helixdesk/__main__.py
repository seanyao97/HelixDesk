"""HelixDesk 入口点: python -m helixdesk"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from helixdesk.app import main

if __name__ == '__main__':
    main()