import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score
import joblib
import os
from texture_analysis import TextureAnalyzer

# Feature columns used for classification (must match TextureAnalyzer output)
FEATURE_KEYS = ['contrast', 'correlation', 'energy', 'homogeneity',
                'dissimilarity', 'asm', 'variance', 'local_entropy']

class TextureClassifier:
    """
    3-Class Texture Classifier using Random Forest.
    
    Classes:
      0 = Smooth  (low contrast, high homogeneity)
      1 = Medium  (moderate texture complexity)
      2 = Rough   (high contrast, high variance, high entropy)
    """
    def __init__(self, model_path='rf_model.pkl', scaler_path='scaler.pkl'):
        self.model_path = model_path
        self.scaler_path = scaler_path
        self.model = None
        self.scaler = None
        self.n_clusters = 3  # 3-tier adaptive
        
        # If models exist, load them
        if os.path.exists(self.model_path) and os.path.exists(self.scaler_path):
            self.model = joblib.load(self.model_path)
            self.scaler = joblib.load(self.scaler_path)

    def prepare_data(self, features_list):
        """Extracts numerical features from the dictionary list."""
        X = []
        for f in features_list:
            row = [f[key] for key in FEATURE_KEYS]
            X.append(row)
        return np.array(X)

    def train_auto(self, image_path=None, image_paths=None):
        """
        Auto-trains the Random Forest on K-Means discovered labels.
        
        Uses 3 clusters: Smooth (0), Medium (1), Rough (2).
        Clusters are ordered by variance so label assignment is deterministic.
        Includes 5-fold cross-validation for proper evaluation.
        """
        analyzer = TextureAnalyzer()
        all_features = []
        
        if image_paths:
            for path in image_paths:
                try:
                    features, _, _ = analyzer.analyze(path)
                    all_features.extend(features)
                except Exception as e:
                    print(f"  Error processing {path}: {e}")
        elif image_path:
            features, _, _ = analyzer.analyze(image_path)
            all_features.extend(features)
        else:
            raise ValueError("Provide image_path or image_paths")
        
        if len(all_features) < 10:
            raise ValueError("Not enough blocks for training. Need at least 10 blocks.")
        
        X = self.prepare_data(all_features)
        
        print(f"Total blocks for training: {len(X)}")
        print("Scaling features...")
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)
        
        print(f"Running K-Means (k={self.n_clusters}) to discover texture tiers...")
        kmeans = KMeans(n_clusters=self.n_clusters, random_state=42, n_init=10)
        labels = kmeans.fit_predict(X_scaled)
        
        # Sort clusters by variance (index 6 in FEATURE_KEYS) to ensure deterministic labeling:
        # Lowest variance = Smooth (0), Highest variance = Rough (2)
        cluster_centers = kmeans.cluster_centers_
        variance_idx = FEATURE_KEYS.index('variance')
        cluster_order = np.argsort(cluster_centers[:, variance_idx])
        
        label_map = {old: new for new, old in enumerate(cluster_order)}
        labels = np.array([label_map[l] for l in labels])
        
        counts = [np.sum(labels == i) for i in range(self.n_clusters)]
        print(f"Discovered: {counts[0]} Smooth, {counts[1]} Medium, {counts[2]} Rough blocks")
        
        print("Training Random Forest Classifier (n_estimators=250)...")
        self.model = RandomForestClassifier(
            n_estimators=250, max_depth=25, random_state=42, n_jobs=-1
        )
        
        # 5-Fold Cross-Validation for proper evaluation
        if len(X_scaled) >= 50:
            cv_scores = cross_val_score(self.model, X_scaled, labels, cv=5, scoring='accuracy')
            print(f"5-Fold Cross-Validation Accuracy: {cv_scores.mean()*100:.2f}% (± {cv_scores.std()*100:.2f}%)")
        
        # Final fit on all data
        self.model.fit(X_scaled, labels)
        
        # Feature importances
        importances = self.model.feature_importances_
        print("\nFeature Importances:")
        for name, imp in sorted(zip(FEATURE_KEYS, importances), key=lambda x: -x[1]):
            print(f"  {name:>15s}: {imp:.4f}")
        
        # Save the models
        joblib.dump(self.model, self.model_path)
        joblib.dump(self.scaler, self.scaler_path)
        print(f"\nModel saved to {self.model_path} and {self.scaler_path}")

    def predict(self, features_list):
        """Predicts texture tier: Smooth (0), Medium (1), or Rough (2)."""
        if self.model is None or self.scaler is None:
            raise Exception("Model is not trained. Call train_auto() first.")
            
        X = self.prepare_data(features_list)
        X_scaled = self.scaler.transform(X)
        predictions = self.model.predict(X_scaled)
        
        return predictions

    def visualize_predictions(self, image_path, output_path="visual_result.png"):
        import cv2
        analyzer = TextureAnalyzer()
        features_list, original, _ = analyzer.analyze(image_path)
        
        predictions = self.predict(features_list)
        vis_img = original.copy()
        
        # 3-tier color coding: Smooth=Blue, Medium=Green, Rough=Red
        colors = {0: (255, 0, 0), 1: (0, 255, 0), 2: (0, 0, 255)}
        
        for i, features in enumerate(features_list):
            y_start, y_end, x_start, x_end = features['coords']
            pred = predictions[i]
            color = colors.get(pred, (255, 255, 255))
            cv2.rectangle(vis_img, (x_start, y_start), (x_end, y_end), color, 1)
            
        cv2.imwrite(output_path, vis_img)
        print(f"Visualization saved to {output_path}")

if __name__ == "__main__":
    print("Texture Classifier Module Loaded.")
    print("Training model on test.jpg...")
    classifier = TextureClassifier()
    try:
        classifier.train_auto('test.jpg')
        classifier.visualize_predictions('test.jpg')
    except Exception as e:
        print(f"Error: {e}")
