import os
import tensorflow as tf
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import (
    Embedding, SpatialDropout1D, Conv1D, 
    GlobalMaxPooling1D, Dense, Dropout
)
from datetime import datetime
import tempfile

import joblib as jb
import pandas as pd
import mlflow
from src.Sentiment.utils.logging import logger
from src.Sentiment.entity.config_entity import PrepareBaseModelConfig
tf.keras.__version__ = tf.__version__

class PrepareBaseModel:
    def __init__(self, config: PrepareBaseModelConfig):
        self.config = config
        self.datetime_suffix = datetime.now().strftime('%Y%m%dT%H%M%S')
        
    def get_base_model(self):
        """Create and return a base CNN model for sentiment analysis."""
        logger.info("Creating base CNN model")
        
        model = Sequential([
            Embedding(
                input_dim=self.config.num_words, 
                output_dim=self.config.embedding_dim, 
                input_length=self.config.maxlen
            ),
            SpatialDropout1D(self.config.dropout_rate),
            Conv1D(self.config.filters, self.config.kernel_size, padding='same', activation='relu'),
            GlobalMaxPooling1D(),
            Dropout(self.config.dropout_rate),
            Dense(1, activation='sigmoid')
        ])
        
        model.compile(
            optimizer='adam',
            loss='binary_crossentropy',
            metrics=['accuracy']
        )
        
        summary_lines = []
        model.summary(print_fn=lambda x: summary_lines.append(x))
        summary_text = "\n".join(summary_lines)

        # Log to your logger (optional)
        logger.info("Base model summary:\n%s", summary_text)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as temp_file:
            temp_file.write(summary_text)
            temp_path = temp_file.name

        mlflow.log_artifact(temp_path, artifact_path="model_summary")
        logger.info(f"Base model saved at: {self.config.model_version_dir}")
        return model
    
    def prepare_tokenizer(self, train_data):
        """Prepare and save tokenizer based on training data."""
        logger.info("Creating scaler from training data")
        
        os.makedirs(self.config.data_version_dir, exist_ok=True)
        os.makedirs(self.config.model_version_dir, exist_ok=True)
        tokenizer_path = os.path.join(self.config.model_version_dir, f"tokinezer_version_{self.datetime_suffix}.pkl")

        try:
            logger.info(f"Loading training data from: {train_data}")
            if "review" not in train_data.columns:
                raise ValueError("Column 'review' not found in training data.")
            original_count = len(train_data)
            train_data = train_data.dropna(subset=["review"])
            train_data["review"] = train_data["review"].astype(str)
            processed_count = len(train_data)
            dropped_count = original_count - processed_count
            logger.info(f"Tokenizer fitted on {processed_count} reviews (dropped {dropped_count} rows with missing 'review')")
            tokenizer = Tokenizer(num_words=self.config.params_num_words)
            tokenizer.fit_on_texts(train_data["review"])
            jb.dump(tokenizer, tokenizer_path)
            
            logger.info(f"Tokenizer saved at: {tokenizer_path}")
            return tokenizer_path , tokenizer

        except Exception as e:
            logger.error(f"Error in preparing tokenizer: {e}")
            raise e
    
    def full_model(self, train_data):
        """Create the base model and scaler."""
        logger.info("Creating base model and scaler")
        
        model = self.get_base_model()
        tokenizer_path , tokenizer= self.prepare_tokenizer(train_data=train_data)
        
        base_model_path = os.path.join(self.config.model_version_dir, f"base_model_sentiment_{self.datetime_suffix}.pkl")
        jb.dump(model, base_model_path)
        logger.info(f"Base model saved: {base_model_path}")
        mlflow.log_artifact(str(tokenizer_path))
        mlflow.log_artifact(str(base_model_path))
        return model, base_model_path, tokenizer_path , tokenizer
        