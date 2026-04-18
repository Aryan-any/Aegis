# Aegis Order Supervisor: Technical Specification

## 1. Overview
The **Aegis Order Supervisor** is a production-grade autonomous agentic system designed to manage long-running business lifecycles—specifically e-commerce orders—through durable orchestration and generative reasoning.

### The Problem
Traditional automated systems often fail in complex, multi-step business processes due to:
1.  **Transient Execution**: Standard microservices lose state during server restarts or network partitions.
2.  **Rigidity**: Rule-based systems cannot handle the "fuzzy" edge cases of human interaction (e.g., a customer providing a vague update about a shipment delay).
3.  **Observability Gaps**: Difficulty in auditing why a particular decision was made by an autonomous system.

Aegis solves this by treating every order as a **durable entity workflow** that combines the reliability of **Temporal** with the strategic reasoning of **Large Language Models (LLMs)**.

---

## 2. Requirements Analysis

### Functional Requirements
- **One Workflow per Order**: Every order must be backed by a single, unique Temporal workflow instance.
- **Triple-Trigger Support**: The system must react to (1) Initial creation, (2) External signals (events), and (3) Scheduled timers.
- **Autonomous Reasoning**: An agent must evaluate the system state and determine the next best action following a structured JSON schema.
- **Persistence**: All events, internal monologues, and tool executions must be logged for auditing.
- **Deterministic Completion**: Termination must follow system-defined rules (e.g., successful delivery) rather than raw agent termination.

### Constraints & Expectations
- **Reliability**: Workflows must be able to "sleep" for extended periods without consuming active compute resources.
- **Guardrails**: Tool execution must be restricted to a predefined whitelist.
- **Aesthetics**: The user interface must provide a high-fidelity, professional-grade monitoring experience.

---

## 3. System Design & Architecture

The system utilizes a modern event-sourced architecture divided into four primary layers:

### A. Coordination Layer (Temporal)
The core of the system is the `OrderWorkflow`. It serves as the "Durable Brain," managing the state machine and ensuring that even if the entire infrastructure crashes, the mission resumes exactly where it stopped.

### B. Intelligence Layer (Agent Runtime)
This layer manages the interaction with LLMs (Google Gemini Pro / Flash). It transforms raw workflow state into a structured prompt, parses the model's reasoning, and enforces strict JSON schema adherence through Pydantic.

### C. Execution Layer (FastAPI & Activities)
The backend provides a RESTful API for external systems to inject signals. Activities perform the "side-effect" work, such as sending messages to customers or logistics teams, while ensuring idempotency.

### D. Observation Layer (Next.js)
A high-density dashboard provides real-time visibility. It uses a "Lumina" design aesthetic to present complex telemetry (strategic traces, audit trails, and performance metrics) in a professional command-center format.

---

## 4. Implementation Details

### Workflow Mechanics (`OrderWorkflow`)
The workflow is implemented using an asynchronous loop that waits on three conditions:
1.  **`add_event` Signal**: Injected when external state changes (e.g., `shipment_delayed`).
2.  **`add_instruction` Signal**: Injected when a human supervisor provides a directive.
3.  **`wait_condition` Timer**: A deterministic sleep period determined by the agent or system rules.

**Key Logic Fragment:**
```python
while not self._exit:
    # 1. State Capture & Snapshotting
    events_to_process = list(self._state.events)
    
    # 2. Agent Execution (Internal Monologue)
    decision = await workflow.execute_activity(execute_agent, state_dict)
    
    # 3. Tool Dispatch
    if decision["should_act"]:
        await workflow.execute_activity(call_tool, tool_params)
        
    # 4. Deterministic Termination check
    if any(e.event_type in COMPLETION_EVENTS for e in events_to_process):
        self._exit = True
```

### Agent Design & Decision Making
The agent is stateless, receiving the full history of the order in every reasoning cycle.
- **Structured JSON**: Enforced via `response_mime_type="application/json"`.
- **System Prompt**: Defines the agent's "Aegis" personality, emphasizing cost-efficiency, speed, and standard operating procedures (SOPs).
- **Circuit Breakers**: Implemented to handle LLM rate limits (429 errors), falling back to a deterministic rule-engine if necessary to prevent mission stalling.

### Memory & Timeline Handling
- **Memory Summary**: The agent maintains a "rolling summary" of its strategic context, which is persisted across workflow iterations.
- **Action Log**: Every tool execution is recorded in a centralized `ActionLog` table via `SQLModel`, allowing for a historical "Rewind" of decisions.

### Tools & Activities
Every tool call is wrapped in a Temporal Activity. The `ALLOWED_ACTIONS` whitelist currently includes:
- `message_fulfillment_team`
- `message_customer`
- `create_internal_note`
- `close_workflow` (System use)

---

## 5. Key Decisions & Trade-offs

### 1. Choice of Temporal vs. standard CRON
- **Decision**: Used Temporal for all long-running logic.
- **Rationale**: standard queues (Celery/SQS) struggle with local state maintenance over multi-day lifecycles. Temporal provides native state persistence and deterministic retries.

### 2. Event Snapshotting vs. Clear-on-Process
- **Decision**: Added atomic list clearing after snapshotting.
- **Rationale**: Prevents race conditions where a signal arrives *precisely* while the agent is reasoning. New events are buffered for the next cycle.

### 3. Decoupled Termination
- **Decision**: Moved termination logic from the Agent to the Workflow rules.
- **Rationale**: An agent might prematurely close a mission based on a misunderstanding. By tying closure to deterministic events (e.g., `delivered`), we maintain system safety.

---

## 6. How It Works (End-to-End Flow)

1.  **Initialization**: An order is created. FastAPI initiates the `OrderWorkflow` with a unique ID.
2.  **Reasoning**: The workflow wakes up, captures state, and sends it to the Agent logic. The agent suggests a 10-minute wait (Wait Timer).
3.  **Signaling**: A logistics partner sends an `inventory_checked` signal. The workflow wakes up immediately, bypassing the timer.
4.  **Acting**: The agent recognizes the inventory update and triggers the `message_fulfillment_team` tool to prepare shipping.
5.  **Completion**: A `delivered` signal is received. The workflow logic detects this, breaks the reasoning loop, generates a **Final Retrospective Summary**, and terminates gracefully.

---

## 7. Additional Considerations

### Edge Cases Handled
- **LLM Failover**: If the primary LLM provider fails, the system switches to a secondary "Fallback Agent" (deterministic logic) to ensure the order remains in an active state.
- **Stuck-in-Loop Detection**: The workflow monitors for repeated identical actions. If detected, it forces a "Cool Down" timer to prevent resource exhaustion.

### Limitations
- **External Dependency**: High reliance on LLM availability for strategic decisions.
- **Linear Processing**: Events within a single order are processed sequentially in the reasoning loop.

### Future Improvements
- **Multi-Agent Collaboration**: Introducing specialized sub-agents for financial vs. logistics auditing.
- **Real-Time Webhooks**: Direct integration with carrier APIs (UPS/FedEx) for automatic signal injection.

---
*Document Version: 1.2.0*  
*Author: Aegis Systems Engineering Team*
