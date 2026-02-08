# RepoRoast Architecture Design

## Core Philosophy
**"One Shot, One Kill"** - To ensure consistency and reliability, we will use a single, massive context prompt to generate all creative outputs (Roast script, Architecture diagram source, Developer guide) in one go. This minimizes API costs and ensures the diagram matches the roast logic.

## Full System Pipeline

### 1. User Input (Frontend -> Backend)
- **User Actions**: Submits a `github.com/user/repo` URL.
- **Frontend Validation**: Regex check for valid GitHub URL format before submission.
- **Backend Validation**: Flask route receives the URL, validates accessibility (HEAD request).

### 2. Repository Ingestion (The "Harvester")
- **Cloning**: Use `git clone --depth 1` to a temporary directory `temp/<uuid>`. We do NOT keep history.
- **Filtering**:
    - **Allow**: `.py`, `.js`, `.ts`, `.java`, `.cpp`, `.go`, `.rs`, `.md`, `Dockerfile`, `requirements.txt`, `package.json`.
    - **Deny**: Images, binaries, `.lock` files, `node_modules`, `venv`, `.git/`, test data.
- **Size Check**: If total size > 10MB (text only), truncate largest files or stop ingestion with an error.

### 3. Structural Analysis & Repository Blueprint (Non-AI)
Before touching the LLM, we build a **Blueprint**:
- **Tree Structure**: traverse directories to build a file tree string.
- **Ranked Content**:
    1.  Dependency files (`package.json`, `requirements.txt`) are prioritized.
    2.  `README.md` is prioritized.
    3.  Entry points (`main.py`, `index.js`, `app.py`) are prioritized.
    4.  All other source code.
- **Concatenation**: Combine prioritized content into a single `prompt_context.txt`. Each file block is wrapped:
    ```
    === FILE: src/main.py ===
    [code content]
    === END FILE ===
    ```

### 4. The "RoastMaster" AI Brain (Single Batch Call)
- **Model**: Google Gemini 1.5 Pro (for massive context window).
- **Prompt**: "You are a senior principal engineer who is also a ruthless comedian. Analyze this codebase..."
- **Mandatory JSON Output**:
    ```json
    {
        "status": "success",
        "roast": {
            "title": "The Spaghetti Incident",
            "summary": "This codebase is...",
            "dialogue": [
                {"speaker": "Host", "text": "Welcome to RepoRoast..."},
                {"speaker": "Guest", "text": "I wish I hadn't seen this..."}
            ]
        },
        "diagram": "graph TD; ... (Mermaid syntax)",
        "guide": "# Developer Recovery Plan\n\n...",
        "file_references": ["src/main.py"]
    }
    ```

### 5. Asset Generation
- **Audio (TTS)**: 
    - Parse `roast.dialogue`.
    - Send "Host" lines to Voice A (e.g., 'en-US-Journey-D').
    - Send "Guest" lines to Voice B (e.g., 'en-US-Journey-F').
    - Save as `temp/<uuid>/audio_<index>.mp3`.
- **PDFs**: 
    - Convert `roast` JSON to formatted PDF logic (if feasible in MVP, otherwise HTML print view).
    - Convert `guide` markdown to HTML/PDF.

### 6. Serving (Frontend)
- **Route**: GET `/result/<uuid>`
- **Template**:
    - **Audio Player**: Sequentially plays the generated MP3s.
    - **Transcript**: Displays the dialogue in a chat-like interface.
    - **Diagram**: Renders the `mermaid` string using `mermaid.js`.
    - **Code Viewer**: Clicking a reference opens a modal with that file's content (cached from ingestion step).

---

## Why Flask?
1.  **Stateless Simplicity**: RepoRoast is inherently stateless. A request comes in, data is processed, results are returned, and the temp folder is deleted. We don't need a complex database or user management system.
2.  **Synchronous Processing**: While ingestion can be slow, for a hackathon/MVP, keeping a single HTTP connection open (with adequate timeouts) or using simple polling is easier to implement and debug than a full celery/redis queue system.
3.  **Python Ecosystem**: Direct access to `git`, file system operations, and Google Gemini SDK without context switching.
4.  **Integration**: Jinja2 templates are perfect for generating dynamic reports quickly without a heavy React/Vue build step.

---

## Failure Handling Strategy
- **GitHub Failures**:
    - *Scenario*: Repo private or doesn't exist.
    - *Handling*: Catch `GitCommandError`, return 400 "Repository not accessible".
- **AI Hallucination / JSON Error**:
    - *Scenario*: Model returns invalid JSON or markdown-wrapped JSON.
    - *Handling*: Use a "repair" parser (try `json.loads`, then try stripping markdown code blocks). If strict parsing fails, fallback to a "Technical Difficulties" roast script (hardcoded).
- **Context Limit Exceeded**:
    - *Scenario*: Repo is too massive.
    - *Handling*: The Harvester enforces a strict token/size limit *before* calling AI. Only top-level files and structure are sent if limit is hit.
- **Timeouts**:
    - *Scenario*: Processing takes > 60s.
    - *Handling*: Frontend uses a polling mechanism (HTMX or simple JS fetch loop) checking status endpoints (`/status/<job_id>`) so the browser doesn't time out. Backend sets a max execution time.

---

## Deliverables Checklist
- [ ] Flask Skeleton (Blueprints, Factories)
- [ ] `IngestionService` (Git + Filtering)
- [ ] `GeminiService` (Prompt + Parsing)
- [ ] `TTSService` (Google Cloud Text-to-Speech)
- [ ] Frontend Templates (Tailwind + Mermaid.js)
