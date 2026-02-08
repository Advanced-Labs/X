"""References to common/ utilities. In the umbrella repo, common/ is a sibling subtree."""

def get_version():
    try:
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "common"))
        from config import APP_VERSION
        return APP_VERSION
    except ImportError:
        return "unknown"
