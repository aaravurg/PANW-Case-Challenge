"""
Configuration settings for the PANW Case Challenge API.
"""
import os
from pathlib import Path

# Base directory (project root)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Environment file path
ENV_FILE = BASE_DIR / '.env'

# Data file paths
TRANSACTIONS_CSV = BASE_DIR / 'sample_transactions_1000_sorted.csv'

# API Configuration
CORS_ORIGINS = ["http://localhost:3000"]

# Default query parameters
DEFAULT_USER_ID = "default_user"
DEFAULT_INSIGHTS_TOP_N = 7
DEFAULT_INSIGHTS_BUFFER = 5
DEFAULT_LOOKBACK_MONTHS = 3

# Tax and financial constants
DEFAULT_TAX_RATE = 0.25
DISCRETIONARY_CUT_PERCENTAGE = 0.7

# Prophet forecasting settings
PROPHET_MIN_DATA_POINTS = 4
PROPHET_CONFIDENCE_INTERVAL = 0.80
PROPHET_CHANGEPOINT_SCALE = 0.05

# Subscription detection thresholds
SUBSCRIPTION_INTERVAL_CV_THRESHOLD = 0.20
SUBSCRIPTION_AMOUNT_CV_THRESHOLD = 0.15
SUBSCRIPTION_FUZZY_MATCH_THRESHOLD = 85

# Logging configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
