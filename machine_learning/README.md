# Irrigation model training

Install `requirements-ai.txt`, then run `python manage.py train_irrigation --rows 5000`.
The command trains Random Forest and XGBoost classifiers, evaluates both on a held-out test split, saves `.joblib` artifacts, and writes comparison metrics.

**Academic limitation:** The initial dataset is synthetic and its target labels are generated from a documented heuristic. Metrics demonstrate the pipeline only; they are not evidence of real-world irrigation accuracy. Replace or validate the synthetic labels with agronomist-labelled observations and field data before operational use.
