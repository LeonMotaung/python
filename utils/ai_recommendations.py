def generate_recommendations(df):
    # Example heuristic-based recommendations
    recommendations = []
    numeric_df = df.select_dtypes(include=['number'])
    if not numeric_df.empty:
        high_corr = (numeric_df.corr().abs() > 0.5).stack()
        high_corr_pairs = high_corr[high_corr].index.tolist()
        if high_corr_pairs:
            recommendations.append("Strong correlations detected between variables. Consider further investigation.")
    return recommendations