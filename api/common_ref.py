"""References to common/ utilities. In the umbrella repo, common/ is a sibling subtree."""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "common"))


def get_version():
    try:
        from config import APP_VERSION
        return APP_VERSION
    except ImportError:
        return "unknown"


def get_category_name(category_id):
    try:
        from utils import get_category_name as _get_category_name
        return _get_category_name(category_id)
    except ImportError:
        return "Unknown"
