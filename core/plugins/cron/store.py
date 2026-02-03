import asyncio
import os
import json
import logging
import aiofiles
from typing import List
from core.config import StorageConfig
from core.plugins.cron.models import CronJob, CronStoreFile

logger = logging.getLogger(__name__)

class CronStore:
    def __init__(self, config: StorageConfig):
        self.config = config
        self.store_path = os.path.join(os.path.expanduser(config.data_path), "cron", "store.json")
        self._ensure_dir()

    def _ensure_dir(self):
        dirname = os.path.dirname(self.store_path)
        if not os.path.exists(dirname):
            os.makedirs(dirname, exist_ok=True)

    async def load(self) -> List[CronJob]:
        if not os.path.exists(self.store_path):
            return []
        
        try:
            async with aiofiles.open(self.store_path, "r", encoding="utf-8") as f:
                content = await f.read()
                data = json.loads(content)
                store_file = CronStoreFile(**data)
                return store_file.jobs
        except Exception as e:
            logger.error(f"[CronStore] Error loading jobs: {e}")
            return []

    async def save(self, jobs: List[CronJob]):
        try:
            store_file = CronStoreFile(jobs=jobs)
            # Use model_dump_json for Pydantic v2
            json_str = store_file.model_dump_json(indent=2)
            
            async with aiofiles.open(self.store_path, "w", encoding="utf-8") as f:
                await f.write(json_str)
        except Exception as e:
            logger.error(f"[CronStore] Error saving jobs: {e}")
