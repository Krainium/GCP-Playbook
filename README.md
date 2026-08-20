# GCP Playbook

Practical Google Cloud guides. Each one lives in its own folder with clear steps and real screenshots.

## Machines

* [Windows RDP and SSH](windows-rdp-ssh). Create a Windows VM, connect over RDP, then add SSH on the same instance.
* [Android 9 emulator](android-emulator). Run a KVM accelerated Android 9 emulator on a Linux VM and reach it over VNC or RDP.

## Observability and platform

Each of these stands up on a small GKE cluster with Prometheus and Grafana, and every screenshot is from a real run.

* [Canary Autopilot](canary-autopilot). Deploys that promote or roll back on their own, gated by your live SLOs with Argo Rollouts.
* [Load Storm](load-storm). Run k6 load tests inside the cluster and watch the load and the cluster react on one board.
* [Event Autoscaler](event-autoscaler). Scale a workload on a Prometheus metric like request rate with KEDA, not CPU.
* [Chaos SLO Arena](chaos-slo-arena). Break the cluster on purpose with Chaos Mesh and watch the error budget burn in real time.
* [eBPF X Ray](ebpf-xray). Golden signals for every service with no code changes, powered by Grafana Beyla and eBPF.
* [Runtime Threat Map](runtime-threat-map). Watch process launches, file reads, and network events live with Cilium Tetragon.
* [FinOps Cockpit](finops-cockpit). Turn cluster cost into a live signal per namespace and per team with OpenCost.
* [Self Hosted LGTM](lgtm-selfhosted). Logs, metrics, traces, and profiles in one Grafana pane you host yourself.
* [Fleet Command](fleet-command). One screen for every cluster in every region, with metrics rolled up centrally.
* [LLM Inference Observatory](llm-inference-observatory). Serve your own LLM on a GPU and watch tokens per second, GPU use, and cost per token.

More guides will be added here over time.
