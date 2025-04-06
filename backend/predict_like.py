import pandas as pd
from datetime import datetime
import numpy as np

# Make a prediction for a new post (using only hour and day_of_week)
def predict_likes(model, feature_names, hour, day_of_week):
    if model is None:
        return "Model not trained. Please check the data file."
    # Create a DataFrame with the input features
    input_data = pd.DataFrame({
        'hour': [hour],
        'is_peak_hour': [1 if 12 <= hour <= 18 else 0],
        'is_weekday': [1 if datetime.strptime(day_of_week, '%A').weekday() < 5 else 0]
    })

    # Add one-hot encoded day_of_week columns (excluding the first day as reference)
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    for day in days[1:]:
        input_data[f'day_of_week_{day}'] = [1 if day == day_of_week else 0]

    # Ensure all columns match the training set
    for col in feature_names:
        if col not in input_data.columns:
            input_data[col] = 0

    # Reorder columns to match training set
    input_data = input_data[feature_names]

    # Predict
    prediction = model.predict(input_data)[0]
    return max(0, int(prediction))  # Ensure non-negative integer


# Extract features from the dataset (for stats calculation)
def extract_features(data):
    print("extracting fetaures..................")
    if not data:
        return pd.DataFrame()
    features = []
    for i, post in enumerate(data):
        dt = datetime.fromisoformat(post['timestamp'].replace('Z', '+00:00'))

        # Basic features
        hour = dt.hour
        day_of_week = dt.strftime('%A')
        is_peak_hour = 1 if 12 <= hour <= 18 else 0
        is_weekday = 1 if dt.weekday() < 5 else 0

        # Calculate days since the first post (for stats, not prediction)
        first_post_dt = datetime.fromisoformat(data[0]['timestamp'].replace('Z', '+00:00'))
        days_since_first_post = (first_post_dt - dt).days

        # Calculate average likes of the last 5 posts (for stats, not prediction)
        avg_likes_last_5 = 0
        if i >= 5:
            prev_likes = [data[j]['likes_count'] for j in range(i - 5, i)]
            avg_likes_last_5 = np.mean(prev_likes)

        # Store features and target
        features.append({
            'hour': hour,
            'day_of_week': day_of_week,
            'is_peak_hour': is_peak_hour,
            'is_weekday': is_weekday,
            'days_since_first_post': days_since_first_post,
            'avg_likes_last_5': avg_likes_last_5,
            'likes_count': post['likes_count'],
            'post_id': post['id'],
            'timestamp': post['timestamp']
        })

    # Create a DataFrame from the features
    df = pd.DataFrame(features)
    
    # Calculate stats as an array of objects
    stats = [
        {'name': 'Total Posts', 'value': len(df)},
        {'name': 'Average Likes', 'value': int(df['likes_count'].mean())},
        {'name': 'Average Comments', 'value': int(sum([post['comments_count'] for post in data]) / len(data))}
    ]

    # Best time to post (hour with highest average likes)
    best_time = df.groupby('hour')['likes_count'].mean().idxmax()

    # Best day to post (day with highest average likes)
    best_day = df.groupby('day_of_week')['likes_count'].mean().idxmax()

    # Top post (post with the most likes)
    top_post_idx = df['likes_count'].idxmax()
    top_post = {
        'id': df.loc[top_post_idx, 'post_id'],
        'likes': int(df.loc[top_post_idx, 'likes_count']),
        'timestamp': df.loc[top_post_idx, 'timestamp']
    }

    # Engagement trend (likes over time)
    engagement_trend = df.groupby('timestamp')['likes_count'].mean().reset_index().to_dict('records')
    print("extracted features.")
    return stats, best_time, best_day, top_post, engagement_trend

