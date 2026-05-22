# System Design — Real-Time Conversation Silence Detector
### (Intercom / Cresta Style Interview)

---

## 1. Requirements

### Functional
- Ingest a real-time stream of timestamped speech events per conversation
- Detect silence gaps that exceed a configurable threshold
- Fire alerts to supervisors when a silence is detected
- Track per-conversation stats (total events, alerts fired, longest silence)
- Handle out-of-order event delivery gracefully

### Non-Functional
- 10,000 concurrent conversations
- p99 end-to-end alert latency < 2 seconds
- No alert must be permanently lost on a consumer crash
- Horizontally scalable — adding consumers should increase throughput linearly
- State must survive consumer restarts and Kafka partition rebalances

---

## 2. High Level Architecture

```
Mobile / Web Clients
        |
        v
   API Gateway
        |
        v
  Kafka (partitioned by conversation_id)
        |
   _____|_____
  |           |
Consumer A  Consumer B        (each owns a set of partitions)
  |           |
  v           v
ConversationMonitor (in-memory watermark buffer + ConversationRecord cache)
  |           |
  v           v
Redis Cluster (durable ConversationRecord state, TTL per conversation)
  |           |
  v           v
Alert Publisher (Kafka topic / Webhook / WebSocket to supervisor dashboard)
```

---

## 3. Kafka Layer

### Partitioning Strategy
- Partition key = `conversation_id`
- Guarantees all events for a given conversation land on the same partition
  in ingestion order — your first defence against out-of-order delivery
- Rule of thumb: num_partitions = 2x your peak consumer count so you have
  headroom to scale without repartitioning

### Topic Config
```
Topic:              conversation-events
Partitions:         64
Replication factor: 3
Retention:          24h  (allows replay / backfill)
Compression:        snappy
```

### Why Retention Matters
- If a consumer crashes mid-grace-window you can replay from the committed
  Kafka offset and reconstruct the buffer without losing events
- Enables the batch reprocessing layer (see Section 8)

---

## 4. Consumer Layer — ConversationMonitor

### What Lives Here
```
ConversationMonitor
├── self.buffers  : dict[str, ConversationBuffer]   # ephemeral, in-memory only
└── self.records  : dict[str, ConversationRecord]   # local cache, backed by Redis
```

### Per-Event Flow
```
Kafka poll() → batch of messages
    |
    for each message:
        |
        1. _get_or_create_buffer(conversation_id)
        |
        2. is_late(timestamp)?
           YES → log warning, skip           (beyond grace window, unrecoverable)
           NO  → push(timestamp) into heap
        |
        3. drain(current_wall_time)
           → pops all timestamps older than (wall_time - grace_period)
           → returns them in ascending order (min-heap guarantee)
        |
        4. for each drained timestamp:
               _process_timestamp()
               → read ConversationRecord (local cache → Redis fallback)
               → compute gap
               → gap > threshold? fire alert, update stats
               → write ConversationRecord back (cache + batched Redis write)
        |
        5. collect and return alerts
```

### Grace Period Tuning
- Set grace_period to your p99 end-to-end producer → Kafka → consumer latency
- Monitor your Kafka consumer lag metrics to validate this number
- If silence_threshold = 5s and p99 lag = 500ms, grace_period = 1-2s is safe
- You are trading alerting latency for event-time correctness

---

## 5. State Management — Redis

### What Goes to Redis
| State              | Redis? | Reason                                              |
|--------------------|--------|-----------------------------------------------------|
| ConversationRecord | YES    | Durable — must survive crashes and rebalances       |
| ConversationBuffer | NO     | Ephemeral — rebuild from Kafka replay on crash      |

### Key Structure
```
Key:   conversation:{conversation_id}
Type:  Redis Hash
TTL:   24h (auto-cleanup of stale conversations)

Fields:
    last_timestamp      int
    total_events        int
    total_alerts_fired  int
    longest_silence     int
```

### Read Path — Local Cache First
```
_process_timestamp()
    |
    check self.records (in-memory dict)
    |
    HIT  → use it directly                  (O(1), no network)
    MISS → GET from Redis → populate cache  (O(1) Redis lookup)
```

### Write Path — Batched for Throughput
Writing to Redis on every single event is correct but expensive at scale.
Instead batch your writes:

```
Strategy A — Write every N events per conversation (e.g. N=10)
Strategy B — Write every M milliseconds (e.g. M=500ms) via a background flush thread
Strategy C — Write on Kafka offset commit (safest, aligns durability with Kafka)
```

Recommended: **Strategy C** — flush dirty records to Redis immediately before
committing the Kafka offset. This way if you crash, you replay from the last
committed offset and your Redis state is consistent with it.

### Tradeoff to State Explicitly
> "We accept a small window of potential stat inaccuracy (total_events etc.)
> in exchange for dramatically lower Redis write pressure. Alerts themselves
> are published immediately and are not batched."

---

## 6. Partition Rebalance Handling

Kafka can reassign partitions between consumers at any time (scale out, crash,
rolling deploy). You must handle this cleanly.

### Kafka Callbacks
```python
def on_partitions_revoked(self, partitions):
    # 1. Flush all dirty ConversationRecords to Redis immediately
    # 2. Clear local self.records cache for conversations on revoked partitions
    # 3. Commit current Kafka offsets
    # This ensures the new owner starts with clean Redis state

def on_partitions_assigned(self, partitions):
    # 1. Clear any stale local cache entries for newly assigned partitions
    # 2. New conversations will be lazily loaded from Redis on first access
```

### Why This Works
- The new consumer reads ConversationRecord from Redis (up to date after flush)
- The new consumer rebuilds ConversationBuffer from scratch (Kafka replay)
- No state is lost, no double-alerting

---

## 7. Alert Publishing

When `_process_timestamp()` detects a silence gap:

```
Alert fired
    |
    Publish to:
    ├── Kafka topic: conversation-alerts   (durable, downstream consumers)
    ├── WebSocket push to supervisor dashboard (real-time UI)
    └── Optional: PagerDuty / webhook for critical thresholds
```

### Exactly-Once Alert Delivery
Naive implementations can double-alert on crash + replay. To prevent this:
- Include a deterministic alert ID: hash(conversation_id + silence_start + silence_end)
- Downstream consumers deduplicate on this ID
- Or use Kafka transactions to atomically commit offset + publish alert

---

## 8. Batch Reprocessing Layer (Lambda Architecture)

The real-time layer optimises for latency but makes bets (grace window).
For analytics and backfill you need a batch layer:

```
Kafka (24h retention)
    |
    v
Batch job (Spark / Flink) — runs every hour
    |
    → reads full event log for each conversation
    → sorts by event timestamp (perfect ordering)
    → recomputes all silences and stats
    → writes corrected results to data warehouse (BigQuery / Redshift)
    → supervisor dashboard shows real-time stats (speed layer)
      AND corrected historical stats (batch layer)
```

This is the **Lambda Architecture** pattern — speed layer for live alerting,
batch layer for correctness over time.

---

## 9. Scaling to 10,000 Concurrent Conversations

| Concern              | Solution                                                  |
|----------------------|-----------------------------------------------------------|
| CPU                  | Horizontal scale — add consumer instances                 |
| Memory               | Each ConversationBuffer is tiny (grace_period is seconds) |
| Redis write pressure | Batched writes (Strategy C above)                        |
| Redis read pressure  | Local cache — Redis only on cache miss                    |
| Kafka throughput     | 64 partitions → 64 max parallel consumers                 |
| Hot partitions       | Monitor partition lag, repartition if one conv dominates  |
| State on rebalance   | Handled by on_partitions_revoked flush                    |

### Back of Envelope
```
10,000 conversations
× 10 events/second average per conversation
= 100,000 events/second total

64 partitions → ~1,560 events/second per partition
Each _process_timestamp() is O(1) → trivially fast per event

Redis writes (batched, Strategy C):
~10,000 writes per Kafka offset commit interval (e.g. every 5s)
= 2,000 Redis writes/second — well within Redis single-node limits (100k+ ops/s)
```

---

## 10. Failure Modes & Mitigations

| Failure                        | Impact                              | Mitigation                                  |
|--------------------------------|-------------------------------------|---------------------------------------------|
| Consumer crash                 | In-flight buffer lost               | Replay from last committed Kafka offset     |
| Redis down                     | Can't read/write ConversationRecord | Local cache keeps processing, queue writes  |
| Kafka partition rebalance      | State moves between consumers       | on_partitions_revoked flush to Redis        |
| Late event beyond grace window | Event dropped, gap miscalculated    | Batch layer corrects in hindsight           |
| Alert double-publish on replay | Supervisor sees duplicate alert     | Deterministic alert ID + deduplication      |

---

## 11. Key Talking Points Summary

1. **Partition by conversation_id** — Kafka ordering as first defence
2. **Watermark buffer** — grace period buys time for late event reordering
3. **Redis backed by local cache** — durability without per-event network cost
4. **Flush on offset commit** — aligns Kafka and Redis consistency boundaries
5. **on_partitions_revoked** — clean state handoff on rebalance
6. **Deterministic alert IDs** — idempotent alert delivery on replay
7. **Lambda Architecture** — speed layer for alerting, batch layer for correctness
8. **Grace period tuned to p99 lag** — practical, measurable, not arbitrary
