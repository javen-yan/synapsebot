import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock
from core.plugins.cron.tool import CronTool
from core.plugins.cron.service import CronService
from core.plugins.cron.models import CronJob, CronJobCreate

@pytest.fixture
def mock_service():
    service = MagicMock(spec=CronService)
    service.add_job = AsyncMock()
    service.remove_job = AsyncMock()
    service.update_job = AsyncMock()
    service.list_jobs = MagicMock(return_value=[])
    service.scheduler = MagicMock()
    service.scheduler.running = True
    return service

@pytest.mark.asyncio
async def test_cron_tool_add_list_remove(mock_service):
    tool = CronTool(mock_service)
    
    # Test Status
    status_args = {"action": "status"}
    result = await tool(status_args)
    assert "running" in result

    # Test Add
    mock_service.add_job.return_value = CronJob(
        id="job123", 
        name="test", 
        schedule={"kind": "at", "atMs": 123},
        payload={"kind": "systemEvent", "text": "foo"},
        enabled=True,
        createdAtMs=1000,
        updatedAtMs=1000
    )
    
    add_args = {
        "action": "add",
        "job": {
            "name": "test",
            "schedule": {"kind": "at", "delaySeconds": 60},
            "payload": {"kind": "systemEvent", "text": "foo"}
        },
        "_context": {"agent_id": "system"}
    }
    result = await tool(add_args)
    assert "Job added successfully. ID: job123" in result
    mock_service.add_job.assert_called_once()
    
    # Test List
    mock_service.list_jobs.return_value = [
        CronJob(id="job123", name="test", schedule={"kind": "at", "atMs": 123}, payload={"kind":"systemEvent"}, enabled=True, createdAtMs=1000, updatedAtMs=1000)
    ]
    list_args = {"action": "list"}
    result = await tool(list_args)
    assert "job123" in result

    # Test Remove
    mock_service.remove_job.return_value = True
    remove_args = {"action": "remove", "job_id": "job123"}
    result = await tool(remove_args)
    assert "Job job123 removed" in result
    mock_service.remove_job.assert_called_with("job123")
