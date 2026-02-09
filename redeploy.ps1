# Redeploy RepoRoast

$projectId = "gen-lang-client-0614247645"
$imageName = "gcr.io/$projectId/reporoast"
$serviceName = "reporoast"
$region = "us-central1"

# Environment variables (Please set these in your local environment or .env file)
# $env:SECRET_KEY = "your-secret-key"
# $env:GOOGLE_API_KEY = "your-google-api-key"
# $env:GOOGLE_CLOUD_TTS_JSON = '{"type":"service_account", ...}'

Write-Host "1. Building new image..."
& "C:\Users\D.SAI CHARAN\AppData\Local\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd" builds submit --tag $imageName

if ($LASTEXITCODE -ne 0) {
    Write-Host "Build failed!"
    exit 1
}

# Create temporary environment file to avoid shell quoting issues
$envFile = "env_vars.yaml"
$envContent = @"
SECRET_KEY: "$env:SECRET_KEY"
GOOGLE_API_KEY: "$env:GOOGLE_API_KEY"
GOOGLE_CLOUD_TTS_JSON: '$env:GOOGLE_CLOUD_TTS_JSON'
"@
Set-Content -Path $envFile -Value $envContent

Write-Host "2. Deploying to Cloud Run..."
& "C:\Users\D.SAI CHARAN\AppData\Local\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd" run deploy $serviceName `
  --image $imageName `
  --platform managed `
  --region $region `
  --allow-unauthenticated `
  --memory 2Gi `
  --timeout 300 `
  --env-vars-file $envFile

# Cleanup
Remove-Item -Path $envFile -ErrorAction SilentlyContinue

Write-Host "Done! Check URL."
