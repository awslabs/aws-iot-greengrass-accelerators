"""Extracts messages from CAN Bus interface and persists to Extract queue"""
import os
import pidlist
from extract_methods import file_playback

PIDS = pidlist.PIDS

def main() -> None:
    """Code to execute from script"""
    file_playback(os.environ['FILE_PATH']+"/events1.txt")

if __name__ == "__main__":
    main()