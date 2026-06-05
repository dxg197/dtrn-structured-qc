# DTRN Replacement Scout Plan

GG LLM Optimizer should look for places where DTRN variants can replace conventional neural-network modules while reducing parameters by at least 10% without degrading performance.

## Objective

```text
parameter_reduction_pct >= 10.0
quality_score >= baseline_quality_score
long_context_score >= baseline_long_context_score
p95_latency_ms <= baseline_p95_latency_ms
time_to_first_token_ms <= baseline_time_to_first_token_ms
inter_token_latency_ms <= baseline_inter_token_latency_ms
failure_rate <= baseline_failure_rate
tokens_per_second >= baseline_tokens_per_second
output_tokens_per_second >= baseline_output_tokens_per_second
```

A candidate is accepted only if it passes the parameter reduction target and all measured no-regression gates. If a candidate passes the parameter target but does not include enough performance metrics, it is marked `needs_ablation`, not accepted.

## Candidate module classes

The scout should prioritize large, repeated, or deployment-critical neural-network modules:

```text
nn.Linear / dense MLP projections
attention Q/K/V/O projections
feed-forward up/down/gate projections
Mixture-of-Experts expert MLPs
adapter / LoRA / projection layers
embedding bottlenecks where safe
router-adjacent MoE components, with caution
```

## Candidate replacement types

```text
baseline_dense
low_rank
tensor_train
dtrn_bottleneck
block_dtrn
moe_dtrn_expert
dtrn_adapter
```

## Input schema

The command accepts JSON with either a top-level list or a dictionary containing `candidates`, `records`, `modules`, or `dtrn_candidates`.

Each candidate may include:

```json
{
  "module_path": "model.layers.12.mlp.down_proj",
  "module_type": "dense_mlp_projection",
  "candidate_type": "block_dtrn",
  "baseline_params": 67108864,
  "candidate_params": 58720256,
  "baseline_quality_score": 0.812,
  "candidate_quality_score": 0.813,
  "baseline_long_context_score": 0.764,
  "candidate_long_context_score": 0.764,
  "baseline_p95_latency_ms": 142.0,
  "candidate_p95_latency_ms": 139.0,
  "baseline_tokens_per_second": 5120.0,
  "candidate_tokens_per_second": 5200.0,
  "baseline_failure_rate": 0.0,
  "candidate_failure_rate": 0.0
}
```

## Command

```bash
ggllm-opt dtrn-scout \
  --candidates examples/dtrn_replacement_candidates.json \
  --min-param-reduction-pct 10.0 \
  --out-json runs/deepseek_pilot/dtrn_replacement_scout.json \
  --out-md runs/deepseek_pilot/dtrn_replacement_scout.md
```

## Output fields

The generated JSON and Markdown include:

```text
module_path
module_type
candidate_type
baseline_params
candidate_params
parameter_reduction_pct
baseline_quality_score
candidate_quality_score
baseline_long_context_score
candidate_long_context_score
baseline_p95_latency_ms
candidate_p95_latency_ms
baseline_tokens_per_second
candidate_tokens_per_second
baseline_failure_rate
candidate_failure_rate
decision
reason
```

## Interpretation

`accept` means the candidate meets the 10% parameter-reduction target and all supplied no-regression metrics. `reject` means either the parameter target failed or a measured metric regressed. `needs_ablation` means the parameter target passed, but more benchmarking is required before the replacement can be considered safe.

DTRN replacement should be treated as a controlled structural-compression wave in the DeepSeek-scale pilot. It should not be mixed with quantization, runtime changes, or scheduler changes in the same ablation wave unless the goal is a later combined-route stress test.
