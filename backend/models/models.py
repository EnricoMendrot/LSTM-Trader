from sqlalchemy import Boolean, create_engine, Column, Integer, String, DateTime, ForeignKey, Numeric, Index, UniqueConstraint 
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy_utils import ChoiceType
from datetime import datetime, timezone
from pathlib import Path

backend_dir = Path(__file__).parent.parent
database_dir = backend_dir / 'database'
database_dir.mkdir(exist_ok=True) 

db_path = database_dir / 'banco_exemplo.db'



# Cria a engine
engine = create_engine(
    f'sqlite:///{db_path}',
    connect_args={'check_same_thread': False}  # Importante para SQLite
)

db = engine.connect()

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id_user = Column("id_user", Integer, primary_key=True, autoincrement=True)
    name = Column("name", String(100), nullable=False)
    password_hash = Column("password_hash", String(255), nullable=False)
    email = Column("email", String(254), unique=True, nullable=False)
    created_at = Column("created_at", DateTime,default=lambda: datetime.now(timezone.utc), nullable=False)

    def __init__(self, name, password_hash, email, created_at):
        self.name = name
        self.password_hash = password_hash
        self.email = email
        self.created_at = created_at

class Stock(Base):
    __tablename__ = 'stocks'

    id_stock = Column("id_stock", Integer, primary_key=True, autoincrement=True)
    ticker = Column("ticker", String(10), unique=True, nullable=False)
    company_name = Column("company_name", String(100), nullable=False)
    sector = Column("sector", String(100), nullable=False)
    exchange = Column("exchange", String(100), nullable=False)

    def __init__(self, ticker, company_name, sector, exchange):
        self.ticker = ticker
        self.company_name = company_name
        self.sector = sector
        self.exchange = exchange

class Portfolio(Base):
    __tablename__ = 'portfolios'

    id_port = Column("id_port", Integer, primary_key=True, autoincrement=True)
    id_user = Column("id_user", ForeignKey("users.id_user"), nullable=False)
    created_at = Column("created_at", DateTime,default=lambda: datetime.now(timezone.utc), nullable=False)

    def __init__(self, id_user, created_at):
        self.id_user = id_user
        self.created_at = created_at

class PortfolioStock(Base):
    __tablename__ = 'portfolio_stocks'

    id_port_stock = Column("id_port_stock", Integer, primary_key=True, autoincrement=True)
    id_port = Column("id_port", ForeignKey("portfolios.id_port"), nullable=False)
    id_stock = Column("id_stock", ForeignKey("stocks.id_stock"), nullable=False)
    amount = Column("amount", Numeric(10, 4), nullable=False)
    average_price = Column("average_price", Numeric(15, 4), nullable=False)

    def __init__(self, id_port, id_stock, amount, average_price):
        self.id_port = id_port
        self.id_stock = id_stock
        self.amount = amount
        self.average_price = average_price
    
    __table_args__ = (
        UniqueConstraint("id_stock", "id_port", name="uq_stock_port"),
    )

class Prediction(Base):
    __tablename__ = 'predictions'

    id_prev = Column("id_prev", Integer, primary_key=True, autoincrement=True)
    id_stock = Column("id_stock", ForeignKey("stocks.id_stock"), nullable=False)
    version_model = Column("version_model", String(100), nullable=False)
    prob_lstm = Column("prob_lstm", Numeric(15, 4), nullable=False)
    prob_xgboost = Column("prob_xgb", Numeric(15, 4), nullable=False)
    prob_ensemble = Column("prob_ensemble", Numeric(15, 4), nullable=False)
    final_forecast = Column("final_forecast", Numeric(15, 4), nullable=False)
    confidence_score = Column("confidence_score", Numeric(15, 4), nullable=False)
    forecast_date = Column("forecast_date", DateTime,default=lambda: datetime.now(timezone.utc), nullable=False)
    target_date = Column("target_date", DateTime, nullable=False)

    def __init__(self, id_stock, version_model, prob_lstm, prob_xgboost, prob_ensemble, final_forecast, confidence_score, forecast_date, target_date):
        self.id_stock = id_stock
        self.version_model = version_model
        self.prob_lstm = prob_lstm
        self.prob_xgboost = prob_xgboost
        self.prob_ensemble = prob_ensemble
        self.final_forecast = final_forecast
        self.confidence_score = confidence_score
        self.forecast_date = forecast_date
        self.target_date = target_date

    __table_args__ = (
        Index("idx_stock_forecast_date", "id_stock", "forecast_date"),
    )

class RealtimePrice(Base):
    __tablename__ = 'realtime_prices'

    id_temp = Column("id_temp", Integer, primary_key=True, autoincrement=True)
    id_stock = Column("id_stock", ForeignKey("stocks.id_stock"), nullable=False, unique=True)
    current_price = Column("current_price", Numeric(15, 4), nullable=False)
    open_price = Column("open_price", Numeric(15, 4), nullable=False)
    price_high = Column("price_high", Numeric(15, 4), nullable=False)
    price_low = Column("price_low", Numeric(15, 4), nullable=False)
    volume = Column("volume", Numeric(15, 4), nullable=False)
    percent_change = Column("percent_change", Numeric(15, 4), nullable=False)
    updated_at = Column("updated_at", DateTime, default=lambda: datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc), nullable=False)

    def __init__(self, id_stock, current_price, open_price, price_high, price_low, volume, percent_change, updated_at):
        self.id_stock = id_stock
        self.current_price = current_price
        self.open_price = open_price
        self.price_high = price_high
        self.price_low = price_low
        self.volume = volume
        self.percent_change = percent_change
        self.updated_at = updated_at

class PriceHistory(Base):
    __tablename__ = 'price_history'

    id_hist = Column("id_hist", Integer, primary_key=True, autoincrement=True)
    id_stock = Column("id_stock", ForeignKey("stocks.id_stock"), nullable=False)
    recorded_at = Column("recorded_at", DateTime, nullable=False)
    close = Column("close", Numeric(15, 4), nullable=False)
    open_price = Column("open_price", Numeric(15, 4), nullable=False)
    price_high = Column("price_high", Numeric(15, 4), nullable=False)
    price_low = Column("price_low", Numeric(15, 4), nullable=False)
    volume = Column("volume", Numeric(15, 4), nullable=False)

    def __init__(self, id_stock, recorded_at, open_price, price_high, price_low, close, volume):
        self.id_stock = id_stock
        self.recorded_at = recorded_at
        self.open_price = open_price
        self.price_high = price_high
        self.price_low = price_low
        self.close = close
        self.volume = volume
    
    __table_args__ = (
        Index("idx_stock_recorded_at", "id_stock", "recorded_at"),
    )

class Alert(Base):
    __tablename__ = 'alerts'

    id_alert = Column("id_alert", Integer, primary_key=True, autoincrement=True)
    id_port = Column("id_port", ForeignKey("portfolios.id_port"), nullable=False)
    id_prev = Column("id_prev", ForeignKey("predictions.id_prev"), nullable=False)
    id_stock = Column("id_stock", ForeignKey("stocks.id_stock"), nullable=False)
    alert_type = Column("alert_type", String(100), nullable=False)
    threshold_value = Column("threshold_value", Numeric(15, 4), nullable=False)
    is_active = Column("is_active", Boolean, nullable=False, default=False)

    def __init__(self, id_port, id_prev, id_stock, alert_type, threshold_value, is_active):
        self.id_port = id_port
        self.id_prev = id_prev
        self.id_stock = id_stock
        self.alert_type = alert_type
        self.threshold_value = threshold_value
        self.is_active = is_active