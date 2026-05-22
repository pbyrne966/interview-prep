# Task Dispatcher — System Design

## 1. High Level Architecture

```mermaid
graph TD
    A[Mobile / Web Clients] -->|HTTP / WebSocket| B[API Gateway]
    B -->|Publish task event| C[Kafka - task-created topic]
    C -->|Consume| D[Task Dispatcher Service]
    D -->|Read / Write Agent State| E[Redis Cluster]
    D -->|Publish assignment event| F[Kafka - task-assigned topic]
    F -->|Consume| G[Supervisor Dashboard]
    F -->|Consume| H[Agent Notification Service]
    H -->|Push notification| I[Agent Desktop / Mobile]
    D -->|Persist all events| J[PostgreSQL / Event Store]
```

---

## 2. Task Dispatcher Service Internals

```mermaid
graph TD
    A[Kafka Consumer - poll] --> B[record_event]
    B --> C{Task Type?}
    C -->|assign_task| D[Pop from Agent Heap]
    C -->|complete_task| E[Push updated tuple back]
    D --> F{Stale Entry?}
    F -->|Yes - discard| D
    F -->|No - valid| G[Update Agent State]
    G --> H[Write to Redis]
    G --> I[Publish to task-assigned topic]
    E --> H
```

---

## 3. Agent State — Read / Write Path

```mermaid
flowchart TD
    A[assign_task called] --> B{agent_lookup cache hit?}
    B -->|Yes| C[Use local cache]
    B -->|No| D[Read from Redis]
    D --> E[Populate local cache]
    C --> F[Compute assignment]
    E --> F
    F --> G[Update local cache]
    G --> H{Offset commit time?}
    H -->|Yes| I[Flush dirty records to Redis]
    H -->|No| J[Keep in local cache]
```

---

## 4. Partition Rebalance Handling

```mermaid
sequenceDiagram
    participant K as Kafka
    participant C1 as Consumer A
    participant C2 as Consumer B
    participant R as Redis

    K->>C1: on_partitions_revoked
    C1->>R: Flush all dirty Agent state
    C1->>K: Commit offsets
    K->>C2: on_partitions_assigned
    C2->>R: Load Agent state for new partitions
    C2->>K: Resume consuming
```

---

## 5. Priority Task Extension

```mermaid
flowchart TD
    A[assign_task called with priority] --> B[Push onto Priority Task Heap]
    B --> C{Agent available?}
    C -->|Yes| D[Pop highest priority task from heap]
    C -->|No| E[Task sits in pending heap]
    D --> F[Assign to least busy agent]
    F --> G[Publish assignment event]
    E --> H{Agent completes task?}
    H -->|Yes - slot freed| C
```

---

## 6. Failure Modes

```mermaid
flowchart TD
    A[Consumer Crash] --> B[Replay from last Kafka offset]
    B --> C[Rebuild in-memory heap from Redis]

    D[Redis Down] --> E[Local cache keeps processing]
    E --> F[Queue writes to Redis]
    F --> G[Flush when Redis recovers]

    H[Task double assigned on replay] --> I[Deterministic task ID]
    I --> J[Deduplicate downstream]

    K[Agent overloaded] --> L[capacity check before assign]
    L --> M[Raise ValueError - queue task as pending]
```

---

## 7. Scaling

```mermaid
flowchart LR
    A[10k Concurrent Tasks] --> B[64 Kafka Partitions]
    B --> C[Partition by agent_pool_id]
    C --> D[Consumer Group - N instances]
    D --> E[Each instance owns subset of partitions]
    E --> F[Local heap per instance]
    F --> G[Redis shared state across instances]
    G --> H[On rebalance - flush to Redis, reload on assign]
```
