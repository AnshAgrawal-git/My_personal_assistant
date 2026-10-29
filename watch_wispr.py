import os
import time
import logging
from sync_wispr import sync, DB_PATH

logging.basicConfig(
    format="%(asctime)s - [Wispr Watcher] %(message)s",
    level=logging.INFO
)

def watch():
    if not os.path.exists(DB_PATH):
        logging.error(f"Wispr Flow database not found at: {DB_PATH}")
        return

    logging.info(f"Watching Wispr Flow database for changes: {DB_PATH}")
    last_mtime = os.path.getmtime(DB_PATH)

    while True:
        try:
            time.sleep(10)
            if not os.path.exists(DB_PATH):
                continue
                
            current_mtime = os.path.getmtime(DB_PATH)
            if current_mtime != last_mtime:
                logging.info("Wispr Flow database changed! Triggering auto-sync...")
                last_mtime = current_mtime
                # Small delay to ensure Wispr Flow finished writing
                time.sleep(1)
                sync()
        except KeyboardInterrupt:
            logging.info("Wispr Watcher stopped by user.")
            break
        except Exception as e:
            logging.error(f"Watcher loop error: {e}")
            time.sleep(10)

if __name__ == "__main__":
    watch()
