# main.py

import sys
import subprocess
from r2 import sync_from_r2, sync_to_r2

def run(cmd):
    print(f"[RUN] {cmd}")
    subprocess.run(cmd, shell=True, check=True)


def champion():
    run("python scraper/champion_scraper.py")
    run("python scraper/championdata_scraper.py")
    run("python scraper/make_ai_input.py")


def patch():
    run("python scraper/champion_scraper.py")
    run("python scraper/patch_scraper.py")
    run("python scraper/champion_lane.py")


def ai():
    run("python scraper/response_ai.py")


if __name__ == "__main__":
    sync_from_r2()

    try:

        if len(sys.argv) < 2:
            print("usage:")
            print("python main.py champion")
            print("python main.py patch")
            print("python main.py ai")
            sys.exit(1)

        mode = sys.argv[1]

        if mode == "champion":
            champion()

        elif mode == "patch":
            patch()

        elif mode == "ai":
            ai()

        else:
            raise ValueError(f"unknown mode: {mode}")
        
    finally:
        sync_to_r2()