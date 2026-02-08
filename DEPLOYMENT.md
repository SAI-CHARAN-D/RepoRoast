# RepoRoast - Deployment Guide

## 🚀 Quick Start (Local)

```bash
# 1. Clone and setup
git clone <your-repo-url>
cd RepoRoast

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Setup environment variables
cp .env.example .env
# Edit .env with your API keys

# 5. Run development server
python -m flask --app "app.factory:create_app" run --debug --port 5000
```

---

## 📋 Prerequisites

1. **Python 3.11+**
2. **Google Gemini API Key** - Get from [Google AI Studio](https://makersuite.google.com/app/apikey)
3. **Google Cloud TTS Credentials** - Service account key from [Firebase Console](https://console.firebase.google.com/)

---

## 🔑 Environment Variables

Create a `.env` file with the following:

```bash
# Required
SECRET_KEY=your-secret-key-change-this
GOOGLE_API_KEY=your-gemini-api-key
GOOGLE_CLOUD_TTS_JSON={"type":"service_account",...}  # or use next line
# GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json
```

**Getting Google Cloud TTS Credentials:**

1. Go to Firebase Console → Project Settings → Service Accounts
2. Click "Generate New Private Key"
3. Download the JSON file
4. **Option A (Cloud):** Minify JSON to single line and set as `GOOGLE_CLOUD_TTS_JSON`
5. **Option B (Local):** Set `GOOGLE_APPLICATION_CREDENTIALS` to file path

---

## 🌐 Deployment Options

### Option 1: Heroku

```bash
# Install Heroku CLI, then:
heroku create your-app-name
heroku config:set SECRET_KEY="your-secret-key"
heroku config:set GOOGLE_API_KEY="your-api-key"
heroku config:set GOOGLE_CLOUD_TTS_JSON='{"type":"service_account",...}'
git push heroku main
```

### Option 2: Render

1. Connect your GitHub repo to Render
2. Create a new Web Service
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `gunicorn --config gunicorn_config.py "app.factory:create_app()"`
5. Add environment variables in dashboard

### Option 3: Docker

```bash
# Build and run
docker-compose up --build

# Or manually
docker build -t reporoast .
docker run -p 8000:8000 --env-file .env reporoast
```

### Option 4: Google Cloud Run

```bash
# Build and deploy
gcloud builds submit --tag gcr.io/YOUR_PROJECT/reporoast
gcloud run deploy reporoast \
  --image gcr.io/YOUR_PROJECT/reporoast \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GOOGLE_API_KEY="your-key" \
  --set-env-vars SECRET_KEY="your-secret"
```

---

## 🏥 Health Check

Your deployment should expose a health check endpoint:

```
GET /health

Response:
{
  "status": "healthy",
  "service": "reporoast",
  "version": "1.0.0"
}
```

Configure your load balancer to check this endpoint.

---

## ⚙️ Production Configuration

### Gunicorn Settings

Configured in `gunicorn_config.py`:
- **Workers:** `(CPU cores * 2) + 1`
- **Worker Class:** `gevent` (async)
- **Timeout:** `120s` (AI requests can be slow)
- **Port:** `$PORT` or `8000`

### Security

- ✅ HTTPS enforced (handled by platform)
- ✅ Environment variables for secrets
- ✅ No debug mode in production
- ✅ Service account credentials isolated

---

## 🐛 Troubleshooting

### Problem: "TTS: Google Cloud credentials not found"

**Solution:** Ensure `GOOGLE_CLOUD_TTS_JSON` is set correctly:
- Must be valid JSON on single line
- No newlines or extra whitespace
- Check quotes are properly escaped

### Problem: "AI Generation Error"

**Solution:**
- Verify `GOOGLE_API_KEY` is valid
- Check Gemini API quota limits
- Review logs for specific error

### Problem: Port binding errors

**Solution:** 
- Ensure `PORT` environment variable is set
- Check firewall rules
- Verify no other service using the port

---

## 📊 Monitoring

### Logging

Logs go to stdout/stderr. Use platform-specific log aggregation:
- **Heroku:** `heroku logs --tail`
- **Render:** View in dashboard
- **Docker:** `docker logs container-name`
- **GCP:** Cloud Logging

### Metrics to Monitor

- `/health` endpoint uptime
- AI request latency
- TTS synthesis time
- Error rates

---

## 🔐 Security Checklist

- [ ] `SECRET_KEY` is strong and unique
- [ ] `.env` file is in `.gitignore`
- [ ] Service account keys are NOT in code
- [ ] HTTPS is enabled
- [ ] Debug mode is OFF
- [ ] API keys have usage limits set

---

## 📞 Support

For issues, check:
1. Server logs for errors
2. `/health` endpoint status
3. Environment variables are set correctly
4. API key quotas

---

## 🎯 Performance Tips

1. **Caching:** Already disabled for fresh results
2. **Concurrency:** Gunicorn uses gevent for async
3. **Resource Limits:** AI analysis can be CPU/memory intensive
4. **Timeouts:** Set to 120s for long-running AI requests

---

**Ready to deploy!** 🚀
