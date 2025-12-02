import os
import time
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

def visualize_customer_churn(df: pd.DataFrame, output_dir: str = "plots/churn"):
    os.makedirs(output_dir, exist_ok=True)
    plt.switch_backend('Agg')  # Non-GUI backend for server use

    try:
        # Ensure Churn_RATE is numeric and handle NaN values
        df_clean = df.copy()
        df_clean['Churn_RATE'] = pd.to_numeric(df_clean['Churn_RATE'], errors='coerce')
        df_clean = df_clean.dropna(subset=['Churn_RATE'])
        
        if len(df_clean) == 0:
            raise ValueError("No valid Churn_RATE data after cleaning")
        
        # Categorize churn rates into risk levels (since Churn_RATE is a probability, not binary)
        df_clean['Risk_Level'] = pd.cut(
            df_clean['Churn_RATE'],
            bins=[0, 0.3, 0.7, 1.0],
            labels=['Low Risk', 'Medium Risk', 'High Risk'],
            include_lowest=True
        )
        
        # Count risk levels
        risk_counts = df_clean['Risk_Level'].value_counts()
        labels = risk_counts.index.tolist()
        # Ensure sizes are native Python integers and handle NaN
        sizes = [int(v) if not pd.isna(v) else 0 for v in risk_counts.values]
        colors = ['#2ecc71', '#F59E0B', '#e74c3c']  # Green, Orange, Red
        
        # Filter out zero sizes to avoid division by zero
        filtered_data = [(label, size, color) for label, size, color in zip(labels, sizes, colors) if size > 0]
        if not filtered_data:
            raise ValueError("No valid data points for visualization")
        
        labels, sizes, colors = zip(*filtered_data)
        labels = list(labels)
        sizes = list(sizes)
        colors = list(colors)
        
        fig_pie = plt.figure(figsize=(8, 6))
        plt.pie(
            sizes,
            labels=labels,
            autopct='%1.1f%%',
            startangle=90,
            colors=colors,
            wedgeprops={'edgecolor': 'black'}
        )
        plt.title('Customer Churn Risk Distribution')

        timestamp = int(time.time())
        pie_plot_path = os.path.join(output_dir, f"Churn_RATE_piechart_{timestamp}.png")
        plt.savefig(pie_plot_path)
        plt.close(fig_pie)

        return pie_plot_path

    except Exception as e:
        print(f"Error generating visualization: {e}")
        # Return a path but don't create the file - let the caller handle it
        return "visualization_failed.png"
