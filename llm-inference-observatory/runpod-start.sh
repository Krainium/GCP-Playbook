#!/bin/bash
set -x
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq && apt-get install -y -qq curl wget >/dev/null 2>&1
mkdir -p /opt/dash /var/log
# expose live nvidia-smi over http for evidence capture
( while true; do nvidia-smi > /opt/nvidia-smi.txt 2>&1; sleep 3; done ) &
( cd /opt && python3 -m http.server 8080 >/var/log/httpd.log 2>&1 ) &


# 1. vLLM (image already has vllm + cuda). Serves OpenAI API + Prometheus metrics on :8000
python3 -m vllm.entrypoints.openai.api_server \
  --model Qwen/Qwen2.5-1.5B-Instruct --port 8000 --max-model-len 8192 \
  --gpu-memory-utilization 0.85 --disable-log-requests > /var/log/vllm.log 2>&1 &

# 2. GPU metrics via nvidia-smi exporter on :9835
cd /opt
wget -q https://github.com/utkuozdemir/nvidia_gpu_exporter/releases/download/v1.2.1/nvidia_gpu_exporter_1.2.1_linux_x86_64.tar.gz -O ge.tgz
tar xzf ge.tgz && chmod +x nvidia_gpu_exporter
./nvidia_gpu_exporter --web.listen-address=":9835" > /var/log/gpuexp.log 2>&1 &

# 3. Prometheus on :9090
wget -q https://github.com/prometheus/prometheus/releases/download/v2.55.1/prometheus-2.55.1.linux-amd64.tar.gz -O p.tgz
tar xzf p.tgz
cat > /opt/prom.yml <<EOF
global: {scrape_interval: 5s}
scrape_configs:
  - job_name: vllm
    static_configs: [{targets: ['localhost:8000']}]
  - job_name: gpu
    static_configs: [{targets: ['localhost:9835']}]
EOF
/opt/prometheus-2.55.1.linux-amd64/prometheus --config.file=/opt/prom.yml \
  --storage.tsdb.path=/opt/promdata --web.listen-address=":9090" > /var/log/prom.log 2>&1 &

# 4. Grafana on :3000 (anonymous admin)
wget -q https://dl.grafana.com/oss/release/grafana-11.3.0.linux-amd64.tar.gz -O g.tgz
tar xzf g.tgz
GF=/opt/grafana-v11.3.0
mkdir -p $GF/conf/provisioning/datasources $GF/conf/provisioning/dashboards
cat > $GF/conf/provisioning/datasources/ds.yml <<EOF
apiVersion: 1
datasources:
  - {name: Prometheus, type: prometheus, uid: prometheus, url: http://localhost:9090, isDefault: true}
EOF
cat > $GF/conf/provisioning/dashboards/db.yml <<EOF
apiVersion: 1
providers:
  - {name: default, type: file, options: {path: /opt/dash}}
EOF
export GF_SECURITY_ADMIN_PASSWORD=llmobs
export GF_AUTH_ANONYMOUS_ENABLED=true
export GF_AUTH_ANONYMOUS_ORG_ROLE=Admin
export GF_SERVER_HTTP_PORT=3000
cd $GF && ./bin/grafana server --homepath=$GF > /var/log/grafana.log 2>&1 &

# 5. wait for vLLM to load, then drive load forever
for i in $(seq 1 60); do curl -sf http://localhost:8000/health && break; sleep 5; done
PROMPTS=("Explain what an SLO is." "Write a haiku about GPUs." "List 3 uses of eBPF." "Summarize the CAP theorem." "What is a canary deploy?")
while true; do
  for c in 1 2 3 4; do
    P=${PROMPTS[$((RANDOM % 5))]}
    curl -s http://localhost:8000/v1/chat/completions -H 'Content-Type: application/json' \
      -d "{\"model\":\"Qwen/Qwen2.5-1.5B-Instruct\",\"messages\":[{\"role\":\"user\",\"content\":\"$P\"}],\"max_tokens\":160}" >/dev/null &
  done
  wait
  sleep 0.2
done
