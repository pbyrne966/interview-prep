import heapq
from threading import Lock
from time import time

from pydantic import BaseModel


class ConversationRecord(BaseModel):
    conversation_id: str
    last_timestamp: int
    total_events: int = 1
    total_alerts_fired: int = 0
    longest_silence: int = 0


class AlertEmitter(BaseModel):
    conversation_id: str
    silence_start: int
    silence_end: int
    duration: int


class ConversationBuffer:
    def __init__(self, grace_period: int) -> None:
        self.grace_period = grace_period
        self.heap: list[tuple[int, int]] = []
        self.seq: int = 0
        self.watermark: int = -1

    def push(self, timestamp: int) -> None:
        heapq.heappush(self.heap, (timestamp, self.seq))
        self.seq += 1

    def is_late(self, timestamp: int) -> bool:
        return timestamp < (self.watermark - self.grace_period)

    def drain(self, current_wall_time: int) -> list[int]:
        drain_up_to = current_wall_time - self.grace_period
        ready: list[int] = []

        while self.heap and self.heap[0][0] <= drain_up_to:
            ts, _ = heapq.heappop(self.heap)
            ready.append(ts)

        if ready:
            self.watermark = ready[-1]

        return ready


class ConversationMonitor:
    def __init__(self, silence_threshold: int, grace_period: int = 0) -> None:
        self.silence_threshold = silence_threshold
        self.grace_period = grace_period
        self.records: dict[str, ConversationRecord] = {}
        self.buffers: dict[str, ConversationBuffer] = {}
        self.lock = Lock()

    def _get_or_create_buffer(self, conversation_id: str) -> ConversationBuffer:
        current_buffer = self.buffers.get(conversation_id)
        if current_buffer is None:
            self.buffers[conversation_id] = ConversationBuffer(self.grace_period)
            current_buffer = self.buffers[conversation_id]
        return current_buffer

    def _process_timestamp(
        self, conversation_id: str, timestamp: int
    ) -> AlertEmitter | None:

        if conversation_id not in self.records:
            self.records[conversation_id] = ConversationRecord(
                conversation_id=conversation_id, last_timestamp=timestamp
            )
            return None

        record = self.records[conversation_id]
        duration = timestamp - record.last_timestamp

        record.last_timestamp = timestamp
        record.total_events += 1

        if duration > self.silence_threshold:
            alert = AlertEmitter(
                **{
                    "conversation_id": conversation_id,
                    "silence_start": record.last_timestamp,
                    "silence_end": timestamp,
                    "duration": duration,
                }
            )
            record.total_alerts_fired += 1
            record.longest_silence = max(record.longest_silence, duration)

            self.emit_alert(alert)
            return alert

        return None

    def emit_alert(self, alert: AlertEmitter) -> None:
        print(alert.model_dump_json(indent=2))

    def record_event(self, conversation_id: str, timestamp: int) -> list[dict]:
        current_buffer = self._get_or_create_buffer(conversation_id)

        if current_buffer.is_late(timestamp):
            print("Current TimeStamp is late")
            return []

        current_buffer.push(timestamp)
        procossed_alerts = []

        for ts in current_buffer.drain(timestamp):
            alert = self._process_timestamp(conversation_id, ts)
            if alert is None:
                continue
            procossed_alerts.append(alert)

        return procossed_alerts

    def get_stats(self, conversation_id: str) -> dict | None:
        record = self.records.get(conversation_id)
        if record is None:
            return None

        return {
            "total_events": record.total_events,
            "total_alerts_fired": record.total_alerts_fired,
            "longest_silence": record.longest_silence,
            "last_event_time": record.last_timestamp,
        }
