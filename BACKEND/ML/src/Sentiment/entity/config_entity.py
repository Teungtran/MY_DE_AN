from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DataIngestionConfig:
    root_dir: Path
    data_version_dir: Path
    local_data_file: Path
    test_size: float
    random_state: int



@dataclass(frozen=True)
class PrepareBaseModelConfig:
    model_version_dir: Path
    data_version_dir: Path
    maxlen: int
    num_words: int
    embedding_dim: int
    batch_size: int
    epochs: int
    filters: int
    kernel_size: int
    dropout_rate: float
    
@dataclass(frozen=True)
class TrainingConfig:
    model_version_dir: Path
    data_version_dir: Path
    maxlen: int
    batch_size: int
    epochs: int
    validation_split: float


@dataclass(frozen=True)
class EvaluationConfig:
    model_version_dir: Path
    data_version_dir: Path
    evaluation_dir: Path


@dataclass(frozen=True)
class CloudStoragePushConfig:
    root_dir: Path
    aws_key_id: str
    aws_secret_key: str
    bucket_name: str
    data_version_dir: Path
    evaluation_dir: Path
    region_name: str


@dataclass(frozen=True)
class MLFlowConfig:
    dagshub_username: str
    dagshub_repo_name: str
    tracking_uri: str
    experiment_name: str
    prediction_experiment_name: str

@dataclass(frozen=True)
class ThresholdConfig:
    confidence_threshold: float
    data_drift_threshold: float

