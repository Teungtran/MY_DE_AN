import os
import time
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

def rating_distribution(df: pd.DataFrame, output_dir: str = "plots/ratings") -> str:
    os.makedirs(output_dir, exist_ok=True)
    plt.switch_backend('Agg')  # Non-GUI backend for server use

    try:
        rating_counts = df['rating'].value_counts().sort_index()
        rating_colors = plt.cm.YlOrRd(np.linspace(0.3, 0.8, len(rating_counts)))

        fig, ax = plt.subplots(figsize=(8, 6))
        bars = ax.bar(
            rating_counts.index.astype(str),
            rating_counts.values,
            color=rating_colors,
            edgecolor='black'
        )

        for rect in bars:
            height = rect.get_height()
            ax.text(
                rect.get_x() + rect.get_width() / 2.,
                height,
                f'{int(height):,}',
                ha='center',
                va='bottom'
            )

        ax.set_title('Ratings Distribution')
        ax.set_xlabel('Ratings')
        ax.set_ylabel('Count')
        plt.tight_layout()

        filename = f"ratings_bar_{int(time.time())}.png"
        file_path = os.path.join(output_dir, filename)
        plt.savefig(file_path)
        plt.close(fig)

        return file_path

    except Exception as e:
        print(f"Error saving ratings distribution plot: {e}")
        return "visualization_failed.png"
