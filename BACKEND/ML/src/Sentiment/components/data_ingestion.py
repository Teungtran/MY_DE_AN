from src.Sentiment.utils.logging import logger
from src.Sentiment.entity.config_entity import DataIngestionConfig
from pathlib import Path
from sklearn.model_selection import train_test_split
import re
import pandas as pd
import contractions 
from tqdm import tqdm
from datetime import datetime, timezone
import numpy as np
from multiprocessing import Pool, cpu_count
import os
import hashlib
import pickle


# Global preprocessing function for multiprocessing
def preprocess_text_worker(review):
    """Simple text cleaning using regex only."""
    try:
        review = str(review).lower()
    except:
        return ""

    # Fast contraction expansion
    try:
        review = contractions.fix(review)
    except:
        pass

    # Remove URLs
    review = re.sub(r'https*\S+', ' ', review)
    # Remove mentions and hashtags
    review = re.sub(r'[@#]\S+', ' ', review)
    # Remove HTML tags
    review = re.sub(r'<.*?>', '', review)
    # Replace punctuation with spaces
    review = re.sub(r'[/(){}\[\]\|@,;]', ' ', review)
    # Keep only letters and spaces
    review = re.sub(r'[^a-z\s]', '', review)
    # Remove extra whitespace
    review = re.sub(r'\s+', ' ', review).strip()
    
    return review 

class DataIngestion:
    def __init__(self, config: DataIngestionConfig):
        self.config = config
        self.rows_processed = 0
        self.datetime_suffix = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        
        # Initialize text processing cache for faster repeat processing
        try:
            os.makedirs(self.config.data_version_dir, exist_ok=True)
            self.cache_file = os.path.join(self.config.data_version_dir, "text_processing_cache.pkl")
            self.text_cache = self._load_cache()
        except Exception as e:
            logger.warning(f"Could not initialize cache: {e}. Proceeding without cache.")
            self.cache_file = None
            self.text_cache = {}

    def _load_cache(self):
        """Load text processing cache from disk."""
        try:
            if self.cache_file and os.path.exists(self.cache_file):
                with open(self.cache_file, 'rb') as f:
                    return pickle.load(f)
        except Exception as e:
            logger.warning(f"Could not load cache: {e}")
        return {}

    def _save_cache(self):
        """Save text processing cache to disk."""
        try:
            if self.cache_file:
                os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
                with open(self.cache_file, 'wb') as f:
                    pickle.dump(self.text_cache, f)
        except Exception as e:
            logger.warning(f"Could not save cache: {e}")

    def _get_text_hash(self, text):
        """Generate hash for text to use as cache key."""
        return hashlib.md5(str(text).encode()).hexdigest()

    def _expand_contractions_fast(self, text: str) -> str:
        """Fast contraction expansion using precompiled regex."""
        try:
            return contractions.fix(text)
        except:
            return text

    def _preprocess_text_fast(self, review):
        """Simple text cleaning using regex only with caching."""
        text_hash = self._get_text_hash(review)
        if text_hash in self.text_cache:
            return self.text_cache[text_hash]
        
        try:
            review = str(review).lower()
        except:
            processed_text = ""
            self.text_cache[text_hash] = processed_text
            return processed_text

        # Fast contraction expansion
        try:
            review = contractions.fix(review)
        except:
            pass

        # Remove URLs
        review = re.sub(r'https*\S+', ' ', review)
        # Remove mentions and hashtags
        review = re.sub(r'[@#]\S+', ' ', review)
        # Remove HTML tags
        review = re.sub(r'<.*?>', '', review)
        # Replace punctuation with spaces
        review = re.sub(r'[/(){}\[\]\|@,;]', ' ', review)
        # Keep only letters and spaces
        review = re.sub(r'[^a-z\s]', '', review)
        # Remove extra whitespace
        processed_text = re.sub(r'\s+', ' ', review).strip()
        
        # Cache the result for future use
        self.text_cache[text_hash] = processed_text
        
        return processed_text

    def load_data(self):
        try:
            logger.info(f"Loading data from {self.config.local_data_file}")
            df = pd.read_csv(self.config.local_data_file, header=None)

            if df.shape[1] == 2:
                df.columns = ['sentiment', 'review']
            else:
                logger.info(f"Data has more than 2 columns ({df.shape[1]}), attempting column inference...")
                df.columns = [str(col).strip().lower() for col in df.columns]

                if 'sentiment' in df.columns and 'review' in df.columns:
                    df = df[['sentiment', 'review']]
                else:
                    review_col = None
                    sentiment_col = None

                    for col in df.columns:
                        if df[col].map(type).eq(str).all() and review_col is None:
                            review_col = col
                        elif df[col].dtype in [int, float] and sentiment_col is None:
                            unique_vals = df[col].dropna().unique()
                            if set(unique_vals).issubset({0, 1, 2}):
                                sentiment_col = col

                    if review_col and sentiment_col:
                        df = df[[sentiment_col, review_col]]
                        df.columns = ['sentiment', 'review']
                        logger.info(f"Inferred 'sentiment' column: {sentiment_col}, 'review' column: {review_col}")
                    else:
                        raise ValueError("Could not infer 'sentiment' and 'review' columns from dataset.")

            sentiment_map = {
                2: 1, 1: 0,
                'positive': 1, 'negative': 0,
                'pos': 1, 'neg': 0,
                'Positive': 1, 'Negative': 0
            }
            df['sentiment'] = df['sentiment'].map(sentiment_map).fillna(df['sentiment'])

            def safe_convert(val):
                try:
                    return int(val)
                except (ValueError, TypeError):
                    return val

            df['sentiment'] = df['sentiment'].apply(safe_convert).astype(float)

            if len(df) > 50000:
                logger.info(f"Dataset is large ({len(df)} rows), sampling 30k per sentiment...")
                df_clean = df.groupby('sentiment', group_keys=False).apply(
                lambda x: x.sample(n=min(30000, len(x)), random_state=42)  
                ).reset_index(drop=True)
            else:
                df_clean = df.copy().reset_index(drop=True)

            logger.info(f"Loaded dataset with clean data {len(df_clean)} rows")
            return df_clean

        except Exception as e:
            logger.error(f"Error in loading data: {e}")
            raise e

    def load_data_for_prediction(self):
        """
        Load data specifically for prediction - doesn't require sentiment column.
        Only needs text data for inference.
        """
        try:
            logger.info(f"Loading prediction data from {self.config.local_data_file}")
            
            # Try reading with header first, then without
            try:
                df = pd.read_csv(self.config.local_data_file)
                df.columns = df.columns.str.lower().str.strip()
                logger.info(f"Loaded data with headers: {list(df.columns)}")
            except:
                df = pd.read_csv(self.config.local_data_file, header=None)
                logger.info(f"Loaded data without headers, {df.shape[1]} columns detected")

            logger.info(f"Data shape: {df.shape}")
            
            return df

        except Exception as e:
            logger.error(f"Error in loading prediction data: {e}")
            raise e

    def save_data(self, df, df_processed):
        input_data_versioned_name = f"input_raw_sentiment_data_version_{self.datetime_suffix}.csv"
        processed_data_versioned_name = f"processed_sentiment_data_version_{self.datetime_suffix}.csv"
        input_data_versioned_path = Path(self.config.data_version_dir) / input_data_versioned_name
        processed_data_versioned_path = Path(self.config.data_version_dir) / processed_data_versioned_name

        if not input_data_versioned_path.exists():
            df.to_csv(input_data_versioned_path, index=False)
        if not processed_data_versioned_path.exists():
            df_processed.to_csv(processed_data_versioned_path, index=False)
            logger.info(f"Created versioned input data file: {input_data_versioned_path}")
            logger.info(f"Created versioned processed data file: {processed_data_versioned_path}")
        else:
            logger.info(f"Versioned file already exists: {input_data_versioned_path}, skipping save.")
            logger.info("Continuing with local processing...")

        return str(input_data_versioned_path), str(processed_data_versioned_path)

    def preprocess_data(self, df_clean):
        """Optimized preprocessing with multiprocessing for faster execution."""
        self.rows_processed = 0
        total_rows = len(df_clean)
        logger.info(f"Starting optimized preprocessing of {total_rows} rows...")

        # Use vectorized operations for better performance
        reviews = df_clean['review'].values
        
        # Determine optimal number of processes
        num_processes = min(cpu_count(), 4)
        chunk_size = max(1, total_rows // (num_processes * 2))
        
        if total_rows < 1000:
            # For small datasets, use single process to avoid overhead
            logger.info("Using single-threaded processing for small dataset")
            processed_reviews = [self._preprocess_text_fast(review) for review in tqdm(reviews)]
        else:
            # For larger datasets, use multiprocessing
            logger.info(f"Using multiprocessing with {num_processes} processes, chunk size: {chunk_size}")
            
            processed_reviews = []
            with Pool(processes=num_processes) as pool:
                results = list(tqdm(
                    pool.imap(preprocess_text_worker, reviews, chunksize=chunk_size),
                    total=total_rows,
                    desc="Processing reviews"
                ))
                processed_reviews = results

        df_clean['review'] = processed_reviews
        self.rows_processed = len(processed_reviews)
        logger.info(f"Completed optimized preprocessing. Total rows processed: {self.rows_processed}")
        
        # Save cache for future runs
        if len(self.text_cache) > 0:
            self._save_cache()
            logger.info(f"Saved {len(self.text_cache)} entries to text processing cache")
        
        return df_clean

    def split_data(self, df_clean):
        logger.info("Splitting data into train and test sets")
        train_data, test_data = train_test_split(
            df_clean,
            test_size=self.config.test_size,
            random_state=self.config.random_state
        )
        logger.info(f"Train data: {len(train_data)} rows, Test data: {len(test_data)} rows")
        return train_data, test_data

    def data_ingestion_pipeline(self):
        logger.info("Initiating data ingestion")
        df_load = self.load_data()
        df_processed = self.preprocess_data(df_load)
        train_data, test_data = self.split_data(df_processed)
        train_path, test_path = self.save_data(train_data, test_data)

        logger.info("Data ingestion completed successfully")
        logger.info(f"First few rows of processed data: \n{df_processed.head()}")
        return df_load, df_processed, train_path, test_path, train_data, test_data
