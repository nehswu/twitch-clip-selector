# Twitch Clip Selector

A Python tool to fetch a random Twitch clip for a given streamer, with support for tracking already-seen clips using a local SQLite database.

## Features

- Fetches random clips for any Twitch streamer.
- Avoids repeating clips by tracking seen clips in a local database.
- Optionally ignores the database to allow repeats.
- Outputs results as JSON for easy integration.
- Simple CLI interface.

## Requirements

- Python 3.8+
- Twitch API credentials

## Installation

1. **Clone the repository:**
   ```sh
   git clone https://github.com/yourusername/twitch-clip-selector.git
   cd twitch-clip-selector
   ```

2. **Create and activate a virtual environment (optional but recommended):**
   ```sh
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```

4. **Set up your environment variables:**
   - Copy `.env.example` to `.env` and fill in your Twitch credentials:
     ```
     TWITCH_CLIENT_ID=your_client_id
     TWITCH_CLIENT_SECRET=your_client_secret
     CLIPS_DB_PATH=seen_clips.db
     ```

## Usage

Run the tool from the command line:

```sh
python -m twitchclipselector <streamer_login> [--limit N] [--ignore-db]
```

### Arguments

- `<streamer_login>` (required): Twitch login name of the streamer.
- `-l`, `--limit` (optional): Maximum number of recent clips to consider (default: 100).
- `-i`, `--ignore-db` (optional): Ignore the seen clips database and allow repeats.

### Example

```sh
python -m twitchclipselector pokimane --limit 10
```

## Development

- All main logic is in `twitchclipselector/core.py`.
- The CLI entry point is in `twitchclipselector/__main__.py`.

## License

MIT License

---

*Made with ❤️ for streamers!*