import pandas as pd
from sklearn.preprocessing import StandardScaler
import joblib
import os
import xgboost as xgb
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from tensorflow.keras.layers import LSTM, Dropout, Dense, BatchNormalization
from tensorflow.keras.models import Sequential
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
from tensorflow.keras.optimizers import Adam
from sklearn.utils.class_weight import compute_class_weight
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, roc_auc_score, classification_report

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FEATURES_PATH = ['']
FILE_PATH = os.path.join(BASE_DIR, 'data', 'train.csv')

def split():
    column_drop = ["Date", 'Close', 'ticker']
    lookback= 60

    X_trains, X_vals, X_tests = [], [], []
    y_trains, y_vals, y_tests = [], [], []

    for ticker in df['ticker'].unique():
        df_t = df[df['ticker'] == ticker].copy()

        # Remove último dia de cada ticker (NaN do shift(-1))
        df_t = df_t.iloc[:-1]

        X_t = df_t.drop(columns=column_drop).values
        y_t = df_t['target'].values

        # Split temporal
        train_end = int(len(X_t) * 0.60)
        val_end   = int(len(X_t) * 0.70)

        X_tr, y_tr = X_t[:train_end],        y_t[:train_end]
        X_v,  y_v  = X_t[train_end:val_end], y_t[train_end:val_end]
        X_te, y_te = X_t[val_end:],          y_t[val_end:]

        # Normaliza
        scaler = StandardScaler()
        X_tr = scaler.fit_transform(X_tr)
        X_v  = scaler.transform(X_v)
        X_te = scaler.transform(X_te)

        # Janelas por ticker separado
        for i in range(lookback, len(X_tr)):
            X_trains.append(X_tr[i-lookback:i])
            y_trains.append(y_tr[i])

        for i in range(lookback, len(X_v)):
            X_vals.append(X_v[i-lookback:i])
            y_vals.append(y_v[i])

        for i in range(lookback, len(X_te)):
            X_tests.append(X_te[i-lookback:i])
            y_tests.append(y_te[i])

    X_train_lstm = np.array(X_trains)
    X_val_lstm   = np.array(X_vals)
    X_test_lstm  = np.array(X_tests)

    y_train_lstm = np.array(y_trains)
    y_val_lstm   = np.array(y_vals)
    y_test_lstm  = np.array(y_tests)

def lstm_train():
    pass

def xgb_train():
    pass

def train():
    pass
