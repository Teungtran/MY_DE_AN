import os
import matplotlib
import mlflow.tensorflow
matplotlib.use('Agg')  # Set non-interactive backend before importing pyplot
import matplotlib.pyplot as plt
import joblib as jb
from pathlib import Path
import seaborn as sns
from datetime import datetime
from sklearn.metrics import (
    roc_auc_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report, roc_curve, auc,precision_recall_curve, average_precision_score
)
import tensorflow as tf
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
from tensorflow.keras.models import load_model
from pathlib import Path
import mlflow
from mlflow import register_model
import uuid
from src.Sentiment.utils.logging import logger
from src.Sentiment.entity.config_entity import TrainingConfig, EvaluationConfig
from src.Sentiment.utils.common import save_json
tf.keras.__version__ = tf.__version__

class MLflowCallback(tf.keras.callbacks.Callback):
    """Callback for logging metrics to MLflow."""
    def __init__(self, model_name):
        self.model_name = model_name
        
    def on_epoch_end(self, epoch, logs=None):
        logs = logs or {}
        for metric_name, metric_value in logs.items():
            mlflow.log_metric(f"{self.model_name}_{metric_name}", metric_value, step=epoch)
            
            
class TrainAndEvaluateModel:
    def __init__(self, config_train: TrainingConfig, config_eval: EvaluationConfig = None):
        self.train_config = config_train
        self.eval_config = config_eval
        self.datetime_suffix = datetime.now().strftime('%Y%m%dT%H%M%S')
        self.model_name = f"model_sentiment_{self.datetime_suffix}"
    def log_model_to_mlflow(self, model, model_name: str):
        logger.info(f"Logging model to MLflow as {model_name}")
        try:
            # Log the model to the current run
            mlflow.tensorflow.log_model(model, model_name)
            run_id = mlflow.active_run().info.run_id
            artifact_uri = f"runs:/{run_id}/{model_name}"
            
            model_id = uuid.uuid4().hex[:8]
            registered_model_name = f"CNN_{model_id}"
            
            mlflow.register_model(model_uri=artifact_uri, name=registered_model_name)

            logger.info(f"Successfully registered model under unique name: {registered_model_name}")
        except Exception as e:
            logger.warning(f"Failed to log or register model to MLflow: {e}")
            logger.warning("Continuing without MLflow model registration")
    def get_callbacks(self):
        """Get callbacks for model training."""
        return [
            MLflowCallback(self.model_name),
            ReduceLROnPlateau(
                monitor='val_loss',
                factor=0.5,
                patience=2,
                min_lr=1e-5
            ),
            EarlyStopping(
                monitor='val_loss',
                patience=3,
                restore_best_weights=True
            )
        ]

    def prepare_data_for_training(self, train_data, test_data,tokenizer):
        train_data = train_data.dropna(subset=["review"])
        train_data["review"] = train_data["review"].astype(str)
        test_data = test_data.dropna(subset=["review"])
        test_data["review"] = test_data["review"].astype(str)
        logger.info("Converting text to sequences")
        X_train = pad_sequences(
            tokenizer.texts_to_sequences(train_data["review"]), 
            maxlen=self.train_config.maxlen
        )
        X_test = pad_sequences(
            tokenizer.texts_to_sequences(test_data["review"]), 
            maxlen=self.train_config.maxlen
        )
        y_train = train_data["sentiment"]
        y_test = test_data["sentiment"]
        
        logger.info(f"Training data shape: {X_train.shape}")
        logger.info(f"Test data shape: {X_test.shape}")
        
        return X_train, y_train, X_test, y_test
    
    def train(self, X_train, y_train, model):
        """Train the model."""
        logger.info(f"Loading model: {model}")
        logger.info(f"Starting model training for {self.model_name}")
        history = model.fit(
            X_train, y_train,
            epochs=self.train_config.epochs,
            batch_size=self.train_config.batch_size,
            validation_split=self.train_config.validation_split,
            callbacks=self.get_callbacks()
        )
        logger.info(f"Model training for {self.model_name} completed")
        model_version_dir = str(self.train_config.model_version_dir)
        os.makedirs(model_version_dir, exist_ok=True)
        
        trained_model_path_versioned = os.path.join(model_version_dir, f"model_sentiment_version_{self.datetime_suffix}.h5")
        
        model.save(trained_model_path_versioned)
        logger.info(f"  trained model file (for future use): {trained_model_path_versioned}")
        return model, history
    

    def perform_detailed_evaluation(self, model, X_test, y_test):
        """Evaluate the model in detail and log results to MLflow."""
        logger.info("Performing detailed evaluation on test data")
        
        y_pred_prob = model.predict(X_test)
        y_pred = (y_pred_prob > 0.5).astype(int)
        
        precision = precision_score(y_test, y_pred)
        recall = recall_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred)
        
        metrics = {
            "precision": float(precision),
            "recall": float(recall),
            "f1_score": float(f1)
        }
        
        report = classification_report(y_test, y_pred, output_dict=True)
        metrics["classification_report"] = report
        
        os.makedirs(self.eval_config.evaluation_dir, exist_ok=True)
        metrics_file_versioned = Path(self.eval_config.evaluation_dir) / f"metrics_{self.datetime_suffix}.json"
        
        save_json(metrics_file_versioned, metrics)
        logger.info(f"Detailed metrics saved to: {self.eval_config.metrics_file}")
        
        mlflow.log_metrics({
            "precision": precision,
            "recall": recall,
            "f1_score": f1,
        })
        
        mlflow.log_artifact(str(metrics_file_versioned))
        
        logger.info("Detailed evaluation completed")        
        return metrics, y_pred, y_pred_prob
    def plot_history(self, history):
        """Plot and save training history."""
        logger.info("Creating training history plots")
        
        plt.figure(figsize=(12, 5))
        
        plt.subplot(1, 2, 1)
        plt.plot(history.history['accuracy'])
        plt.plot(history.history['val_accuracy'])
        plt.title('Model Accuracy')
        plt.ylabel('Accuracy')
        plt.xlabel('Epoch')
        plt.legend(['Train', 'Validation'], loc='lower right')
        
        plt.subplot(1, 2, 2)
        plt.plot(history.history['loss'])
        plt.plot(history.history['val_loss'])
        plt.title('Model Loss')
        plt.ylabel('Loss')
        plt.xlabel('Epoch')
        plt.legend(['Train', 'Validation'], loc='upper right')
        
        plt.tight_layout()
        
        os.makedirs(self.eval_config.evaluation_dir, exist_ok=True)
        history_fig_path = os.path.join(self.eval_config.evaluation_dir, f"history_training_{self.datetime_suffix}.png")
        plt.savefig(history_fig_path)
        plt.close()
        logger.info(f"Training history plot saved at: {history_fig_path}")
        mlflow.log_artifact(history_fig_path)
        return history_fig_path
    def plot_confusion_matrix(self, y_test, y_pred):
        """Plot and save confusion matrix."""
        logger.info("Creating confusion matrix plot")
        
        cm = confusion_matrix(y_test, y_pred)
        plt.figure(figsize=(8, 6))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', cbar=False)
        plt.title('Confusion Matrix')
        plt.ylabel('True Label')
        plt.xlabel('Predicted Label')
        
        os.makedirs(self.eval_config.evaluation_dir, exist_ok=True)
        cm_path = os.path.join(self.eval_config.evaluation_dir, f"confusion_matrix_{self.datetime_suffix}.png")
        plt.savefig(cm_path)
        plt.close()
        logger.info(f"Confusion matrix saved to: {cm_path}")
        mlflow.log_artifact(cm_path)

        return cm_path
    def plot_precision_recall_curve(self, y_test, y_pred_prob):
        """Plot and save Precision-Recall curve."""
        logger.info("Creating Precision-Recall curve plot")

        precision_vals, recall_vals, _ = precision_recall_curve(y_test, y_pred_prob)
        avg_precision = average_precision_score(y_test, y_pred_prob)

        plt.figure(figsize=(8, 6))
        plt.plot(recall_vals, precision_vals, color='purple', lw=2,
                label=f'Precision-Recall curve (AP = {avg_precision:.3f})')
        plt.xlabel('Recall')
        plt.ylabel('Precision')
        plt.title('Precision-Recall Curve')
        plt.legend(loc='lower left')

        os.makedirs(self.eval_config.evaluation_dir, exist_ok=True)
        pr_path = os.path.join(self.eval_config.evaluation_dir, f"precision_recall_curve_{self.datetime_suffix}.png")
        plt.savefig(pr_path)
        plt.close()
        logger.info(f"Precision-Recall curve saved to: {pr_path}")
        mlflow.log_artifact(pr_path)
        return pr_path
    
    def plot_roc_curve(self, y_test, y_pred_prob):
        """Plot and save ROC curve."""
        logger.info("Creating ROC curve plot")
        
        fpr, tpr, thresholds = roc_curve(y_test, y_pred_prob)
        roc_auc = auc(fpr, tpr)
        
        plt.figure(figsize=(8, 6))
        plt.plot(fpr, tpr, color='blue', lw=2, label=f'ROC curve (AUC = {roc_auc:.3f})')
        plt.plot([0, 1], [0, 1], color='gray', linestyle='--')
        plt.xlim([0.0, 1.0])
        plt.ylim([0.0, 1.05])
        plt.xlabel('False Positive Rate')
        plt.ylabel('True Positive Rate')
        plt.title('Receiver Operating Characteristic (ROC) Curve')
        plt.legend(loc="lower right")
        
        os.makedirs(self.eval_config.evaluation_dir, exist_ok=True)
        roc_path = os.path.join(self.eval_config.evaluation_dir, f"roc_curve_{self.datetime_suffix}.png")
        plt.savefig(roc_path)
        plt.close()
        logger.info(f"ROC curve saved to: {roc_path}")
        mlflow.log_artifact(roc_path)

        return roc_path
    
    def train_and_evaluate(self, base_model, train_data, test_data,tokenizer):
        """Main method to train and evaluate the model using temporary directories."""
        logger.info("Initiating model training and evaluation with temporary directory management")

        X_train, X_test, y_train, y_test = self.prepare_data_for_training(train_data, test_data,tokenizer)
        try:
            try:
                logger.info(f"Loaded y_train shape: {y_train.shape}")
                logger.info(f"Loaded y_test shape: {y_test.shape}")
                
                # Handle NaN values in target variables
                logger.info(f"NaN count in y_train: {y_train.isna().sum()}")
                logger.info(f"NaN count in y_test: {y_test.isna().sum()}")
                
                if y_train.isna().sum() > 0:
                    logger.warning(f"Found {y_train.isna().sum()} NaN values in y_train, filling with 0")
                    y_train = y_train.fillna(0)
                    
                if y_test.isna().sum() > 0:
                    logger.warning(f"Found {y_test.isna().sum()} NaN values in y_test, filling with 0")
                    y_test = y_test.fillna(0)
                    
            except FileNotFoundError as e:
                logger.error(f"Target files not found: {e}")
                raise e

            logger.info(f"Final X_train_scaled shape: {X_train.shape}")
            logger.info(f"Final y_train shape: {y_train.shape}")
            logger.info(f"Final X_test_scaled shape: {X_test.shape}")
            logger.info(f"Final y_test shape: {y_test.shape}")

            model, history = self.train(X_train, y_train, base_model)
            self.plot_history(history)
            metrics, y_pred, y_pred_prob = self.perform_detailed_evaluation(base_model, X_test, y_test)
            self.plot_confusion_matrix(y_test, y_pred)
            self.plot_precision_recall_curve(y_test, y_pred_prob)
            self.plot_roc_curve(y_test, y_pred_prob)
            self.log_model_to_mlflow(model, str(self.model_name))
        except Exception as e:
            logger.error(f"An error occurred during model training and evaluation: {e}")
            raise e
        else:
            logger.info("Model training and evaluation completed successfully")
            return model, metrics
            
                