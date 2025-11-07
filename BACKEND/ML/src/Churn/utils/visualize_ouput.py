import os
import time
import matplotlib.pyplot as plt
import pandas as pd

def visualize_customer_churn(df: pd.DataFrame, output_dir: str = "plots\churn"):
    os.makedirs(output_dir, exist_ok=True)
    plt.switch_backend('Agg')  # Non-GUI backend for server use

    try:
        # Ensure Churn_RATE is numeric to avoid categorical plotting warnings
        churn_counts = df['Churn_RATE'].astype(float).value_counts().sort_index()
        labels = ['Not Churned', 'Churned']
        # Ensure sizes are native Python integers to avoid warnings
        sizes = [int(churn_counts.get(0.0, 0)), int(churn_counts.get(1.0, 0))]
        colors = ['#2ecc71', '#e74c3c']  
        fig_pie = plt.figure(figsize=(8, 6))
        plt.pie(
            sizes,
            labels=labels,
            autopct='%1.1f%%',
            startangle=90,
            colors=colors,
            wedgeprops={'edgecolor': 'black'}
        )
        plt.title('Customer Churn Distribution')

        timestamp = int(time.time())
        pie_plot_path = os.path.join(output_dir, f"Churn_RATE_piechart_{timestamp}.png")
        plt.savefig(pie_plot_path)
        plt.close(fig_pie)

        return pie_plot_path

    except Exception as e:
        print(f"Error generating visualization: {e}")
        return os.path.join(output_dir, "visualization_failed.png")
