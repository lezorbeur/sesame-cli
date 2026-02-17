#!/usr/bin/env python3
"""
Sesame CLI wrapper entry point.

This module is imported via setup.py console_scripts to avoid conflicts with Python's 'cmd' module.
"""

import sys
import os

# Ensure we can import cmd module from project root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and re-export the main function from cmd.cli
def main(argv=None):
    """Entry point for sesame-cli."""
    from cmd.cli import main as _main
    return _main(argv)

if __name__ == '__main__':
    sys.exit(main())
