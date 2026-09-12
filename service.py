# -*- coding: utf-8 -*-
"""Background service entry point for script.bdcontrol."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                'resources', 'lib'))

from bdcontrol.service import main  # noqa: E402  (path set up above)

if __name__ == '__main__':
    main()
