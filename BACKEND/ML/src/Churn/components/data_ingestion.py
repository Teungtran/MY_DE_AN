import os
import pandas as pd
from sklearn.model_selection import train_test_split
from imblearn.combine import SMOTEENN
from pathlib import Path
from datetime import datetime
from pandas import DataFrame

from src.Churn.utils.logging import logger
from src.Churn.entity.config_entity import DataIngestionConfig
from .support import most_common, get_dummies


class DataIngestion:
    def __init__(self, config: DataIngestionConfig):
        self.config = config
        self.rows_processed = 0
        self.datetime_suffix = datetime.now().strftime('%Y%m%dT%H%M%S')

    def process_data_for_churn(self, df_input: pd.DataFrame) -> pd.DataFrame:
        df_input = df_input.copy()
        df_input.columns = df_input.columns.map(lambda x: str(x).strip())

        cols_to_drop = {"Returns", "Age", "Total Purchase Amount"}
        df_input.drop(columns=[col for col in cols_to_drop if col in df_input.columns], inplace=True, errors='ignore')
        df_input = df_input.dropna().copy()

        if 'Price' not in df_input.columns:
            df_input['Price'] = df_input.get('Product Price')
        if 'Product Price' not in df_input.columns:
            raise KeyError("Required column 'Product Price' is missing from the dataset.")

        df_input['TotalSpent'] = df_input['Quantity'] * df_input['Price']

        df_features = df_input.groupby("customer_id", as_index=False, sort=False).agg(
            LastPurchaseDate=("Purchase Date", "max"),
            Favoured_Product_Categories=("Product Category", lambda x: most_common(list(x))),
            Frequency=("Purchase Date", "count"),
            TotalSpent=("TotalSpent", "sum"),
            Favoured_Payment_Methods=("Payment Method", lambda x: most_common(list(x))),
            Customer_Name=("Customer Name", "first"),
            Customer_Label=("Customer_Labels", "first"),
            Churn=("Churn", "first"),
        )

        df_features = df_features.drop_duplicates(subset=['Customer_Name'], keep='first')

        df_features['LastPurchaseDate'] = pd.to_datetime(df_features['LastPurchaseDate'])
        max_date = df_features["LastPurchaseDate"].max()
        df_features['Recency'] = (max_date - df_features['LastPurchaseDate']).dt.days
        df_features['Avg_Spend_Per_Purchase'] = df_features['TotalSpent'] / df_features['Frequency'].replace(0, 1)
        df_features['Purchase_Consistency'] = df_features['Recency'] / df_features['Frequency'].replace(0, 1)

        df_features.drop(columns=["customer_id", "LastPurchaseDate", 'Customer_Name'], inplace=True)

        for col in df_features.select_dtypes(include='int').columns:
            df_features[col] = df_features[col].astype('float64')

        return df_features

    def encode_churn(self, df_features: pd.DataFrame) -> pd.DataFrame:
        df_copy = df_features.copy()
        return get_dummies(df_copy)

    def load_data(self) -> pd.DataFrame:
        try:
            logger.info(f"Loading data from {self.config.local_data_file}")
            df = pd.read_csv(self.config.local_data_file)
            logger.info(f"Loaded dataset with {len(df)} rows")
            logger.info(f"Columns found: {list(df.columns)}")
            return df
        except Exception as e:
            logger.error(f"Error while loading data: {e}")
            raise

    def save_data(self, df, df_processed, df_features):
        input_name = f"input_raw_data_version_{self.datetime_suffix}.csv"
        processed_name = f"processed_data_version_{self.datetime_suffix}.csv"
        features_name = f"features_data_version_{self.datetime_suffix}.csv"

        input_path = Path(self.config.data_version_dir) / input_name
        processed_path = Path(self.config.data_version_dir) / processed_name
        features_path = Path(self.config.data_version_dir) / features_name

        if not input_path.exists():
            df.to_csv(input_path, index=False)
            logger.info(f"Saved input data to: {input_path}")
        if not processed_path.exists():
            df_processed.to_csv(processed_path, index=False)
            logger.info(f"Saved processed data to: {processed_path}")
        if not features_path.exists():
            df_features.to_csv(features_path, index=False)
            logger.info(f"Saved features data to: {features_path}")

    def preprocess_data(self, df_clean: pd.DataFrame):
        self.rows_processed = 0
        logger.info(f"Starting preprocessing of {len(df_clean)} rows...")
        logger.info(f"Initial columns: {list(df_clean.columns)}")

        df_features = self.process_data_for_churn(df_clean)
        logger.info(f"After feature engineering: {df_features.shape}")

        df_processed = self.encode_churn(df_features)
        logger.info(f"After encoding: {df_processed.shape}")

        df_processed = df_processed.dropna()
        logger.info(f"After dropping NaNs: {df_processed.shape}")

        if "Churn" not in df_processed.columns:
            logger.error("Churn column missing after preprocessing")
            raise KeyError("Churn column is missing after preprocessing")

        X = df_processed.drop("Churn", axis=1)
        y = df_processed["Churn"]

        logger.info(f"X shape: {X.shape}, y shape: {y.shape}")
        logger.info(f"Target value counts:\n{y.value_counts(normalize=True)}")

        if y.isna().sum() > 0:
            logger.warning(f"Filling {y.isna().sum()} missing target values with 0")
            y = y.fillna(0)

        nan_cols = X.columns[X.isna().any()].tolist()
        if nan_cols:
            logger.warning(f"Filling NaNs in columns: {nan_cols}")
            X = X.fillna(0)

        class_distribution = y.value_counts(normalize=True)
        min_max_ratio = class_distribution.min() / class_distribution.max()

        if min_max_ratio < 0.5:
            logger.info("Target variable is imbalanced. Applying SMOTEENN...")
            smote = SMOTEENN(random_state=42)
            X_res, y_res = smote.fit_resample(X, y)
            logger.info(f"Resampled shapes: X={X_res.shape}, y={y_res.shape}")
        else:
            logger.info("Target variable is balanced. Skipping SMOTEENN.")
            X_res, y_res = X, y

        return X_res, y_res, df_processed, df_features

    def split_data(self, X_res, y_res):
        logger.info("Splitting data into train and test sets")
        X_train, X_test, y_train, y_test = train_test_split(
            X_res, y_res, test_size=self.config.test_size, random_state=self.config.random_state
        )
        logger.info(f"Train: {X_train.shape}, Test: {X_test.shape}")
        return X_train, X_test, y_train, y_test

    def data_ingestion_pipeline(self):
        logger.info("Initiating data ingestion pipeline")
        df = self.load_data()
        X, y, df_processed, df_features = self.preprocess_data(df)
        self.save_data(df, df_processed, df_features)
        X_train, X_test, y_train, y_test = self.split_data(X, y)
        logger.info("Data ingestion completed")
        return X_train, X_test, y_train, y_test, df_processed, df, df_features
