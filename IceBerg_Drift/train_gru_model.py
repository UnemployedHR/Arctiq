"""
train_gru_model.py

GRU sequence model for iceberg trajectory prediction.

Architecture:
  Input: (batch, seq_len=1, n_features)
  GRU → Dense → output [delta_lat, delta_lon]

Note: IIP data is not regular hourly; each sample has one
previous-segment context vector. A seq_len=1 GRU is equivalent to a
dense network but preserves the architecture for extension to multi-step
inputs when denser observation data becomes available.

For reproducibility: fixed random seeds in numpy, Python, and PyTorch.
"""

import os, sys, json, warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

warnings.filterwarnings('ignore')
os.makedirs('models/gru', exist_ok=True)

RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)

# ─── Try importing PyTorch ────────────────────────────────────────────────────
try:
    import torch
    import torch.nn as nn
    from torch.utils.data import DataLoader, TensorDataset
    torch.manual_seed(RANDOM_SEED)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(RANDOM_SEED)
    DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"PyTorch {torch.__version__}  device: {DEVICE}")
    HAS_TORCH = True
except ImportError:
    print("PyTorch not available. GRU model will be skipped.")
    HAS_TORCH = False

R = 6371.0

def geo_error_km(pred_dlat, pred_dlon, true_dlat, true_dlon):
    pred_la = np.radians(pred_dlat)
    true_la = np.radians(true_dlat)
    dlo = np.radians(true_dlon - pred_dlon)
    dla = np.radians(true_dlat - pred_dlat)
    # Simplified: treat delta degrees as positions offset from 0
    # More accurate: use haversine on the actual difference
    a = np.sin(dla/2)**2 + np.cos(np.radians(0))*np.cos(np.radians(true_dlat - pred_dlat))*np.sin(dlo/2)**2
    return R * 2 * np.arcsin(np.sqrt(np.clip(a, 0, 1)))

def geo_error_km_full(pred_dlat, pred_dlon, true_dlat, true_dlon, lat_ref):
    pred_la = np.radians(lat_ref + pred_dlat)
    true_la = np.radians(lat_ref + true_dlat)
    dlo = np.radians(true_dlon - pred_dlon)
    dla = true_la - pred_la
    a = np.sin(dla/2)**2 + np.cos(pred_la)*np.cos(true_la)*np.sin(dlo/2)**2
    return R * 2 * np.arcsin(np.sqrt(np.clip(a, 0, 1)))

def metrics_dict(errs, label):
    e = np.array(errs)
    e = e[~np.isnan(e)]
    print(f"  {label} (n={len(e)}):  mean={np.mean(e):.3f}  median={np.median(e):.3f}  "
          f"rmse={np.sqrt(np.mean(e**2)):.3f}  max={np.max(e):.3f}")
    return {
        'n': int(len(e)),
        'mean_km':   round(float(np.mean(e)),   3),
        'median_km': round(float(np.median(e)), 3),
        'rmse_km':   round(float(np.sqrt(np.mean(e**2))), 3),
        'min_km':    round(float(np.min(e)),    3),
        'max_km':    round(float(np.max(e)),    3),
    }

# ─── Load data ────────────────────────────────────────────────────────────────
ml = pd.read_parquet('data/ml/final_ml_dataset.parquet')
with open('data/ml/ml_dataset_config.json') as f:
    config = json.load(f)

feature_cols = config['feature_cols']
target_cols  = config['target_cols']

train = ml[ml['split'] == 'train'].reset_index(drop=True)
val   = ml[ml['split'] == 'val'].reset_index(drop=True)
test  = ml[ml['split'] == 'test'].reset_index(drop=True)

from sklearn.preprocessing import StandardScaler
import joblib

# Fit scaler on train only
scaler = StandardScaler()
X_train = scaler.fit_transform(train[feature_cols].values.astype(np.float32))
X_val   = scaler.transform(val[feature_cols].values.astype(np.float32))
X_test  = scaler.transform(test[feature_cols].values.astype(np.float32))
y_train = train[target_cols].values.astype(np.float32)
y_val   = val[target_cols].values.astype(np.float32)
y_test  = test[target_cols].values.astype(np.float32)
lat_train = train['lat'].values
lat_val   = val['lat'].values
lat_test  = test['lat'].values

# Target scaler (fit on train)
target_scaler = StandardScaler()
y_train_sc = target_scaler.fit_transform(y_train)
y_val_sc   = target_scaler.transform(y_val)

joblib.dump(scaler,        'models/gru/feature_scaler.joblib')
joblib.dump(target_scaler, 'models/gru/target_scaler.joblib')

results = {}

if not HAS_TORCH:
    print("Skipping GRU — PyTorch not installed.")
    # Save placeholder
    results['gru_val']  = {'n': 0, 'note': 'PyTorch not available'}
    results['gru_test'] = {'n': 0, 'note': 'PyTorch not available'}
else:
    # ── GRU Model definition ──────────────────────────────────────────────────
    class IcebergGRU(nn.Module):
        def __init__(self, input_size, hidden_size=128, num_layers=2, dropout=0.2, output_size=2):
            super().__init__()
            self.gru = nn.GRU(
                input_size=input_size, hidden_size=hidden_size,
                num_layers=num_layers, batch_first=True,
                dropout=dropout if num_layers > 1 else 0.0
            )
            self.dropout = nn.Dropout(dropout)
            self.fc1 = nn.Linear(hidden_size, 64)
            self.fc2 = nn.Linear(64, output_size)
            self.act = nn.GELU()

        def forward(self, x):
            # x: (batch, seq_len, features)
            out, _ = self.gru(x)
            out = out[:, -1, :]   # last timestep
            out = self.dropout(out)
            out = self.act(self.fc1(out))
            return self.fc2(out)

    N_FEATURES = X_train.shape[1]

    # ── Tensors (seq_len=1 — single context vector per sample) ───────────────
    Xt = torch.from_numpy(X_train[:, np.newaxis, :]).float().to(DEVICE)
    yt = torch.from_numpy(y_train_sc).float().to(DEVICE)
    Xv = torch.from_numpy(X_val[:, np.newaxis, :]).float().to(DEVICE)
    yv = torch.from_numpy(y_val_sc).float().to(DEVICE)
    Xte= torch.from_numpy(X_test[:, np.newaxis, :]).float().to(DEVICE)

    train_ds = TensorDataset(Xt, yt)
    val_ds   = TensorDataset(Xv, yv)

    # ── Train ─────────────────────────────────────────────────────────────────
    EPOCHS    = 200
    BATCH     = 128
    LR        = 1e-3
    PATIENCE  = 20

    model = IcebergGRU(input_size=N_FEATURES, hidden_size=128, num_layers=2, dropout=0.2).to(DEVICE)
    optimizer = torch.optim.Adam(model.parameters(), lr=LR, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=10, factor=0.5)
    criterion = nn.MSELoss()

    train_loader = DataLoader(train_ds, batch_size=BATCH, shuffle=True,
                              generator=torch.Generator().manual_seed(RANDOM_SEED))

    best_val_loss = np.inf
    patience_ctr  = 0
    train_losses, val_losses = [], []

    print(f"\nTraining GRU ({N_FEATURES} features, hidden=128, layers=2)...")
    for epoch in range(1, EPOCHS+1):
        model.train()
        ep_loss = 0.0
        for xb, yb in train_loader:
            optimizer.zero_grad()
            pred = model(xb)
            loss = criterion(pred, yb)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            ep_loss += loss.item() * len(xb)
        ep_loss /= len(train_ds)
        train_losses.append(ep_loss)

        model.eval()
        with torch.no_grad():
            vl = criterion(model(Xv), yv).item()
        val_losses.append(vl)
        scheduler.step(vl)

        if vl < best_val_loss:
            best_val_loss = vl
            patience_ctr = 0
            torch.save(model.state_dict(), 'models/gru/best_model.pt')
        else:
            patience_ctr += 1

        if epoch % 20 == 0:
            print(f"  Epoch {epoch:3d}  train_loss={ep_loss:.5f}  val_loss={vl:.5f}  patience={patience_ctr}")

        if patience_ctr >= PATIENCE:
            print(f"  Early stopping at epoch {epoch}")
            break

    # Load best
    model.load_state_dict(torch.load('models/gru/best_model.pt', map_location=DEVICE, weights_only=True))
    model.eval()

    # ── Predictions ───────────────────────────────────────────────────────────
    with torch.no_grad():
        gru_val_sc  = model(Xv).cpu().numpy()
        gru_test_sc = model(Xte).cpu().numpy()

    gru_val  = target_scaler.inverse_transform(gru_val_sc)
    gru_test = target_scaler.inverse_transform(gru_test_sc)

    gru_val_err  = geo_error_km_full(gru_val[:,0],  gru_val[:,1],  y_val[:,0],  y_val[:,1],  lat_val)
    gru_test_err = geo_error_km_full(gru_test[:,0], gru_test[:,1], y_test[:,0], y_test[:,1], lat_test)

    results['gru_val']  = metrics_dict(gru_val_err,  "GRU (Val)")
    results['gru_test'] = metrics_dict(gru_test_err, "GRU (Test)")

    # ── Training curve ────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(train_losses, label='Train loss')
    ax.plot(val_losses,   label='Val loss')
    ax.set_xlabel('Epoch'); ax.set_ylabel('MSE Loss')
    ax.set_title('GRU Training Curve')
    ax.legend(); ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('models/gru/training_curve.png', dpi=150)
    plt.close()
    print("Saved: models/gru/training_curve.png")

    # ── Error distribution ────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(8, 4))
    e = gru_val_err[~np.isnan(gru_val_err)]
    ax.hist(e, bins=40, color='purple', alpha=0.75, edgecolor='black', linewidth=0.3)
    ax.axvline(np.mean(e),   color='red',   linestyle='--', linewidth=1.5, label=f'Mean: {np.mean(e):.1f} km')
    ax.axvline(np.median(e), color='black', linestyle=':',  linewidth=1.5, label=f'Median: {np.median(e):.1f} km')
    ax.set_xlabel('Geodesic Error (km)'); ax.set_ylabel('Count')
    ax.set_title('GRU Error Distribution (Validation Set)')
    ax.legend(); ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('models/gru/gru_error_distribution.png', dpi=150)
    plt.close()
    print("Saved: models/gru/gru_error_distribution.png")

# ─── Save GRU config ─────────────────────────────────────────────────────────
gru_config = {
    'random_seed': RANDOM_SEED,
    'architecture': 'GRU',
    'input_size': len(feature_cols),
    'hidden_size': 128,
    'num_layers': 2,
    'dropout': 0.2,
    'output_size': 2,
    'batch_size': 128,
    'learning_rate': 1e-3,
    'max_epochs': 200,
    'early_stop_patience': 20,
    'feature_cols': feature_cols,
    'target_cols': target_cols,
    'pytorch_available': HAS_TORCH,
}
with open('models/gru/gru_config.json', 'w') as f:
    json.dump(gru_config, f, indent=2)

with open('models/gru/gru_results.json', 'w') as f:
    json.dump(results, f, indent=2)

print("Saved: models/gru/gru_config.json")
print("Saved: models/gru/gru_results.json")
