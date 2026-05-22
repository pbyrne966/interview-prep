# ============================================================
#  CRESTA CHALLENGE 06 — Task Dispatcher
#  Assign incoming tasks to the least busy agent
# ============================================================
#
# BACKGROUND
# ----------
# Cresta routes incoming customer conversations to live agents.
# Each agent has a capacity — the maximum number of concurrent
# tasks they can handle. When a new task arrives it should
# always be assigned to the agent who currently has the most
# available capacity (i.e. the least busy one).
#
# WHAT YOU NEED TO BUILD
# ----------------------
# A class called TaskDispatcher with the following interface:
#
#   class TaskDispatcher:
#       def __init__(self, agents: list[tuple[str, int]]) -> None:
#           """
#           agents: list of (agent_id, capacity) tuples
#           e.g. [("agent-1", 3), ("agent-2", 2)]
#           """
#
#       def assign_task(self, task_id: str) -> str:
#           """
#           Assign task_id to the least busy agent.
#           Returns the agent_id the task was assigned to.
#           Raises ValueError if no agents have any capacity left.
#           """
#
#       def complete_task(self, task_id: str) -> None:
#           """
#           Mark task_id as complete, freeing up a slot on the
#           agent it was assigned to.
#           Raises ValueError if task_id is not recognised.
#           """
#
#       def get_status(self, agent_id: str) -> dict | None:
#           """
#           Returns None if agent_id is not recognised.
#           Otherwise returns:
#           {
#               "agent_id":          str,
#               "capacity":          int,   # total capacity
#               "active_tasks":      int,   # currently assigned tasks
#               "available_slots":   int,   # capacity - active_tasks
#           }
#           """
#
# RULES & EDGE CASES
# ------------------
# 1. If two agents have equal available slots, break the tie
#    by choosing the agent with the LOWER agent_id (alphabetically).
#
# 2. An agent with 0 available slots must never be assigned a task.
#
# 3. complete_task() must free exactly one slot on the correct agent.
#
# 4. The same task_id can be reused after it has been completed.
#
# 5. assign_task() should be as efficient as possible —
#    think about what data structure gives you the least busy
#    agent in O(log n).
#
# HINT
# ----
# Think about what data structure you used in the Meeting Rooms
# challenge... it works here too, just inverted.
# You want the agent with the MOST available slots at the top.
# ============================================================

import heapq
from enum import Enum
from threading import Lock

from pydantic import BaseModel


class TaskStatus(Enum):
    in_progress = "in_progress"
    pending = "pending"
    comepleted = "completed"


class Agent(BaseModel):
    agent_id: str
    capacity: int
    original_capacity: int
    agent_name: str | None = None
    active_tasks: int = 0
    current_tasks: int = 0

    def __lt__(self, other: "Agent"):
        if self.capacity != other.capacity:
            return self.capacity > other.capacity
        return self.agent_id < other.agent_id


class AgentTask(BaseModel):
    task_id: str
    agent_id: str
    task_name: str | None = None
    task_complete: bool = False
    task_status: TaskStatus = TaskStatus.pending


class TaskDispatcher:
    def __init__(self, agents: list[tuple[str, int]]) -> None:
        self.registered_tasks: dict[str, AgentTask] = {}
        # Here we can also heapify tasks based of their prioty
        self.pending_tasks: dict[str, AgentTask] = {}
        self.agent_look_up: dict[str, Agent] = {}
        self.lock = Lock()

        # Make this so it can be min heaped brother
        self.agents = []

        for agent, capacity in agents:
            agent = Agent(agent_id=agent, capacity=capacity, original_capacity=capacity)
            heapq.heappush(self.agents, (-capacity, agent.agent_id))
            self.agent_look_up[agent.agent_id] = agent

    def assign_task(self, task_id: str) -> str:
        with self.lock:
            while self.agents:
                neg_slots, agent_id = heapq.heappop(self.agents)
                agent = self.agent_look_up[agent_id]
                if -neg_slots != agent.capacity:
                    continue

                if agent.capacity == 0:
                    raise ValueError("No Agent is available")

                task = AgentTask(task_id=task_id, agent_id=agent_id)
                self.registered_tasks[task_id] = task
                agent.capacity -= 1
                agent.active_tasks += 1
                heapq.heappush(self.agents, (-agent.capacity, agent_id))
                return agent_id

            raise ValueError("Broke Out of loop with no agent assined")

    def complete_task(self, task_id: str) -> None:
        with self.lock:
            if task_id not in self.registered_tasks.keys():
                raise ValueError("Task not recognised")
            task = self.registered_tasks[task_id]
            agent = self.agent_look_up[task.agent_id]
            agent.capacity += 1
            agent.active_tasks -= 1
            heapq.heappush(self.agents, (-agent.capacity, agent.agent_id))

    def get_status(self, agent_id: str) -> dict | None:
        if agent_id not in self.agent_look_up.keys():
            return None
        with self.lock:
            agent = self.agent_look_up[agent_id]
            return {
                "agent_id": agent.agent_id,
                "capacity": agent.original_capacity,
                "active_tasks": agent.active_tasks,
                "available_slots": agent.original_capacity - agent.active_tasks,
            }


# ------------------------------------------------------------
# Tests
# ------------------------------------------------------------

if __name__ == "__main__":
    results = []

    def check(label: str, got, expected) -> None:
        ok = got == expected
        results.append(ok)
        print(f"[{'PASS' if ok else 'FAIL'}] {label}")
        if not ok:
            print(f"       got:      {got!r}")
            print(f"       expected: {expected!r}")

    # Basic assignment — agent-1 has more capacity so gets task first
    d = TaskDispatcher([("agent-1", 3), ("agent-2", 1)])
    check("assign to most available", d.assign_task("task-1"), "agent-1")

    # agent-1 now has 2 slots, agent-2 has 1 — still agent-1
    check("assign second task to agent-1", d.assign_task("task-2"), "agent-1")

    # agent-1 has 1 slot, agent-2 has 1 slot — tie break by agent_id
    check("tie break by agent_id", d.assign_task("task-3"), "agent-1")

    # agent-1 full, agent-2 has 1 slot
    check("agent-1 full, assign to agent-2", d.assign_task("task-4"), "agent-2")

    # Both agents full — should raise ValueError
    try:
        d.assign_task("task-5")
        results.append(False)
        print("[FAIL] no capacity — should have raised ValueError")
    except ValueError:
        results.append(True)
        print("[PASS] no capacity raises ValueError")

    # Complete a task and free up a slot
    d.complete_task("task-1")
    check("after complete, assign freed slot", d.assign_task("task-5"), "agent-1")

    # complete_task with unknown task_id raises ValueError
    try:
        d.complete_task("unknown-task")
        results.append(False)
        print("[FAIL] unknown task_id — should have raised ValueError")
    except ValueError:
        results.append(True)
        print("[PASS] unknown task_id raises ValueError")

    # get_status for known agent
    d2 = TaskDispatcher([("agent-A", 2)])
    d2.assign_task("t1")
    check(
        "get_status known agent",
        d2.get_status("agent-A"),
        {"agent_id": "agent-A", "capacity": 2, "active_tasks": 1, "available_slots": 1},
    )

    # get_status for unknown agent returns None
    check("get_status unknown agent", d2.get_status("ghost"), None)

    print(f"\n{sum(results)}/{len(results)} tests passed")
