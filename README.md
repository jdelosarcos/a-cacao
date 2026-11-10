# Cacao Farm Intelligence — Streamlit

Professional, modular Streamlit interface for the supplied `cacao_data_mining_analysisv2.py`.

## Installation

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Upload the original **CacaoY.csv** survey using the sidebar. This CSV was not included in the supplied files. The application expects the original two-row header arrangement as used by the original Python script.

## Architecture and bottleneck control

- `app.py`: Streamlit interface, Plotly charts, stakeholder insights and downloads.
- `engine.py`: Executes the original numbered modules incrementally, with prerequisite modules run once per uploaded dataset. Computation state persists across Streamlit reruns in a cached resource.
- `original_analysis.py`: Unmodified user-provided analysis code, retaining normalization, permutation tests, K-Modes, grouped CV, seven classifiers, interpretation and forecasting logic.
- `.streamlit/config.toml`: Green professional theme.

**Lazy loading:** Modules 1–2 load for overview; association testing loads on demand; clustering/modeling/record explanations only run when opened. The original five-fold grid searches and nested cluster selection are computationally expensive and can take several minutes or longer. They have not been simplified or silently replaced with different models.

**Important:** The original source uses module-level global variables. For a straightforward single-user research deployment, the adapter executes modules sequentially in an isolated temporary working directory. Each distinct uploaded CSV has a distinct cached session. For a multi-user production deployment, add job isolation, per-user cache management, authentication, background workers and resource quotas.

## Interpretation safeguards

- The target is a three-class **reported yield range** in kg/ha/season, not exact kilograms.
- The original four survey ranges remain available in descriptive outputs.
- No chronology exists in the survey; forecasts require a separate regular dated numeric series.
- Farmer and agency insights are descriptive screening prompts, **not causal agronomic effects or validated funding allocation decisions**.
- Predictions are not externally or temporally validated. Probability outputs, where available, are uncalibrated.
- Original source's fixed interpretation text is not used as an empirical result; the Streamlit UI reads metrics from the current uploaded dataset.

## Notes

The original module 8 uses an independent forecast function and can be opened without training the classifiers. The original module 11 depends on the preceding analysis modules and therefore is a heavier optional export. Modules 12–13 in the original are a standalone HTML/Colab dashboard, replaced by this Streamlit frontend.
