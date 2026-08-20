#!/usr/bin/env python3
# Fallback launcher: same observatory stack on a GCP T4 VM (Deep Learning VM
# image ships NVIDIA drivers + docker + nvidia runtime). Use if GCP grants the
# GPU quota before AWS. Requires a GCP service account key with Compute Admin rights.
import base64, io, os, subprocess, sys, tarfile

ZONE = sys.argv[1] if len(sys.argv) > 1 else "us-central1-a"
HERE = os.path.dirname(os.path.abspath(__file__))
GCLOUD = "gcloud"

# package ./stack -> base64
buf = io.BytesIO()
with tarfile.open(fileobj=buf, mode="w:gz") as tar:
    tar.add(os.path.join(HERE, "stack"), arcname="stack")
blob = base64.b64encode(buf.getvalue()).decode()

startup = f"""#!/bin/bash
set -x
mkdir -p /opt/obs && cd /opt/obs
echo {blob} | base64 -d | tar xz
cd /opt/obs/stack
# Deep Learning VM prompts to install driver on first boot; wait for it
for i in $(seq 1 40); do nvidia-smi && break; sleep 10; done
for i in $(seq 1 30); do docker info && break; sleep 5; done
docker compose up -d || docker-compose up -d
"""
sf = "/tmp/obs_startup.sh"
open(sf, "w").write(startup)

cmd = [GCLOUD, "compute", "instances", "create", "llm-observatory",
       "--zone", ZONE, "--machine-type", "n1-standard-4",
       "--accelerator", "type=nvidia-tesla-t4,count=1",
       "--image-family", "common-cu123-debian-11", "--image-project", "deeplearning-platform-release",
       "--maintenance-policy", "TERMINATE", "--boot-disk-size", "100GB",
       "--metadata", "install-nvidia-driver=True",
       "--metadata-from-file", f"startup-script={sf}",
       "--scopes", "cloud-platform"]
print(" ".join(cmd))
subprocess.run(cmd, check=True)
subprocess.run([GCLOUD, "compute", "instances", "describe", "llm-observatory", "--zone", ZONE,
                "--format", "value(networkInterfaces[0].accessConfigs[0].natIP)"])
