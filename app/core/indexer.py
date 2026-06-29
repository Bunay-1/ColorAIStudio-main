import os
import json
import asyncio
import logging
from typing import Set

logger = logging.getLogger("ICAP_API")

async def background_indexer(icap_state, manager):
    state_file = "AuditTrail/indexer_state.json"
    indexed_files: Set[str] = set()

    base_dir = "./RAG"
    os.makedirs(base_dir, exist_ok=True)

    consecutive_errors = 0

    while True:
        try:
            # Sync with actual DB state if DB was wiped but state file remains
            stats = await icap_state.rag.get_stats()
            if stats.get("total_chunks") == 0 and os.path.exists(state_file):
                logger.info("RAG Database is empty but state file exists. Resetting state file for re-indexing.")
                indexed_files = set()
                if os.path.exists(state_file): os.remove(state_file)
            elif not indexed_files and os.path.exists(state_file):
                try:
                    with open(state_file, "r") as f:
                        loaded = json.load(f)
                        # Normalize paths: ensure consistency (no leading ./)
                        indexed_files = {os.path.normpath(p) for p in loaded}
                except: pass

            found_any_new = False
            for root, _, files in os.walk(base_dir):
                for file in files:
                    # Normalize both current and stored paths for comparison
                    full_path = os.path.join(root, file)
                    rel_path = os.path.normpath(os.path.relpath(full_path, start="."))

                    if rel_path not in indexed_files and file.lower().endswith(('.pdf', '.docx', '.xlsx', '.csv', '.json', '.md')):
                        logger.info(f"Background Indexer: Processing NEW file: {rel_path}")
                        async def progress_cb(data):
                            await manager.broadcast(data)

                        await icap_state.rag.index_any(full_path, progress_callback=progress_cb)
                        indexed_files.add(rel_path)
                        found_any_new = True
                        with open(state_file, "w") as f: json.dump(list(indexed_files), f)

                        # Update stats and broadcast
                        current_stats = await icap_state.rag.get_stats()
                        await manager.broadcast({
                            "type": "rag_update",
                            "last_file": file,
                            "stats": current_stats
                        })

            # Periodically broadcast stats even if no new files
            if not found_any_new:
                await manager.broadcast({"type": "rag_update", "stats": stats})

            consecutive_errors = 0 # Reset errors on success
            await asyncio.sleep(30) # Пауза при успех за намаляване на натоварването

        except asyncio.CancelledError:
            logger.info("Background indexer task cancelled.")
            break
        except Exception as e:
            consecutive_errors += 1
            logger.error(f"Indexer error (attempt {consecutive_errors}): {e}")
            sleep_time = min(60 * (2 ** (consecutive_errors - 1)), 3600)
            logger.info(f"Retrying in {sleep_time} seconds...")
            await asyncio.sleep(sleep_time)
            continue

        await asyncio.sleep(60)
