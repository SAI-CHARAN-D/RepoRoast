# Deploy RepoRoast to Cloud Run

$projectId = "gen-lang-client-0614247645"
$serviceName = "reporoast"
$region = "us-central1"
$image = "gcr.io/$projectId/$serviceName"

# Environment variables
# Please set these in your local environment or .env file
# $env:SECRET_KEY = "your-secret-key"
# $env:GOOGLE_API_KEY = "your-google-api-key"
# $env:GOOGLE_CLOUD_TTS_JSON = '{"type":"service_account", ...}'

# Deploy to Cloud Run
& "C:\Users\D.SAI CHARAN\AppData\Local\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd" run deploy $serviceName `
  --image $image `
  --platform managed `
  --region $region `
  --allow-unauthenticated `
  --memory 2Gi `
  --timeout 300 `
  --update-env-vars SECRET_KEY="$env:SECRET_KEY" `
  --update-env-vars GOOGLE_API_KEY="$env:GOOGLE_API_KEY" `
  --update-env-vars GOOGLE_CLOUD_TTS_JSON="$env:GOOGLE_CLOUD_TTS_JSON"

Write-Host "`n✅ Deployment complete!"
Write-Host "Your app is live at the URL shown above! 🚀"
