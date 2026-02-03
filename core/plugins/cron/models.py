from enum import Enum
from typing import Optional, Literal, Union
from pydantic import BaseModel, Field
from typing import List

class ScheduleType(str, Enum):
    AT = "at"
    EVERY = "every"
    CRON = "cron"

class CronSchedule(BaseModel):
    kind: ScheduleType
    atMs: Optional[int] = None
    everyMs: Optional[int] = None
    anchorMs: Optional[int] = None
    expr: Optional[str] = None
    tz: Optional[str] = None

class PayloadType(str, Enum):
    SYSTEM_EVENT = "systemEvent"
    AGENT_TURN = "agentTurn"

class CronPayload(BaseModel):
    kind: PayloadType
    # systemEvent
    text: Optional[str] = None
    # agentTurn
    message: Optional[str] = None
    model: Optional[str] = None
    thinking: Optional[str] = None
    timeoutSeconds: Optional[int] = None
    deliver: Optional[bool] = None
    channel: Optional[str] = None
    to: Optional[str] = None
    bestEffortDeliver: Optional[bool] = None

class CronSessionTarget(str, Enum):
    MAIN = "main"
    ISOLATED = "isolated"

class CronJobState(BaseModel):
    nextRunAtMs: Optional[int] = None
    lastRunAtMs: Optional[int] = None
    lastStatus: Optional[Literal["ok", "error", "skipped"]] = None
    lastError: Optional[str] = None
    lastDurationMs: Optional[int] = None

class CronJob(BaseModel):
    id: str
    agentId: Optional[str] = None
    name: str = ""
    meta: Optional[dict] = None
    description: Optional[str] = None
    enabled: bool = True
    deleteAfterRun: Optional[bool] = None
    createdAtMs: int
    updatedAtMs: int
    schedule: CronSchedule
    sessionTarget: CronSessionTarget = CronSessionTarget.MAIN
    payload: CronPayload
    state: CronJobState = Field(default_factory=CronJobState)

class CronJobCreate(BaseModel):
    agentId: Optional[str] = None
    name: Optional[str] = ""
    meta: Optional[dict] = None
    schedule: CronSchedule
    payload: CronPayload
    sessionTarget: CronSessionTarget = CronSessionTarget.MAIN
    enabled: bool = True
    deleteAfterRun: Optional[bool] = None

class CronJobPatch(BaseModel):
    name: Optional[str] = None
    enabled: Optional[bool] = None
    schedule: Optional[CronSchedule] = None
    payload: Optional[CronPayload] = None
    
class CronStoreFile(BaseModel):
    version: int = 1
    jobs: List[CronJob] = []
