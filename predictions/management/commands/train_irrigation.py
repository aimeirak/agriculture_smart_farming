import json
from pathlib import Path
import numpy as np
import joblib
import pandas as pd
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix
from sklearn.model_selection import train_test_split

FEATURES = ["soil_moisture_pct", "temperature_c", "humidity_pct", "rainfall_24h_mm"]

class Command(BaseCommand):
    help = "Train and compare Random Forest and XGBoost irrigation classifiers on generated synthetic data."
    def add_arguments(self, parser):
        parser.add_argument("--rows", type=int, default=5000)
        parser.add_argument("--seed", type=int, default=42)
        parser.add_argument("--dataset", help="Optional CSV path produced by simulate_farm_data.")
    def handle(self, *args, **opts):
        try:
            from xgboost import XGBClassifier
        except ImportError as exc:
            raise CommandError("XGBoost is missing. Install requirements-ai.txt first.") from exc
        if opts["rows"] < 500: raise CommandError("Use at least 500 synthetic rows.")
        rng = np.random.default_rng(opts["seed"])
        dataset_type = "synthetic"
        if opts.get("dataset"):
            dataset_path = Path(opts["dataset"]).expanduser()
            if not dataset_path.is_absolute():
                dataset_path = Path(settings.BASE_DIR) / dataset_path
            if not dataset_path.exists():
                raise CommandError(f"Dataset not found: {dataset_path}")
            frame = pd.read_csv(dataset_path)
            required = FEATURES + ["irrigation_required"]
            missing = [column for column in required if column not in frame.columns]
            if missing:
                raise CommandError(f"Dataset is missing required columns: {', '.join(missing)}")
            frame = frame[required].dropna()
            if len(frame) < 500:
                raise CommandError("Dataset must contain at least 500 complete rows.")
            X = frame[FEATURES].astype(float).to_numpy()
            y = frame["irrigation_required"].astype(int).to_numpy()
            if len(np.unique(y)) != 2:
                raise CommandError("Dataset target must contain both classes 0 and 1.")
            n = len(frame)
            dataset_type = "simulated_sensor_dataset" if "simulated" in dataset_path.name.lower() else "external_csv"
        else:
            n = opts["rows"]
            soil = rng.uniform(8, 90, n)
            temp = rng.uniform(12, 40, n)
            humidity = rng.uniform(20, 100, n)
            rain = np.clip(rng.gamma(1.4, 3.0, n), 0, 35)
            # Transparent synthetic labelling rule: teaching baseline, not expert ground truth.
            risk = (soil < 30).astype(float) * 0.58 + (temp > 30).astype(float) * 0.12
            risk += (humidity < 45).astype(float) * 0.10 - (rain >= 5).astype(float) * 0.32
            risk += rng.normal(0, 0.08, n)
            y = (risk > 0.35).astype(int)
            X = np.column_stack([soil, temp, humidity, rain])
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=opts["seed"], stratify=y
        )
        models = {
            "random_forest": RandomForestClassifier(n_estimators=300, max_depth=12,
                min_samples_leaf=3, class_weight="balanced", random_state=opts["seed"], n_jobs=-1),
            "xgboost": XGBClassifier(n_estimators=300, max_depth=5, learning_rate=0.05,
                subsample=0.85, colsample_bytree=0.9, objective="binary:logistic",
                eval_metric="logloss", random_state=opts["seed"], n_jobs=-1),
        }
        output = Path(settings.BASE_DIR) / "machine_learning" / "trained_models"
        output.mkdir(parents=True, exist_ok=True)
        metrics = {}
        for name, model in models.items():
            model.fit(X_train, y_train)
            pred = model.predict(X_test)
            proba = model.predict_proba(X_test)[:, 1]
            result = {"accuracy": accuracy_score(y_test, pred),
                "precision": precision_score(y_test, pred, zero_division=0),
                "recall": recall_score(y_test, pred, zero_division=0),
                "f1": f1_score(y_test, pred, zero_division=0),
                "roc_auc": roc_auc_score(y_test, proba)}
            metrics[name] = {key: round(float(value), 4) for key, value in result.items()}
            metrics[name]["confusion_matrix"] = confusion_matrix(y_test, pred, labels=[0, 1]).tolist()
            metrics[name]["feature_importance"] = {
                feature: round(float(value), 6)
                for feature, value in zip(FEATURES, getattr(model, "feature_importances_", []))
            }
            joblib.dump({"model": model, "features": FEATURES, "version": "1.0",
                "training_data": dataset_type, "metrics": metrics[name]}, output / f"{name}.joblib")
            self.stdout.write(self.style.SUCCESS(f"{name}: {metrics[name]}"))
        (output / "comparison_metrics.json").write_text(json.dumps({
            "dataset": dataset_type, "rows": n, "seed": opts["seed"],
            "label_definition": "Simulated heuristic labels; not agronomist-validated ground truth",
            "models": metrics}, indent=2), encoding="utf-8")
        self.stdout.write(self.style.SUCCESS(f"Models saved in {output}"))
