import matplotlib
matplotlib.use('Agg')  # Use Agg backend
import matplotlib.pyplot as plt
import os
import seaborn as sns

def generate_histogram(df, filename):
    # Set the style
    sns.set_style("whitegrid")
    
    # Create a figure with subplots for each numerical column
    num_cols = df.select_dtypes(include=['int64', 'float64']).columns
    n_cols = len(num_cols)
    
    if n_cols == 0:
        return None
    
    # Calculate rows and columns for subplot grid
    n_rows = (n_cols + 2) // 3  # 3 plots per row
    n_cols_plot = min(3, n_cols)
    
    fig, axes = plt.subplots(n_rows, n_cols_plot, figsize=(15, 5*n_rows))
    fig.suptitle('Data Distribution', fontsize=16, y=1.02)
    
    # Flatten axes array if there's more than one row
    if n_rows > 1:
        axes = axes.flatten()
    elif n_rows == 1 and n_cols_plot > 1:
        axes = axes.flatten()
    else:
        axes = [axes]
    
    # Plot histograms
    for idx, col in enumerate(num_cols):
        sns.histplot(data=df, x=col, ax=axes[idx], kde=True)
        axes[idx].set_title(f'Distribution of {col}')
        axes[idx].tick_params(axis='x', rotation=45)
    
    # Remove empty subplots if any
    for idx in range(len(num_cols), len(axes)):
        fig.delaxes(axes[idx])
    
    plt.tight_layout()
    
    # Save the plot
    img_path = os.path.join("static", "images", f"{filename}.png")
    plt.savefig(img_path, bbox_inches='tight', dpi=300)
    plt.close()
    
    return img_path
