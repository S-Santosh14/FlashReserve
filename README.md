# FlashReserve

FlashReserve is a distributed ticket booking system built using **Python, Streamlit, MongoDB, REST APIs, gRPC, and the Raft Consensus Algorithm**.

The application supports two modes:

- **Normal Mode:** Uses a standalone MongoDB database.
- **Raft Mode:** Uses a distributed cluster of seven Raft nodes to handle event operations and bookings through a leader.

The application also includes an LLM-based support service, booking confirmations, cancellation notifications, and a Raft cluster monitoring interface.

---

## 1. Prerequisites

Make sure the following are installed:

- Python (3.11 or compatible version)
- MongoDB Atlas account or a MongoDB deployment supporting transactions
- Git
- Required environment variables configured in `.env`

## 2. Project Setup (Windows)

Open the project folder in the terminal.

**Step 1: Create a virtual environment**

```bash
py -3.11 -m venv venv
```

Replace `3.11` with your installed Python version if necessary.

**Step 2: Activate the virtual environment**

```powershell
.\venv\Scripts\Activate.ps1
```

**Step 3: Install dependencies**

```bash
python -m pip install --no-cache-dir -r requirements.txt
```

**Step 4: Configure environment variables**

Create a `.env` file in the project root directory.

Configure the following:

- `MONGODB_URI`
- `STANDALONE_DB_NAME`
- `JWT_SECRET`
- Raft node MongoDB URIs and database names
- Raft node addresses and ports
- `GROQ_API_KEY` and `GROQ_MODEL` (for LLM responses)
- SMTP credentials (for booking emails)

Refer to `.env.example` for the complete configuration.

**Important:**
- Each Raft node must have its own MongoDB database.
- All seven nodes must use the same cluster size.
- Use an odd cluster size (7 in this project).
- Never commit your `.env` file to GitHub.

---

## 3. Running the Application

Each service must run in a **separate terminal**.

Keep the virtual environment activated in every terminal.

### Terminal 1: Streamlit Frontend

```bash
python -m streamlit run app.py --server.headless true --server.port 8502
```

Open the application at:

`http://localhost:8502`

### Terminal 2: REST Backend

```bash
./venv/Scripts/python.exe -m backend.main
```

The backend provides the REST APIs for Normal Mode and the Raft gateway.

### Terminal 3: LLM Support Service

```bash
./venv/Scripts/python.exe -m llm.llm_service
```

The LLM service uses Groq for AI-powered responses.

If Groq is unavailable or not configured, the service provides an FAQ-based fallback.

---

## 4. Starting the Raft Cluster

FlashReserve uses seven independent Raft nodes.

**Important:** Start each node in a separate terminal.

Run the following commands individually:

**Terminal 4: Node 1**

```bash
./venv/Scripts/python.exe -m backend.raft.node_runner --node node-1
```

**Terminal 5: Node 2**

```bash
./venv/Scripts/python.exe -m backend.raft.node_runner --node node-2
```

**Terminal 6: Node 3**

```bash
./venv/Scripts/python.exe -m backend.raft.node_runner --node node-3
```

**Terminal 7: Node 4**

```bash
./venv/Scripts/python.exe -m backend.raft.node_runner --node node-4
```

**Terminal 8: Node 5**

```bash
./venv/Scripts/python.exe -m backend.raft.node_runner --node node-5
```

**Terminal 9: Node 6**

```bash
./venv/Scripts/python.exe -m backend.raft.node_runner --node node-6
```

**Terminal 10: Node 7**

```bash
./venv/Scripts/python.exe -m backend.raft.node_runner --node node-7
```

Wait until the nodes establish communication and elect a leader.

The cluster requires a majority of nodes (4 out of 7) to maintain quorum and commit operations.

The frontend communicates with the REST gateway. It does not communicate directly with the Raft nodes' gRPC ports.

---

## 5. Booking and Notification System

- Users can register and log in.
- Users can browse events and book tickets.
- Mock payment processing is used to confirm bookings.
- Booking confirmation emails are queued after successful payment.
- Cancellation emails are queued after successful cancellation.
- Email notifications use SMTP with STARTTLS.

Configure SMTP credentials in `.env` to enable email notifications.

The email delivery system uses a shared MongoDB notification outbox.

---

## 6. Important Notes

- Normal Mode and Raft Mode maintain separate event catalogues.
- Events created in one mode are not automatically available in the other mode.
- User accounts and authentication are shared between both modes.
- Raft operations require majority commitment and leader application.
- MongoDB transactions are required for booking and payment operations.
- All seven Raft nodes require their respective MongoDB databases to be accessible.
- Booking timestamps are displayed in Indian Standard Time (IST).

**Limitations:**

- Payment processing is currently mocked.
- SMTP acceptance does not guarantee inbox delivery.
- Raft snapshot installation is not implemented.
- The project is intended for academic and development purposes, not production ticketing.

---

## 7. Running Tests

To execute the project tests:

```bash
run_tests.bat
```

The tests use mock databases and do not modify the configured MongoDB database or send actual emails.

---

## 8. Project Documentation

For additional technical details, refer to:

- `docs/architecture-audit.md`
- `docs/migration-recovery-report.md`
- `docs/implementation-report.md`

---