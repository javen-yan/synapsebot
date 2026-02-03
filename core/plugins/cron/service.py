import time
import logging
import uuid
import asyncio
from typing import List, Optional
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

from core.eventbus import EventBus
from core.plugins.cron.models import (
    CronJob, CronJobCreate, CronJobPatch, 
    ScheduleType
)
from core.plugins.cron.store import CronStore

logger = logging.getLogger(__name__)

class CronService:
    def __init__(self, store: CronStore, event_bus: EventBus):
        self.store = store
        self.event_bus = event_bus
        self.scheduler = AsyncIOScheduler(logger=logger)
        self._jobs_cache: List[CronJob] = []
        self._initialized = False

    async def start(self):
        """Starts the scheduler and loads existing jobs."""
        if self._initialized:
            return

        logger.debug("[CronService] Starting...")
        self.scheduler.start()
        
        # Load jobs from store
        self._jobs_cache = await self.store.load()
        logger.debug(f"[CronService] Loaded {len(self._jobs_cache)} jobs from store")
        
        # Cleanup expired AT jobs
        now_ms = int(time.time() * 1000)
        jobs_to_remove = []
        for job in self._jobs_cache:
            if job.schedule.kind == ScheduleType.AT and job.schedule.atMs and job.schedule.atMs < now_ms:
                # remove expired AT jobs
                jobs_to_remove.append(job.id)
        
        if jobs_to_remove:
            logger.debug(f"[CronService] Removing {len(jobs_to_remove)} expired jobs during startup")
            for job_id in jobs_to_remove:
                await self.remove_job(job_id)

        # Schedule remaining jobs
        for job in self._jobs_cache:
            if job.enabled:
                self._schedule_job(job)
        
        self._initialized = True

    def stop(self):
        """Stops the scheduler."""
        self.scheduler.shutdown()
        self._initialized = False

    async def add_job(self, create_params: CronJobCreate) -> CronJob:
        """Creates and schedules a new cron job."""
        now_ms = int(time.time() * 1000)
        job = CronJob(
            id=str(uuid.uuid4()),
            **create_params.model_dump(),
            createdAtMs=now_ms,
            updatedAtMs=now_ms
        )
        
        self._jobs_cache.append(job)
        await self.store.save(self._jobs_cache)
        
        if job.enabled:
            self._schedule_job(job)
            
        logger.debug(f"[CronService] Added job {job.id} ({job.name})")
        return job

    async def remove_job(self, job_id: str) -> bool:
        """Removes a job."""
        job_idx = next((i for i, j in enumerate(self._jobs_cache) if j.id == job_id), -1)
        if job_idx == -1:
            return False
            
        # Unschedule if needed
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)
            
        self._jobs_cache.pop(job_idx)
        await self.store.save(self._jobs_cache)
        logger.debug(f"[CronService] Removed job {job_id}")
        return True

    def list_jobs(self, include_disabled: bool = False) -> List[CronJob]:
        """Lists all jobs."""
        if include_disabled:
            return self._jobs_cache
        return [j for j in self._jobs_cache if j.enabled]

    def get_job(self, job_id: str) -> Optional[CronJob]:
        return next((j for j in self._jobs_cache if j.id == job_id), None)

    async def update_job(self, job_id: str, patch: CronJobPatch) -> Optional[CronJob]:
        """Updates an existing job."""
        job_idx = next((i for i, j in enumerate(self._jobs_cache) if j.id == job_id), -1)
        if job_idx == -1:
            return None
            
        job = self._jobs_cache[job_idx]
        
        # Update fields
        patch_data = patch.model_dump(exclude_unset=True)
        updated_job = job.model_copy(update=patch_data)
        updated_job.updatedAtMs = int(time.time() * 1000)
        
        # Reschedule if schedule or enabled changed
        schedule_changed = "schedule" in patch_data
        enabled_changed = "enabled" in patch_data
        
        if schedule_changed or enabled_changed:
            # Remove old schedule
            if self.scheduler.get_job(job_id):
                self.scheduler.remove_job(job_id)
                
            # Add new schedule if enabled
            if updated_job.enabled:
                self._schedule_job(updated_job)
        
        self._jobs_cache[job_idx] = updated_job
        await self.store.save(self._jobs_cache)
        logger.debug(f"[CronService] Updated job {job_id}")
        return updated_job

    def _schedule_job(self, job: CronJob):
        """Internal: Registers a job with APScheduler."""
        try:
            trigger = None
            if job.schedule.kind == ScheduleType.AT:
                if job.schedule.atMs:
                    run_date = datetime.fromtimestamp(job.schedule.atMs / 1000, tz=timezone.utc)
                    trigger = DateTrigger(run_date=run_date)
            
            elif job.schedule.kind == ScheduleType.EVERY:
                if job.schedule.everyMs:
                    seconds = job.schedule.everyMs / 1000
                    trigger = IntervalTrigger(seconds=seconds)
                    
            elif job.schedule.kind == ScheduleType.CRON:
                if job.schedule.expr:
                    # Very basic cron parsing, usually split by space
                    # APScheduler format: minute, hour, day, month, day_of_week
                    # We assume standard 5-part cron
                    vals = job.schedule.expr.split()
                    if len(vals) >= 5:
                         trigger = CronTrigger.from_crontab(job.schedule.expr)
                    else:
                        logger.error(f"[CronService] Invalid cron expression for job {job.id}: {job.schedule.expr}")
                        return

            if trigger:
                self.scheduler.add_job(
                    self._handle_trigger,
                    trigger=trigger,
                    id=job.id, # Use job ID as scheduler ID
                    args=[job.id],
                    replace_existing=True
                )
        except Exception as e:
            logger.error(f"[CronService] Failed to schedule job {job.id}: {e}")


    async def _handle_trigger(self, job_id: str):
        """Callback when a job is triggered."""
        logger.debug(f"[CronService] Job triggered: {job_id}")
        
        job = self.get_job(job_id)
        if not job:
            return

        now_ms = int(time.time() * 1000)
        
        # Update State
        job.state.lastRunAtMs = now_ms
        job.state.lastStatus = "ok" # optimistically
        
        # Calculate next run
        aps_job = self.scheduler.get_job(job_id)
        if aps_job and aps_job.next_run_time:
            job.state.nextRunAtMs = int(aps_job.next_run_time.timestamp() * 1000)
        
        # Publish Event
        await self.event_bus.publish("cron:trigger", job)

        await self.store.save(self._jobs_cache)

        # Handle one-shot cleanup
        # Only save if we modify the job (e.g., enable=False)
        # Handle cleanup
        if job.deleteAfterRun:
             await self.remove_job(job.id)
        elif job.schedule.kind == ScheduleType.AT:
             # Default behavior for AT jobs: Disable after run
            await self.update_job(job.id, CronJobPatch(enabled=False))
