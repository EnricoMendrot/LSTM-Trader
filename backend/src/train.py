import pandas as pd
import os
import joblib
import xgboost as xgb
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3" 
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
from tensorflow.keras.layers import LSTM, Dropout, Dense, BatchNormalization
from tensorflow.keras.models import Sequential
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
from tensorflow.keras.optimizers import Adam
from sklearn.utils.class_weight import compute_class_weight
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score, classification_report

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILE_PATH = os.path.join(BASE_DIR, '..', 'data', 'processed_data.csv')

lookback       = 60
lstm_units_1   = 64
lstm_units_2   = 32
dropout        = 0.3
epochs         = 200
batch_size     = 32
xgb_estimators = 500
xgb_lr         = 0.02
depth          = 4

def load_data():
     df = pd.read_csv(FILE_PATH)
     column_drop = ["recorded_at", 'id_stock', 'target']
     return [df, column_drop]

def split(df, column_drop):

    lookback= 60

    X_trains, X_vals, X_tests = [], [], []
    y_trains, y_vals, y_tests = [], [], []

    scalers = {}
    for ticker in df['id_stock'].unique():
        df_t = df[df['id_stock'] == ticker].copy()

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

        scalers[ticker] = scaler

    X_train_lstm = np.array(X_trains)
    X_val_lstm   = np.array(X_vals)
    X_test_lstm  = np.array(X_tests)

    y_train_lstm = np.array(y_trains)
    y_val_lstm   = np.array(y_vals)
    y_test_lstm  = np.array(y_tests)
   
    print(f"Target treino:    {y_train_lstm.mean():.2f}")
    print(f"Target validação: {y_val_lstm.mean():.2f}")
    print(f"Target teste:     {y_test_lstm.mean():.2f}")
    print(f"Shape treino:     {X_train_lstm.shape}")
    return [X_train_lstm, X_val_lstm, X_test_lstm, y_train_lstm, y_val_lstm, y_test_lstm, scalers]

def callbacks(y_train_lstm):
    early_stop = EarlyStopping(
        monitor='val_loss',
        patience=10,
        restore_best_weights=True,
    )

    reduce_lr = ReduceLROnPlateau(
        monitor="val_loss",
        factor=0.5,
        patience=3,
        min_lr=0.00001,
        verbose=1
    )

    classes = np.unique(y_train_lstm)
    weights = compute_class_weight('balanced', classes=classes, y=y_train_lstm)

    return [early_stop, reduce_lr, dict(zip(classes, weights))]

def lstm_train(X_train_lstm, X_val_lstm, y_train_lstm, y_val_lstm):
    early_stop, reduce_lr, class_weight = callbacks(y_train_lstm)

    modelo_lstm = Sequential([
        LSTM(lstm_units_1, input_shape=(lookback, X_train_lstm.shape[2]), return_sequences=True),
        BatchNormalization(),
        Dropout(dropout),

        LSTM(lstm_units_2),
        Dropout(dropout),

        Dense(16, activation="relu"),
        Dense(1, activation="sigmoid")
    ])

    modelo_lstm.compile(
        optimizer=Adam(learning_rate=0.001, clipnorm=1.0),
        loss='binary_crossentropy',
        metrics=["accuracy"]
        )

    X_train_lstm = X_train_lstm.astype(np.float32)

    history = modelo_lstm.fit(
        X_train_lstm,
        y_train_lstm,
        epochs=epochs,
        batch_size=batch_size,
        verbose=1,
        validation_data=(X_val_lstm, y_val_lstm),
        callbacks=[early_stop, reduce_lr],
        class_weight=class_weight
        )
    
    return modelo_lstm, history

def xgb_train(X_train_lstm, X_val_lstm, y_train_lstm, y_val_lstm):

    X_train_xgb = X_train_lstm[:, -1, :]
    X_val_xgb   = X_val_lstm[:, -1, :]

    modelo_xgb = xgb.XGBClassifier(
    n_estimators=xgb_estimators,
    max_depth=depth,
    learning_rate=xgb_lr,
    subsample=0.8,
    colsample_bytree=0.8,
    eval_metric="logloss",
    early_stopping_rounds=20,
    scale_pos_weight=len(y_train_lstm[y_train_lstm==0]) / len(y_train_lstm[y_train_lstm==1])
    )
    modelo_xgb.fit(
        X_train_xgb, y_train_lstm,
        eval_set=[(X_val_xgb, y_val_lstm)],
        verbose=50
    )

    return modelo_xgb

def save_model(modelo_lstm, modelo_xgb, df, scalers):
    MODELS_DIR = os.path.join(BASE_DIR, "..", "..", "model", "models")
    os.makedirs(MODELS_DIR, exist_ok=True)

    # 1. Salva o XGBoost
    save_xgb =joblib.dump(modelo_xgb, os.path.join(MODELS_DIR, "xgboost_model.pkl"))
    print("XGBoost salvo!")

    # 2. Salva o LSTM
    save_lstm = modelo_lstm.save(os.path.join(MODELS_DIR, "lstm_model.keras"))  
    print("LSTM salvo!")

    save_scalers = joblib.dump(scalers, os.path.join(MODELS_DIR, "scalers.pkl"))
    print("Scalers salvos!")

    # Salva o Ensemble
    ensemble_config = {
        "lookback": lookback,
        "threshold": 0.45,
        "peso_lstm": 0.5,
        "peso_xgb": 0.5,
        "features": list(df.drop(columns=['recorded_at', 'id_stock']).columns),
        "tickers": list(df['id_stock'].unique())
    }

    save_ensemble = joblib.dump(ensemble_config, os.path.join(MODELS_DIR, "ensemble_config.pkl"))
    print("Configuração do Ensemble salva!")

    return [save_xgb, save_lstm, save_scalers, save_ensemble]

def predict(lstm_model_trained, xgb_model_trained, X_test_lstm):
    X_test_xgb = X_test_lstm[:, -1, :]

    # XGBoost no teste
    prob_xgb_test  = xgb_model_trained.predict_proba(X_test_xgb)[:, 1]
    pred_xgb_test  = (prob_xgb_test > 0.35).astype(int)

    # LSTM no teste
    prob_lstm_test = lstm_model_trained.predict(X_test_lstm).flatten()
    pred_lstm_test = (prob_lstm_test > 0.4).astype(int)

    # Ensemble
    prob_final_test = (prob_lstm_test + prob_xgb_test) / 2
    pred_final_test = (prob_final_test > 0.35).astype(int)

    return[prob_final_test, pred_final_test, prob_lstm_test, pred_lstm_test, prob_xgb_test, pred_xgb_test]

def grafico(pred_lstm_test, prob_lstm_test, pred_xgb_test, prob_xgb_test, pred_final_test, prob_final_test):
    resultados = {
    "LSTM": {"y_pred": pred_lstm_test, "y_prob": prob_lstm_test},
    "XGBoost": {"y_pred": pred_xgb_test, "y_prob": prob_xgb_test},
    "Ensemble": {"y_pred": pred_final_test, "y_prob": prob_final_test},
    }

    linhas = []
    for modelo, dados in resultados.items():
        report = classification_report(y_test_lstm, dados["y_pred"], output_dict=True)
        auc = roc_auc_score(y_test_lstm, dados["y_prob"])

        linhas.append({"Modelo": modelo, "Métrica": "Precision", "Valor": report["1"]["precision"]})
        linhas.append({"Modelo": modelo, "Métrica": "Recall", "Valor": report["1"]["recall"]})
        linhas.append({"Modelo": modelo, "Métrica": "F1-Score", "Valor": report["1"]["f1-score"]})
        linhas.append({"Modelo": modelo, "Métrica": "ROC-AUC", "Valor": auc})

    df_metrics = pd.DataFrame(linhas)

    sns.set_style("whitegrid")

    plt.figure(figsize=(10, 6))
    ax = sns.barplot(data=df_metrics, x="Métrica", y="Valor", hue="Modelo",
                    palette="viridis")

    for container in ax.containers:
        ax.bar_label(container, fmt="%.2f", padding=3, fontsize=9, fontweight="bold")

    plt.title("Comparação de Métricas entre Modelos", fontsize=14, fontweight="bold")
    plt.ylabel("Valor", fontsize=11)
    plt.xlabel("Métrica", fontsize=11)
    plt.ylim(0, 1.05)
    plt.legend(title="Modelo", frameon=True)
    sns.despine(left=True)
    plt.tight_layout()

    os.makedirs("reports", exist_ok=True)
    plt.savefig("reports/metrics_comparison.png", dpi=300, bbox_inches="tight")
    plt.show()
        
def train(df, X_train_lstm, X_val_lstm, y_train_lstm, y_val_lstm, scalers):
    lstm_model_trained, lstm_history = lstm_train(X_train_lstm, X_val_lstm, y_train_lstm, y_val_lstm)
    xgb_model_trained = xgb_train(X_train_lstm, X_val_lstm, y_train_lstm, y_val_lstm)
    model_save = save_model(lstm_model_trained, xgb_model_trained, df, scalers)
   
    
    return [lstm_model_trained, xgb_model_trained, model_save]

if __name__ == "__main__":
    df, column_drop = load_data()
    X_train_lstm, X_val_lstm, X_test_lstm, y_train_lstm, y_val_lstm, y_test_lstm, scalers = split(df, column_drop)
    lstm_model_trained, xgb_model_trained, model_save = train(df, X_train_lstm, X_val_lstm, y_train_lstm, y_val_lstm, scalers)
    prob_final_test, pred_final_test, prob_lstm_test, pred_lstm_test, prob_xgb_test, pred_xgb_test = predict(lstm_model_trained, xgb_model_trained, X_test_lstm)
    grafico(pred_lstm_test, prob_lstm_test, pred_xgb_test, prob_xgb_test, pred_final_test, prob_final_test)
    
    print(" # ========================== LSTM ========================== #")
    print(classification_report(y_test_lstm, pred_lstm_test))

    print(" # ========================== XGBoost ========================== #")
    print(classification_report(y_test_lstm, pred_xgb_test))

    print(" # ========================== Ensemble ========================== #")
    print(classification_report(y_test_lstm, pred_final_test))
    print(f"ROC-AUC Ensemble: {roc_auc_score(y_test_lstm, prob_final_test):.4f}")

