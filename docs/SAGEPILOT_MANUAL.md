# 🚀 SagePilot: Professional Usage Manual

This manual provides a comprehensive guide to running and using the SagePilot Order Supervisor agentic system.

---

## 🏗️ 1. Setup & Installation

Ensure you have the following prerequisites:
- **Temporal CLI**: Installed and available in PATH.
- **Python 3.10+**: With a virtual environment (`.venv`) initialized.
- **Google API Key**: A valid Gemini key in `backend/.env`.

### Environment Configuration
Your `backend/.env` should look like this:
```env
TEMPORAL_HOST=localhost:7233
GOOGLE_API_KEY=YOUR_GEMINI_API_KEY
DATABASE_URL=sqlite:///./sagepilot.db
```

---

## 🚦 2. Starting the System

The easiest way to start everything is using the provided `dev.py` script. It orchestrates the Temporal server, the Backend API, the AI Worker, and the Next.js Frontend.

```powershell
.\.venv\Scripts\python.exe dev.py
```

**Wait for these signals in the logs:**
*   `✅ Temporal start-dev signal sent.`
*   `✅ SERVER is running at http://localhost:8000`
*   `✅ WORKER is starting...`
*   `✅ UI Ready in ...`

---

## 🛠️ 3. Using the Dashboard

1.  Open [http://localhost:3000](http://localhost:3000) in your browser.
2.  **Create a New Supervisor**:
    - Enter an Order ID (or leave blank for a random one).
    - Select a **Personality Template** (e.g., Aggressive Logistician).
    - Click **Start Simulation**.
3.  **Monitor the Agent**:
    - The **Intelligence Trace** card will show the agent's real-time monologues and confidence scores.
    - The **Order Timeline** shows every event (customer signals, logistics updates).
    - The **Action Log** shows tools being executed by the AI (e.g., messaging teams).

---

## 🧪 4. Testing End-to-End Robustness

### Injecting Live Instructions
You can steer the agent in real-time. 
*   *Example*: Type *"Prioritize customer satisfaction over cost"* in the instruction box. 
*   The agent will acknowledge this in its next Monologue.

### Simulating Events
Use the "Send Event" buttons to simulate order lifecycle changes:
- `payment_received`: Signals the agent to begin fulfillment.
- `inventory_checked`: Updates the agent on stock status.
- `label_printed`: Informs the agent that logistics is ready.

### Autonomous Closure
The system is designed to close itself when the order is "Delivered". 
1. Send all progress events.
2. Finally, send `order_delivered`.
3. Watch the agent call `close_workflow` and generate the **Final Completion Summary**.

---

## 🛡️ 5. Professional Guardrails
The system includes two critical professional-grade guardrails:
1.  **Tool Whitelisting**: If the agent attempts a tool not in the allowed list, the system rejects it. 
2.  **Signal Buffering**: Even if you spam events, the system snapshots them correctly, ensuring no data loss during "thinking" cycles.

---

## 📈 6. Observability
- **Temporal Web UI**: Visit [http://localhost:8233](http://localhost:8233) to see the underlying workflow state machine and event history.
- **Trace IDs**: Check the Backend console for `[TRACE:xxxx]` logs to track every user request through the system.
