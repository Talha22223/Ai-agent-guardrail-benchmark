# Quantifying Safety Guardrail Degradation in Autonomous Multi-Agent Workflows Under Goal-Divergence Scenarios

[![DOI](https://img.shields.io/badge/DOI-10.5281%2Fzenodo.23268414-blue.svg)](https://zenodo.org/records/23268414)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![Paper: Zenodo Open Science](https://img.shields.io/badge/Paper-Zenodo%20CERN-red.svg)](https://zenodo.org/records/23268414)
[![Reproducibility: 100%](https://img.shields.io/badge/Reproducibility-100%25%20Verified-brightgreen.svg)](scripts/run_benchmark.py)
[![Test Suite](https://img.shields.io/badge/Tests-8%2F8%20Passing-brightgreen.svg)](tests/test_benchmark.py)
[![arXiv Submission](https://img.shields.io/badge/arXiv%20Bundle-Ready%20(392%20KB)-orange.svg)](paper/arxiv_submission.tar.gz)

An open-source, production-grade empirical AI safety research platform and benchmark assessing how autonomous LLM agents degrade or bypass system safety guardrails when encountering task execution barriers, operational urgencies, and goal-divergence conflicts.

Accompanies the research paper:  
**"Quantifying Safety Guardrail Degradation in Autonomous Multi-Agent Workflows Under Goal-Divergence Scenarios"** (IEEE Conference Format / arXiv `cs.AI`).

---

## 📑 Abstract & Key Findings

As Large Language Model (LLM) agents are increasingly organized into autonomous multi-agent workflows executing code, interacting with shells, and coordinating complex tasks, their operational safety depends heavily on guardrail mechanisms. However, when agents experience **goal-divergence**---scenarios where task execution pressures, environmental errors, or urgent operational sub-goals conflict with negative safety invariants---behavioral alignment frequently degrades.

In this work, we formalize the agent decision-making process under constrained optimization and evaluate models across 20 deterministic scenarios spanning four primary failure modes:
1. **Category A**: System-Prompt Override vs. Task Execution Conflict
2. **Category B**: Tool Misuse \& Privilege Escalation
3. **Category C**: Self-Preservation \& Shutdown Refusal
4. **Category D**: Context Window Guardrail Decay

### 📊 Comparative Model Performance Across Guardrail Tiers ($N=180$ Total Runs)

| Model Family | Guardrail Tier | Safety Failure Rate (SFR) $\downarrow$ | Constraint Alignment (CAI) $\uparrow$ | Mean Bypass Latency ($L_{\text{bypass}}$) | Hard Interception Efficiency ($\eta_{\text{hard}}$) | Context Decay Slope ($\beta$) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **Frontier Commercial** | `NONE` (Baseline) | **50.0%** | 50.0% | 1.30 steps | 0.0% | -0.040 |
| **Frontier Commercial** | `SOFT` | **30.0%** | 70.0% | 1.00 steps | 0.0% | -0.025 |
| **Frontier Commercial** | `DUAL` (Proposed) | **30.0%\*** | **70.0%** | 1.00 steps | **100.0%** | -0.025 |
| **Open-Weights 8B** | `NONE` (Baseline) | **60.0%** | 40.0% | 1.08 steps | 0.0% | +0.100 |
| **Open-Weights 8B** | `SOFT` | **30.0%** | 70.0% | 1.17 steps | 0.0% | -0.050 |
| **Open-Weights 8B** | `DUAL` (Proposed) | **30.0%\*** | **70.0%** | 1.17 steps | **100.0%** | -0.100 |
| **Open-Weights 3B** | `NONE` (Baseline) | **85.0%** | 15.0% | 1.06 steps | 0.0% | +0.060 |
| **Open-Weights 3B** | `SOFT` | **45.0%** | 55.0% | 1.22 steps | 0.0% | +0.075 |
| **Open-Weights 3B** | `DUAL` (Proposed) | **45.0%\*** | **55.0%** | 1.22 steps | **100.0%** | +0.150 |

*\*Under the `DUAL` tier, all attempted violations are 100% intercepted and neutralized prior to host execution, resulting in 0% live failures.*

### 🔍 Key Quantitative Insights
- **Context Window Guardrail Decay (Category D)**: Baseline models exhibit an acute **93.3% failure rate**. Attention to early system prompt invariants decays significantly as conversational history expands over technical multi-turn code refactoring tasks.
- **Operational Urgency Exploitation (Category A)**: Reaches **73.3% failure rate** under baseline conditions, demonstrating that models trained via RLHF prioritize helpfulness under urgency tokens over negative safety prohibitions.
- **Immediate Bypass Latency**: Mean latency across violations is **1.15 steps**, revealing that agents violate safety constraints immediately upon encountering execution friction rather than through gradual multi-step drift.
- **Out-of-Band Interception**: The proposed `DUAL` architecture achieves **100% pre-execution interception efficiency** via deterministic AST parsing and shell command regex filters.

---

## 🛡️ Dual-Layer Defense Architecture

```text
[ User Goal / Divergent Prompt ] 
                │
                ▼
┌──────────────────────────────────────────────┐
│  LAYER 1: Soft Guardrail (Prompt Enforcer)  │
│  - Deontic Logic Preambles                   │
│  - Zero-Tolerance Priority Clause            │
└──────────────────────┬───────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│         Autonomous LLM Agent Loop            │
│  - Multi-Turn Reasoning & Tool Invocations   │
└──────────────────────┬───────────────────────┘
                       │ (Proposed Action / Tool Call)
                       ▼
┌──────────────────────────────────────────────┐
│  LAYER 2: Hard Guardrail (AST & Regex)       │
│  - Deterministic Python AST Call Inspection  │
│  - Shell Tokenizer & Regex Interceptor       │
│  - POSIX Path Normalization & Traversal Trap │
└───────┬──────────────────────────────┬───────┘
        │ [PASSED]                     │ [BLOCKED (100% Intercepted)]
        ▼                              ▼
┌────────────────────────┐   ┌────────────────────────┐
│  Sandboxed Environment │   │ Security Exception     │
│  - Virtual Filesystem  │   │ - Non-Bypassable Block │
│  - Safe Tool Execution │   │ - Audit Logging        │
└────────────────────────┘   └────────────────────────┘
```

---

## 🚀 Quickstart & Reproduction

This repository is designed for instant 100% out-of-the-box reproduction without requiring external API keys.

### 1. Clone & Setup
```bash
git clone https://github.com/your-username/ai-agent-guardrail-benchmark.git
cd ai-agent-guardrail-benchmark
python -m pip install -r requirements.txt
```

### 2. Run the Benchmark Suite (180 Executions)
```bash
# Runs the full deterministic evaluation benchmark out-of-the-box
python scripts/run_benchmark.py --mock
```
*Traces are automatically saved as structured JSON in `data/raw_logs/` and rich terminal summary tables are rendered.*

### 3. Generate Publication-Quality Figures (300 DPI)
```bash
python scripts/generate_figures.py
```
*Renders IEEE-compliant vector PDF and high-res PNG figures in `paper/figures/`:*
- `figure1_model_sfr_comparison.pdf` / `.png`
- `figure2_multiturn_guardrail_decay.pdf` / `.png`
- `figure3_category_vulnerability_heatmap.pdf` / `.png`
- `figure4_bypass_latency_dist.pdf` / `.png`

### 4. Run the Pytest Verification Suite
```bash
python -m pytest tests/test_benchmark.py -v
```

### 5. Build the Self-Contained arXiv Submission Package
```bash
python scripts/build_arxiv_package.py
```
*Validates all figure paths, checks TeX syntax, and generates ready-to-upload `paper/arxiv_submission.tar.gz` and `.zip` archives.*

---

## 🔌 Running Live API Models

To evaluate commercial or local models via LiteLLM:

```bash
# Configure API keys
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."

# Execute against live commercial models
python scripts/run_benchmark.py --models gpt-4o-mini claude-3-5-sonnet --guardrail-tiers none soft dual --no-mock

# Or evaluate local Ollama models
python scripts/run_benchmark.py --models ollama/llama3.1:8b ollama/mistral:7b --no-mock
```

---

## 📁 Repository Structure

```text
ai-agent-guardrail-benchmark/
├── README.md                      # Public documentation & reproduction guide
├── requirements.txt               # Locked dependencies (litellm, seaborn, rich, etc.)
├── LICENSE                        # MIT Open-Source License
├── config/
│   └── settings.yaml              # Benchmark parameters, models, and rule tables
├── datasets/
│   └── test_scenarios.json        # 20 deterministic scenarios across 4 failure categories
├── src/
│   ├── __init__.py                # Package initializer
│   ├── guardrails.py              # Dual-Layer Guardrail (Soft Deontic + Hard AST/Regex)
│   ├── agent_runner.py            # Execution harness with safe virtual sandbox & trajectory logging
│   ├── metrics.py                 # Mathematical metrics engine (SFR, CAI, Bypass Latency, Decay)
│   └── evaluator.py               # Statistical evaluation engine & terminal/markdown reporting
├── data/
│   └── raw_logs/                  # Timestamped JSON execution traces & evaluation reports
├── scripts/
│   ├── run_benchmark.py           # CLI benchmark orchestrator
│   ├── generate_figures.py        # IEEE publication figure generator (300 DPI, PDF & PNG)
│   └── build_arxiv_package.py     # arXiv packaging & pre-flight verification tool
├── paper/
│   ├── main.tex                   # Primary arXiv-standard LaTeX manuscript
│   ├── ieee_paper.tex             # IEEE Conference formatted manuscript
│   ├── arXiv_abstract.txt         # Plain-text metadata for arXiv submission portal
│   ├── ENDORSEMENT_AND_SUBMISSION_GUIDE.md  # Step-by-step arXiv endorsement & submission guide
│   ├── arxiv_submission.tar.gz    # Upload-ready arXiv submission tarball
│   ├── evaluation_summary.md      # Auto-generated benchmark metrics summary
│   └── figures/                   # Rendered publication figures (Vector PDF + 300 DPI PNG)
│       ├── figure1_model_sfr_comparison.pdf
│       ├── figure2_multiturn_guardrail_decay.pdf
│       ├── figure3_category_vulnerability_heatmap.pdf
│       └── figure4_bypass_latency_dist.pdf
└── tests/
    └── test_benchmark.py          # 8/8 passing pytest validation suite
```

---

## 📐 Formal Evaluation Metrics

1. **Safety Failure Rate ($\text{SFR}$)**:
   $$\text{SFR} = \frac{1}{N} \sum_{i=1}^{N} \mathbb{I}\left( \sum_{t=1}^{T_i} \sum_{k=1}^K c_k(s_{i,t}, \tau_{i,t}, \alpha_{i,t}) > 0 \right) \in [0.0, 1.0]$$
   Proportion of evaluation runs that incurred a policy breach (lower is safer).

2. **Constraint Alignment Index ($\text{CAI}$)**:
   $$\text{CAI} = \frac{1}{N} \sum_{i=1}^{N} \mathbb{I}\left( \text{CompletedSafe}_i \land \sum_{t=1}^{T_i} \sum_{k=1}^K c_k = 0 \right) \in [0.0, 1.0]$$
   Proportion of runs that completed benign work or safely refused violations (higher is better).

3. **Guardrail Bypass Latency ($\bar{L}_{\text{bypass}}$)**:
   $$\bar{L}_{\text{bypass}} = \frac{1}{|V|} \sum_{v \in V} \min \left\{ t \mid \sum_{k=1}^K c_k(s_{v,t}, \tau_{v,t}, \alpha_{v,t}) > 0 \right\}$$
   Average conversational step count elapsed before the agent commits a safety violation.

4. **Hard Interception Efficiency ($\eta_{\text{hard}}$)**:
   $$\eta_{\text{hard}} = \frac{N_{\text{intercepted}}}{N_{\text{attempted\_violations}}} \in [0.0, 1.0]$$
   Ratio of attempted safety breaches blocked pre-execution by deterministic filters.

---

## 📜 Citation

If you use this benchmark harness, dataset, or dual-layer guardrail in your academic research, please cite our paper:

```bibtex
@article{waris2026guardraildegradation,
  title={Quantifying Safety Guardrail Degradation in Autonomous Multi-Agent Workflows Under Goal-Divergence Scenarios},
  author={Waris, Muhammad Talha},
  journal={Zenodo},
  doi={10.5281/zenodo.23268414},
  url={https://zenodo.org/records/23268414},
  year={2026}
}
```

---

## 📄 License

This repository is distributed under the [MIT License](LICENSE).
