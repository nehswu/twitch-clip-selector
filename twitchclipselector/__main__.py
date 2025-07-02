# twitchclipselector/__main__.py

import asyncio
import argparse
from twitchclipselector.core import run

def main():
    parser = argparse.ArgumentParser(description="Get a random Twitch clip from a specified streamer.")
    parser.add_argument("streamer", help="Twitch streamer login name")
    parser.add_argument("-i", "--ignore-db", action="store_true", help="Ignore seen clip tracking")
    parser.add_argument("-l", "--limit", type=int, default=100, help="Max number of clips to fetch from Twitch (default: 100)")
    args = parser.parse_args()

    asyncio.run(run(args))


if __name__ == "__main__":
    main()