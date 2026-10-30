import os
import time
import logging
from sync_wispr import sync, DB_PATH, LOCAL_AGENT_DB

logging.basicConfig(
    format="%(asctime)s - [Cloud Sync Watcher] %(message)s",
    level=logging.INFO
)

def watch():
    logging.info("Starting background cloud sync watcher...")
    last_wispr_mtime = os.path.getmtime(DB_PATH) if os.path.exists(DB_PATH) else 0
    last_db_mtime = os.path.getmtime(LOCAL_AGENT_DB) if os.path.exists(LOCAL_AGENT_DB) else 0
    counter = 0

    while True:
        try:
            time.sleep(10)
            counter += 1
            should_sync = False
            
            # 1. Check Wispr Flow
            if os.path.exists(DB_PATH):
                current_wispr = os.path.getmtime(DB_PATH)
                if current_wispr != last_wispr_mtime:
                    logging.info("Wispr Flow updated. Syncing...")
                    last_wispr_mtime = current_wispr
                    should_sync = True
                    
            # 2. Check local database
            if os.path.exists(LOCAL_AGENT_DB):
                current_db = os.path.getmtime(LOCAL_AGENT_DB)
                if current_db != last_db_mtime:
                    logging.info("Local agent database updated. Syncing...")
                    last_db_mtime = current_db
                    should_sync = True
                    
            # 3. Periodic cloud poll every 60 seconds (counter == 6)
            if counter >= 6:
                counter = 0
                should_sync = True

            if should_sync:
                sync()
                # Update mtime after sync so sync itself doesn't loop
                if os.path.exists(LOCAL_AGENT_DB):
                    last_db_mtime = os.path.getmtime(LOCAL_AGENT_DB)

        except KeyboardInterrupt:
            logging.info("Sync Watcher stopped by user.")
            break
        except Exception as e:
            logging.error(f"Watcher loop error: {e}")
            time.sleep(10)

if __name__ == "__main__":
    watch()
