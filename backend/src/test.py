import joblib
import pandas as pd
import numpy as np
from sklearn.metrics import roc_auc_score, classification_report
import os
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3" 
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"
from tensorflow.keras.models import load_model
from sklearn.preprocessing import StandardScaler


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, '..', 'data', 'processed_data.csv')
MODEL_PATH = os.path.join(BASE_DIR, '..', '..', 'model', 'models')


def load():
     data = pd.read_csv(DATA_PATH)

     lstm = load_model(os.path.join(MODEL_PATH, 'lstm_model.keras'))
     print("LSTM model loaded successfully.")
     xgb = joblib.load(os.path.join(MODEL_PATH, 'xgboost_model.pkl'))
     print("XGBoost model loaded successfully.")
     ensemble = joblib.load(os.path.join(MODEL_PATH, 'ensemble_config.pkl'))
     print("Ensemble model loaded successfully.")
     scalers = joblib.load(os.path.join(MODEL_PATH, 'scalers.pkl'))
     print("Scalers loaded successfully.")
    
     return dict(
         data=data,
         lstm=lstm,
         xgb=xgb,
         ensemble=ensemble,
         scalers=scalers
     )

def create_sequences(X, y, lookback=60):
    X_seq, y_seq = [], []

    for i in range(lookback, len(X)):
            X_seq.append(X[i-lookback:i])
            y_seq.append(y[i])

    return np.array(X_seq), np.array(y_seq)

def prepare_data(data, scalers):
     
     X_seq_list, y_seq_list, X_xgb_list =  [], [], []

     for ticker in data['id_stock'].unique():
          print(f"Preparing data for ticker: {ticker}")
          df_ticker = data[data['id_stock'] == ticker].sort_values('recorded_at')
          scaler = scalers[ticker]
          X = scaler.transform(df_ticker.drop(columns=['id_stock', 'recorded_at', 'target']))
          y = df_ticker['target'].values
          X_seq , y_seq = create_sequences(X, y)
          X_xgb = X_seq[:,-1,:] #Serve para pegar o ultimo dia

          X_seq_list.append(X_seq)
          y_seq_list.append(y_seq)
          X_xgb_list.append(X_xgb)

     print("Data preparation completed.")
     return dict(
          X_seq = np.concatenate(X_seq_list, axis=0),
          y_seq = np.concatenate(y_seq_list, axis=0),
          X_xgb = np.concatenate(X_xgb_list, axis=0)
     )

def lstm_predict(lstm, X_seq):
     
     if len(X_seq) == 0:
          print("No sequences available for prediction.")
          return np.array([])

     lstm_predictions = lstm.predict(X_seq)

     return lstm_predictions

def xgb_predict(xgb, X_xgb):
     if len(X_xgb) == 0:
          print("No data available for XGBoost prediction.")
          return np.array([])

     xgb_predictions = xgb.predict_proba(X_xgb)

     return xgb_predictions

def ensemble_predict(ensemble, lstm_predictions, xgb_predictions):
     if len(lstm_predictions) == 0 or len(xgb_predictions) == 0:
          print("Insufficient predictions for ensemble.")
          return np.array([])

     ensemble_predictions = (
          (ensemble['peso_lstm'] * lstm_predictions.flatten()) +
          (ensemble['peso_xgb'] * xgb_predictions[:, 1])
     )

     return ensemble_predictions

def comparison(ensemble_predictions, xgb_predictions, lstm_predictions, y_seq):
     print("Comparing model predictions...")

     print(f"LSTM Predictions:")
     report_lstm = classification_report(y_seq, (lstm_predictions.flatten() >= 0.5).astype(int))
     print(report_lstm)

     print(f"XGBoost Predictions:")
     report_xgb = classification_report(y_seq, (xgb_predictions[:, 1] >= 0.5).astype(int))
     print(report_xgb)

     print(f"Ensemble Predictions:")
     auc_score = roc_auc_score(y_seq, ensemble_predictions)

     y_pred = (ensemble_predictions >= 0.5).astype(int)
     report = classification_report(y_seq, y_pred)
     print(f"ROC AUC Score: {auc_score:.4f}")
     print("Classification Report:")
     print(report)

if __name__ == "__main__":
     data, lstm, xgb, ensemble, scalers = load().values()
     X_seq, y_seq, X_xgb = prepare_data(data, scalers).values()
     lstm_predictions = lstm_predict(lstm, X_seq)
     xgb_predictions = xgb_predict(xgb, X_xgb)
     ensemble_predictions = ensemble_predict(ensemble, lstm_predictions, xgb_predictions)
     comparison(ensemble_predictions, xgb_predictions, lstm_predictions, y_seq)