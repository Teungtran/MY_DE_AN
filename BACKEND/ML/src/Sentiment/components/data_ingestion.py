from src.Sentiment.utils.logging import logger
from src.Sentiment.entity.config_entity import DataIngestionConfig
from pathlib import Path
from sklearn.model_selection import train_test_split
import re
import nltk
import pandas as pd
from nltk.corpus import stopwords
from nltk.corpus import opinion_lexicon
import contractions 
nltk.download('opinion_lexicon')
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
nltk.download('stopwords')
nltk.download('wordnet')
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')
from nltk.tag import pos_tag
from tqdm import tqdm
from datetime import datetime, timezone 

class DataIngestion:
    def __init__(self, config: DataIngestionConfig):
        self.config = config
        self.rows_processed = 0
        self.datetime_suffix = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')

    def _expand_contractions(self, text: str) -> str:
        """Expand contractions using `contractions` lib."""
        return contractions.fix(text)

    def _preprocess_text(self, review):
        REPLACE_BY_SPACE_RE = re.compile('[/(){}\[\]\|@,;]')
        BAD_SYMBOLS_RE = re.compile('[^0-9a-z #+_]')
        NEGATIVE_WORDS = set(opinion_lexicon.negative())
        POSITIVE_WORDS = set(opinion_lexicon.positive())

        try:
            review = str(review).lower()
        except Exception as e:
            logger.warning(f"Review conversion error: {e}, setting to empty string.")
            review = ""

        review = self._expand_contractions(review)
        review = REPLACE_BY_SPACE_RE.sub(' ', review)
        review = BAD_SYMBOLS_RE.sub('', review)
        review = re.sub(r'https*\S+', ' ', review)
        review = re.sub(r'[@#]\S+', ' ', review)
        review = re.sub('<.*?>', '', review)

        tokenizer = word_tokenize(review)
        stop_words = set(stopwords.words('english')) - NEGATIVE_WORDS - POSITIVE_WORDS
        tokens = [token for token in tokenizer if token not in stop_words]

        lemmatizer = WordNetLemmatizer()
        tokens = [lemmatizer.lemmatize(word) for word in tokens]

        tagged_tokens = pos_tag(tokens)
        IMPORTANT_POS = {'JJ', 'JJR', 'JJS', 'RB', 'RBR', 'RBS',
                        'VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ',
                        'NN', 'NNS', 'NNP', 'NNPS', 'MD'}
        processed_tokens = [
            lemmatizer.lemmatize(word.lower())
            for word, tag in tagged_tokens
            if tag in IMPORTANT_POS and len(word) >= 2
        ]
        return ' '.join(processed_tokens)

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
        self.rows_processed = 0
        print(f"Starting preprocessing of {len(df_clean)} rows...")

        processed_reviews = []
        for idx, review in tqdm(enumerate(df_clean['review']), total=len(df_clean)):
            cleaned_review = self._preprocess_text(review)
            processed_reviews.append(cleaned_review)
            self.rows_processed += 1

        df_clean['review'] = processed_reviews
        logger.info(f"Completed preprocessing. Total rows processed: {self.rows_processed}")
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
