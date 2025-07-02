# twitchclipselector/core.py

import os
import random
import sqlite3
from pathlib import Path
from typing import Optional, Dict
from twitchAPI.twitch import Twitch
from twitchAPI.helper import first
from twitchAPI.type import TwitchAPIException
from dotenv import load_dotenv
import asyncio
import json
import logging

load_dotenv()

logging.basicConfig(level=logging.CRITICAL + 1)
logger = logging.getLogger(__name__)

CLIENT_ID = os.getenv("TWITCH_CLIENT_ID")
CLIENT_SECRET = os.getenv("TWITCH_CLIENT_SECRET")
DB_PATH = os.getenv("CLIPS_DB_PATH", "seen_clips.db")


def init_db():
    db_dir = Path(DB_PATH).parent
    if not db_dir.exists():
        db_dir.mkdir(parents=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS seen_clips (
                streamer TEXT,
                clip_id TEXT PRIMARY KEY
            )
        """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_streamer ON seen_clips(streamer)")


def has_seen_clip(streamer: str, clip_id: str) -> bool:
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT 1 FROM seen_clips WHERE streamer = ? AND clip_id = ?",
            (streamer, clip_id),
        )
        return cur.fetchone() is not None


def mark_clip_seen(streamer: str, clip_id: str):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT OR IGNORE INTO seen_clips (streamer, clip_id) VALUES (?, ?)",
            (streamer, clip_id),
        )


def clear_seen_clips_for_streamer(streamer: str):
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM seen_clips WHERE streamer = ?", (streamer,))
        conn.commit()


async def get_random_clip(twitch: Twitch, streamer_login: str, args) -> dict:
    logger.info(f"Starting to fetch clips for streamer: '{streamer_login}'")

    try:
        user = await first(twitch.get_users(logins=[streamer_login]))
        if not user:
            logger.error(f"Streamer '{streamer_login}' not found on Twitch.")
            return {
                "success": False,
                "error": f"❌ Streamer '{streamer_login}' not found.",
            }

        user_id = user.id
        display_name = user.display_name

        logger.info(f"Retrieving up to {args.limit} clips for '{display_name}' (user_id: {user_id})")
        clip_gen = twitch.get_clips(broadcaster_id=user_id, first=args.limit)
        clips = [clip async for clip in clip_gen]

        if not clips:
            logger.warning(f"No clips found for streamer '{display_name}'.")
            return {"success": False, "error": f"⚠️ No clips found for {display_name}"}

        if args.ignore_db:
            eligible_clips = clips
            logger.info("Database check is ignored; considering all fetched clips as eligible.")
        else:
            eligible_clips = [clip for clip in clips if not has_seen_clip(streamer_login, clip.id)]
            logger.info(f"Filtered out already seen clips; {len(eligible_clips)} eligible clips remain.")

        if not eligible_clips:
            if args.ignore_db:
                eligible_clips = clips
                logger.info("No eligible clips found, but ignore_db is set. Using all fetched clips.")
            else:
                logger.warning(
                    f"All clips have been seen for '{display_name}'. Resetting clip history for this streamer."
                )
                clear_seen_clips_for_streamer(streamer_login)
                eligible_clips = clips

        if not eligible_clips:
            logger.error(f"No usable clips available for '{display_name}' even after resetting history.")
            return {
                "success": False,
                "error": f"⚠️ No usable clips available for {display_name} after reset",
            }

        clip = random.choice(eligible_clips)
        logger.info(f"Randomly selected clip: '{clip.title}' (ID: {clip.id})")

        game_name = "Unknown"
        if clip.game_id:
            logger.info(f"Fetching game information for game_id: {clip.game_id}")
            game = await first(twitch.get_games(game_ids=[clip.game_id]))
            if game:
                game_name = game.name
                logger.info(f"Clip is from game: '{game_name}'")

        result = {
            "success": True,
            "title": clip.title,
            "streamer": display_name,
            "game": game_name,
            "duration": clip.duration,
            "url": clip.url,
        }

        if not args.ignore_db:
            mark_clip_seen(streamer_login, clip.id)
            logger.info(f"Marked clip '{clip.id}' as seen for streamer '{streamer_login}' in the database.")

        return result

    except TwitchAPIException as e:
        logger.error(f"Twitch API error occurred while fetching clips: {str(e)}")
        return {"success": False, "error": f"Twitch API error: {str(e)}"}
    except Exception as e:
        logger.exception(f"Unexpected error occurred while fetching a clip for '{streamer_login}': {str(e)}")
        return {"success": False, "error": f"Unexpected error fetching clip: {str(e)}"}


async def run(args):
    if not CLIENT_ID or not CLIENT_SECRET:
        logger.error("Missing Twitch credentials (TWITCH_CLIENT_ID or TWITCH_CLIENT_SECRET) in .env file. Exiting.")
        print(
            json.dumps(
                {
                    "success": False,
                    "error": "❌ Missing Twitch credentials in .env file.",
                }
            )
        )
        return

    if not args.ignore_db:
        logger.info("Initializing the seen clips database.")
        init_db()

    twitch = await Twitch(CLIENT_ID, CLIENT_SECRET)

    try:
        logger.info(f"Requesting a random clip for streamer '{args.streamer}' with a maximum of {args.limit} clips to consider.")
        result = await get_random_clip(twitch, args.streamer, args)
        print(json.dumps(result, ensure_ascii=False))
        logger.info("Random clip retrieval complete. Output sent as JSON.")
    finally:
        logger.info("Closing Twitch API session.")
        await twitch.close()
