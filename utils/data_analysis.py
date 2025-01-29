import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

def analyze_data(df):
    analysis = {
        'summary': df.describe().to_dict(),
        'correlations': df.corr().to_dict()
    }
    
    # Generate plots
    os.makedirs('static/plots', exist_ok=True)
    for column in df.select_dtypes(include=['number']).columns:
        plt.figure()
        sns.histplot(df[column])
        plt.savefig(f'static/plots/{column}_hist.png')
        plt.close()
    
    return analysis