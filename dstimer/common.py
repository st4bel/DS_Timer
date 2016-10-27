import os

USER_AGENT = "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.75 Safari/537.36"

def get_root_folder():
    return os.path.join(os.path.expanduser("~"), ".dstimer")

def create_folder_structure():
    """Create all folders needed by DS_Timer

    Currently this creates a '.dstimer' folder in the user's home directory
    on all platforms.
    """
    root = get_root_folder()
    os.makedirs(root, exist_ok=True)
    folders = ["schedule", "trash", "expired", "cache", "keks", "logs"]
    for folder in folders:
        os.makedirs(os.path.join(root, folder), exist_ok=True)
