import pandas as pd
from sklearn.preprocessing import StandardScaler
import joblib
import os
import xgboost as xgb
import mlflow
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

def train():
    pass