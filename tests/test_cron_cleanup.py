import pytest
import time
from unittest.mock import AsyncMock, MagicMock
from core.plugins.cron.service import CronService
from core.plugins.cron.models import CronJob, ScheduleType, CronSchedule, PayloadType, CronPayload

@pytest.fixture
def mock_store():
    store = AsyncMock()
    store.save = AsyncMock()
    return store

@pytest.fixture
def mock_event_bus():
    return AsyncMock()

@pytest.fixture
def cron_service(mock_store, mock_event_bus):
    service = CronService(mock_store, mock_event_bus)
    # Mock scheduler
    service.scheduler = MagicMock()
    return service

@pytest.mark.asyncio
async def test_start_cleanup_expired_jobs(cron_service):
    now_ms = int(time.time() * 1000)
    past_ms = now_ms - 100000 # 100s ago
    future_ms = now_ms + 100000
    
    expired_job = CronJob(
        id="expired",
        name="Expired Job",
        createdAtMs=now_ms,
        updatedAtMs=now_ms,
        schedule=CronSchedule(kind=ScheduleType.AT, atMs=past_ms),
        payload=CronPayload(kind=PayloadType.SYSTEM_EVENT, text="test")
    )
    
    valid_job = CronJob(
        id="valid",
        name="Valid Job",
        createdAtMs=now_ms,
        updatedAtMs=now_ms,
        schedule=CronSchedule(kind=ScheduleType.AT, atMs=future_ms),
        payload=CronPayload(kind=PayloadType.SYSTEM_EVENT, text="test")
    )
    
    cron_service.store.load.return_value = [expired_job, valid_job]
    
    # Mock remove_job to update local cache as real one does, or just inspect calls
    # Since remove_job depends on _jobs_cache being populated, we need to populate it first?
    # But start() calls load() then populates _jobs_cache. 
    # Wait, start() assigns self._jobs_cache = await self.store.load()
    # So we don't need to manually populate it before start.
    
    # However, remove_job uses self._jobs_cache.pop
    # We should mock remove_job or let it run.
    # Let's let it run but we need to ensure store.save is mocked (it is).
    # And scheduler.get_job needs to be safe.
    cron_service.scheduler.get_job.return_value = None
    
    await cron_service.start()
    
    # Check if expired job was removed
    # The _jobs_cache should only have valid_job
    assert len(cron_service._jobs_cache) == 1
    assert cron_service._jobs_cache[0].id == "valid"
    
    # Verify save was called (once for remove, potentially)
    assert cron_service.store.save.called

@pytest.mark.asyncio
async def test_handle_trigger_delete_after_run(cron_service):
    job = CronJob(
        id="delete-me",
        name="Cleanup Job",
        createdAtMs=1000,
        updatedAtMs=1000,
        schedule=CronSchedule(kind=ScheduleType.AT, atMs=2000),
        payload=CronPayload(kind=PayloadType.SYSTEM_EVENT, text="test"),
        deleteAfterRun=True
    )
    
    cron_service._jobs_cache = [job]
    cron_service.get_job = MagicMock(return_value=job)
    cron_service.scheduler.get_job.return_value = None
    
    await cron_service._handle_trigger("delete-me")
    
    # Verify removal
    assert len(cron_service._jobs_cache) == 0
    assert cron_service.store.save.called
