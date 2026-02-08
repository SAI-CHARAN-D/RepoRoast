# 🔥 RepoRoast

**Turn GitHub repositories into roast-style podcasts.**

RepoRoast analyzes any public GitHub repository and generates a natural-sounding podcast where two AI voices discuss the codebase—one roasts the architecture, the other explains the trade-offs. Think *senior engineers reviewing code over coffee*, delivered as audio.

Built for **Google AI Hackathon** (Firebase Track).

---

## ✨ What It Does

1. **📥 Paste a GitHub URL** → We clone and analyze the full repository
2. **🎙️ Listen First** → Get a 60-second roast-style podcast with male/female AI voices
3. **📊 Visual Proof** → Auto-generated architecture diagram referenced in the audio
4. **🧭 Guided Learning** → Developer guide showing what to read first, what to skip, and known risks

---

## 🎯 The Problem

Junior developers waste **days** clicking through 50,000-line codebases trying to build a mental model. By the time they understand the architecture, they've forgotten why they needed to know it.

## 💡 The Solution

**Listen first, read later.** RepoRoast lets you understand architecture through conversation—the way senior engineers already learn systems. Spend 60 seconds listening, then know exactly what to read and why.

---

## 🛠️ Tech Stack

- **Backend:** Flask, Gunicorn
- **AI:** Google Gemini 3 Pro Preview
- **TTS:** Google Cloud Text-to-Speech (Studio voices with SSML)
- **Frontend:** HTML, Tailwind CSS, Vanilla JS
- **Deployment:** Docker, Google Cloud Run

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Git
- Google Gemini API key
- Google Cloud TTS credentials

### Local Setup

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/RepoRoast.git
cd RepoRoast

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment variables
cp .env.example .env
# Edit .env with your API keys

# Run development server
python -m flask --app "app.factory:create_app" run --debug --port 5000
```

Visit `http://localhost:5000`

---

## 🌐 Deployment

### Docker
```bash
docker-compose up --build
```

### Google Cloud Run
```bash
gcloud builds submit --tag gcr.io/YOUR_PROJECT/reporoast
gcloud run deploy reporoast --image gcr.io/YOUR_PROJECT/reporoast --platform managed
```

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed instructions.

---

## 🔑 Environment Variables

```bash
SECRET_KEY=your-secret-key
GOOGLE_API_KEY=your-gemini-api-key
GOOGLE_CLOUD_TTS_JSON={"type":"service_account",...}
```

See `.env.example` for full template.

---

## 🎨 Features

- ✅ **Audio-First Experience** - Natural male/female dialogue with 1s pauses
- ✅ **SSML Prosody** - Rate control for speaker personality
- ✅ **Architecture Diagrams** - Mermaid diagrams with error handling
- ✅ **Code Viewer** - GitHub-style file browser for transparency
- ✅ **Download Reports** - Exportable guides and scripts
- ✅ **No Markdown in Speech** - Clean audio without "backquote" artifacts

---

## 📁 Project Structure

```
RepoRoast/
├── app/
│   ├── services/        # AI, TTS, GitHub ingestion
│   ├── templates/       # HTML pages
│   ├── static/         # CSS, JS, generated audio
│   └── routes.py       # Flask endpoints
├── DEPLOYMENT.md       # Deployment guide
├── requirements.txt    # Python dependencies
├── gunicorn_config.py  # Production WSGI config
├── Dockerfile          # Container config
└── docker-compose.yml  # Local container setup
```

---

## 🧪 How It Works

1. **Clone & Analyze** - Full repository structure scan
2. **Generate Insights** - AI creates dialogue, diagram, and guide
3. **Synthesize Audio** - Google Cloud TTS with SSML
4. **Listen & Learn** - Audio-first understanding

---

## 📊 Architecture

- **Entry Point:** `app/factory.py`
- **Services:** Modular (AI, TTS, GitHub, Blueprint)
- **Caching:** Disabled for fresh generation
- **Error Handling:** Graceful degradation for Mermaid/TTS failures

---

## 🤝 Contributing

This is a hackathon project built for demonstration. If you'd like to extend it:

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

---

## 📝 License

MIT License - See LICENSE file for details

---

## 🏆 Built For

**Google AI Hackathon** - Firebase Track  
Demonstrating audio-first architecture learning with Google Gemini & Cloud TTS

---

## 🔗 Live Demo

[Add your deployed URL here]

---

**Made with ❤️ and AI**
