import time, threading
from openai import OpenAI
client = OpenAI(base_url="http://vllm:8000/v1", api_key="none")
PROMPTS = [
    "Explain what an SLO is in one paragraph.",
    "Write a haiku about kubernetes.",
    "List three benefits of eBPF.",
    "Summarize the CAP theorem simply.",
    "What is a canary deployment?",
]
def worker(i):
    n = 0
    while True:
        p = PROMPTS[(i + n) % len(PROMPTS)]
        try:
            s = client.chat.completions.create(
                model="Qwen/Qwen2.5-0.5B-Instruct",
                messages=[{"role": "user", "content": p}],
                max_tokens=128, stream=True, temperature=0.7)
            for _ in s: pass
        except Exception:
            time.sleep(1)
        n += 1
# ramp concurrency so the graphs breathe
for i in range(6):
    threading.Thread(target=worker, args=(i,), daemon=True).start()
    time.sleep(5)
while True: time.sleep(60)
