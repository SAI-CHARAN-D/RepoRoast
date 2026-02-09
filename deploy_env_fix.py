import os
import subprocess
import yaml
import json

# Configuration
PROJECT_ID = "gen-lang-client-0614247645"
SERVICE_NAME = "reporoast"
REGION = "us-central1"
GCLOUD_CMD = r"C:\Users\D.SAI CHARAN\AppData\Local\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd"

print(f"1. Exporting current config for {SERVICE_NAME}...")
export_cmd = [
    GCLOUD_CMD, "run", "services", "describe", SERVICE_NAME,
    "--project", PROJECT_ID,
    "--region", REGION,
    "--format", "yaml"
]

try:
    result = subprocess.run(export_cmd, check=True, capture_output=True, text=True)
    config = yaml.safe_load(result.stdout)
    
    # 2. Modify config
    print("2. Injecting environment variables...")
    
    # helper to read .env
    env_vars = {}
    with open(".env", "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"): continue
            try:
                k, v = line.split("=", 1)
                if k in ["SECRET_KEY", "GOOGLE_API_KEY", "GOOGLE_CLOUD_TTS_JSON"]:
                    env_vars[k] = v
            except: continue
            
    # Locate the container spec (usually spec.template.spec.containers[0])
    containers = config['spec']['template']['spec']['containers']
    
    # Update env vars in the first container
    if 'env' not in containers[0]:
        containers[0]['env'] = []
        
    # Remove existing keys we are about to update
    containers[0]['env'] = [item for item in containers[0]['env'] if item['name'] not in env_vars]
    
    # Add new keys
    for k, v in env_vars.items():
        containers[0]['env'].append({'name': k, 'value': v})
        
    # Remove status and redundant metadata to allow clean replace
    if 'status' in config: del config['status']
    if 'metadata' in config:
        # Keep only name, namespace, labels, annotations
        allowed_meta = ['name', 'namespace', 'labels', 'annotations']
        config['metadata'] = {k: v for k, v in config['metadata'].items() if k in allowed_meta}

    # 3. Save modified config
    service_yaml = "service.yaml"
    with open(service_yaml, "w") as f:
        yaml.dump(config, f)
        
    print(f"3. Applying new configuration from {service_yaml}...")
    apply_cmd = [
        GCLOUD_CMD, "run", "services", "replace", service_yaml,
        "--project", PROJECT_ID,
        "--region", REGION
    ]
    
    apply_result = subprocess.run(apply_cmd, check=True, capture_output=True, text=True)
    print("\n✅ Service updated successfully!")
    # print(apply_result.stderr) # gcloud often writes info to stderr

except subprocess.CalledProcessError as e:
    print("\n❌ Operation failed!")
    print(e.stderr)
finally:
    if os.path.exists("service.yaml"):
        os.remove("service.yaml")
        print("Cleaned up temporary file.")
