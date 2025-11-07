import os
import time
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

def rating_distribution(df: pd.DataFrame, output_dir: str = "plots/ratings") -> str:
    os.makedirs(output_dir, exist_ok=True)
    plt.switch_backend('Agg')  # Non-GUI backend for server use

    try:
        # Ensure rating is numeric to avoid categorical plotting warnings
        rating_counts = df['rating'].astype(float).value_counts().sort_index()
        rating_colors = plt.cm.YlOrRd(np.linspace(0.3, 0.8, len(rating_counts)))

        fig, ax = plt.subplots(figsize=(8, 6))
        # Convert index to numeric to avoid categorical plotting warning
        x_values = rating_counts.index.astype(float)
        # Ensure values are native Python integers to avoid warnings
        y_values = [int(v) for v in rating_counts.values]
        bars = ax.bar(
            x_values,
            y_values,
            color=rating_colors,
            edgecolor='black'
        )
        
        # Set x-axis labels as strings for display
        ax.set_xticks(x_values)
        ax.set_xticklabels([str(x) for x in x_values])

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
