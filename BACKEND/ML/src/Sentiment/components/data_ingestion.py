
from src.Churn.utils.logging import logger
from src.Churn.entity.config_entity import DataIngestionConfig
from pathlib import Path
from sklearn.model_selection import train_test_split
import re
import nltk
import pandas as pd
from nltk.corpus import stopwords
from nltk.corpus import opinion_lexicon
nltk.download('opinion_lexicon')
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
nltk.download('stopwords')
nltk.download('wordnet')
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')
from nltk.tag import pos_tag
import shutil
from tqdm import tqdm
import uuid
from datetime import datetime, timezone
class DataIngestion:
    def __init__(self, config: DataIngestionConfig):
        self.config = config
        self.rows_processed = 0
        self.datetime_suffix = datetime.now().strftime('%Y%m%dT%H%M%S')

    def _expand_contractions(self, text: str) -> str:
        """Expand contractions in text."""
        contractions = {
            "don't": 'do not', "can't": 'cannot', "won't": 'will not', "isn't": 'is not',
            "aren't": 'are not', "wasn't": 'was not', "weren't": 'were not', "hasn't": 'has not',
            "haven't": 'have not', "hadn't": 'had not', "doesn't": 'does not', "didn't": 'did not',
            "shouldn't": 'should not', "couldn't": 'could not', "wouldn't": 'would not', "mightn't": 'might not',
            "mustn't": 'must not', "needn't": 'need not'
        }
        
        for contraction, expanded in contractions.items():
            text = text.replace(contraction, expanded)
        return text

    def _preprocess_text(self, review):
        """Preprocess review text."""
        REPLACE_BY_SPACE_RE = re.compile('[/(){}\[\]\|@,;]')
        BAD_SYMBOLS_RE = re.compile('[^0-9a-z #+_]')
        NEGATIVE_WORDS = set(opinion_lexicon.negative())
        POSITIVE_WORDS = set(opinion_lexicon.positive())
        
        # Remove noise data
        try:
            review = str(review).lower()
        except Exception as e:
            logger.warning(f"Review conversion error: {e}, setting to empty string.")
            review = ""
            
        review = self._expand_contractions(review)
        review = REPLACE_BY_SPACE_RE.sub(' ', review)
        review = BAD_SYMBOLS_RE.sub('', review)
        review = re.sub(r'https*\S+', ' ', review)  # Remove URLs
        review = re.sub(r'[@#]\S+', ' ', review)   # Remove mentions and hashtags
        review = re.sub('<.*?>', '', review)       # Remove HTML tags
        
        tokenizer = word_tokenize(review)
        stop_words = set(stopwords.words('english')) - NEGATIVE_WORDS - POSITIVE_WORDS
        tokens = [token for token in tokenizer if token not in stop_words]
        
        lemmatizer = WordNetLemmatizer()
        tokens = [lemmatizer.lemmatize(word) for word in tokens]
        
        tagged_tokens = pos_tag(tokens)
        IMPORTANT_POS = {
            'JJ', 'JJR', 'JJS',  
            'RB', 'RBR', 'RBS',  
            'VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ',  
            'NN', 'NNS', 'NNP', 'NNPS', 
            'MD'  
        }    
        processed_tokens = [
            lemmatizer.lemmatize(word.lower())
            for word, tag in tagged_tokens
            if tag in IMPORTANT_POS and len(word) >= 2
        ]
        
        processed_review = ' '.join(processed_tokens)
        return processed_review

    def load_data(self):
        """Load the dataset from CSV file."""
        try:
            logger.info(f"Loading data from {self.config.local_data_file}")
            df = pd.read_csv(self.config.local_data_file, header=None)
            df.columns = ['sentiment', 'review']
            sentiment_map = {
                2: 1,
                1: 0,
                'positive': 1,
                'negative': 0,
                'pos': 1,
                'neg': 0,
                'Positive': 1,
                'Negative': 0
            }
            df['sentiment'] = df['sentiment'].map(sentiment_map).fillna(df['sentiment'])
            def safe_convert(val):
                try:
                    return int(val)
                except (ValueError, TypeError):
                    return val
            df['sentiment'] = df['sentiment'].apply(safe_convert)
            if len(df) > 50000:
                logger.info(f"Dataset is large ({len(df)} rows)")
                df_clean = df.groupby('sentiment', group_keys=False).apply(
                    lambda x: x.sample(n=30000, random_state=self.config.random_state)
                )
                df_clean = df_clean.reset_index(drop=True)
            else:
                df_clean = df.copy()
                df_clean = df_clean.reset_index(drop=True)
                
            logger.info(f"Loaded dataset with clean data {len(df_clean)} rows")
            return df_clean
        except Exception as e:
            logger.error(f"Error in loading data: {e}")
            raise e
        
    def save_data(self, df, df_processed):
            input_data_versioned_name = f"input_raw_sentiment_data_version_{self.datetime_suffix}.csv"
            processed_data_versioned_name = f"processed_sentiment_data_version_{self.datetime_suffix}.csv"
            input_data_versioned_path = Path(self.config.data_version_dir) / input_data_versioned_name
            processed_data_versioned_name = Path(self.config.data_version_dir) / processed_data_versioned_name
            if not input_data_versioned_path.exists():
                df.to_csv(input_data_versioned_path, index=False)
            if not processed_data_versioned_name.exists():
                df_processed.to_csv(processed_data_versioned_name, index=False)
                logger.info(f"Created versioned input data file: {input_data_versioned_path}")
                logger.info(f"Created versioned processed data file: {processed_data_versioned_name}")
            else:
                logger.info(f"Versioned file already exists: {input_data_versioned_path}, skipping save.")
                logger.info("Continuing with local processing...")
                
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
        """Split data into training and testing sets."""
        logger.info("Splitting data into train and test sets")
        train_data, test_data = train_test_split(
            df_clean, 
            test_size=self.config.test_size,
            random_state=self.config.random_state
        )
        logger.info(f"Train data: {len(train_data)} rows, Test data: {len(test_data)} rows")
        return train_data, test_data


    def data_ingestion_pipeline(self):
        """Main method to perform data ingestion."""
        logger.info("Initiating data ingestion")
        df_load = self.load_data()
        df_processed = self.preprocess_data(df_load)
        train_data, test_data = self.split_data(df_processed)
        train_path, test_path = self.save_data(train_data, test_data)
        
        logger.info("Data ingestion completed successfully")
        logger.info(f"First few rows of processed data: \n{df_processed.head()}")
        return df_processed, train_path, test_path,train_data,test_data
