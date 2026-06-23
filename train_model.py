import numpy as np
import cv2
import os
import random
import requests
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score
from texture_analysis import TextureAnalyzer
from classifier import TextureClassifier

# Maximum image dimension for training (resized to keep GLCM fast)
MAX_TRAIN_DIM = 256

# --- DATASET DEFINITIONS ---

# 1. USC-SIPI Miscellaneous Volume (The Academic Standard)
SIPI_IMAGES = {
    "lena.png": "https://sipi.usc.edu/database/preview/misc/4.1.04.png",
    "baboon.png": "https://sipi.usc.edu/database/preview/misc/4.2.03.png",
    "peppers.png": "https://sipi.usc.edu/database/preview/misc/4.2.04.png",
    "airplane.png": "https://sipi.usc.edu/database/preview/misc/4.2.05.png",
    "sailboat.png": "https://sipi.usc.edu/database/preview/misc/4.2.06.png",
    "house.png": "https://sipi.usc.edu/database/preview/misc/4.1.05.png"
}

# 2. Fallback: Generate synthetic test images with known texture properties
def generate_synthetic_images(save_dir, count=10):
    """
    Generate synthetic images with varying textures for training when
    online datasets are unavailable. Creates gradient, noise, checkerboard,
    and natural-pattern images.
    """
    os.makedirs(save_dir, exist_ok=True)
    paths = []
    
    patterns = [
        ("smooth_gradient", lambda s: np.tile(np.linspace(0, 255, s, dtype=np.uint8), (s, 1))),
        ("vertical_gradient", lambda s: np.tile(np.linspace(0, 255, s, dtype=np.uint8), (s, 1)).T),
        ("checkerboard_8", lambda s: np.kron([[0, 255]*4, [255, 0]*4]*4, np.ones((s//8, s//8))).astype(np.uint8)[:s, :s]),
        ("checkerboard_16", lambda s: np.kron([[0, 255]*8, [255, 0]*8]*8, np.ones((s//16, s//16))).astype(np.uint8)[:s, :s]),
        ("random_noise", lambda s: np.random.randint(0, 256, (s, s), dtype=np.uint8)),
        ("gaussian_noise", lambda s: np.clip(128 + np.random.randn(s, s) * 60, 0, 255).astype(np.uint8)),
        ("circles", lambda s: _make_circles(s)),
        ("stripes_h", lambda s: np.tile(np.array([0, 0, 255, 255]*64, dtype=np.uint8)[:s], (s, 1))),
        ("stripes_v", lambda s: np.tile(np.array([0, 0, 255, 255]*64, dtype=np.uint8)[:s], (s, 1)).T),
        ("mixed_texture", lambda s: _make_mixed(s)),
    ]
    
    for name, gen_func in patterns[:count]:
        path = os.path.join(save_dir, f"{name}.png")
        if not os.path.exists(path):
            img = gen_func(256)
            if len(img.shape) == 2:
                img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
            cv2.imwrite(path, img)
            print(f"  [+] Generated: {name}.png")
        else:
            print(f"  [~] Already exists: {name}.png")
        paths.append(path)
    
    return paths

def _make_circles(size):
    img = np.zeros((size, size), dtype=np.uint8)
    center = size // 2
    for r in range(10, center, 20):
        cv2.circle(img, (center, center), r, 255, 2)
    return img

def _make_mixed(size):
    img = np.zeros((size, size), dtype=np.uint8)
    # Top-left: smooth gradient
    img[:size//2, :size//2] = np.tile(np.linspace(0, 255, size//2, dtype=np.uint8), (size//2, 1))
    # Top-right: noise
    img[:size//2, size//2:] = np.random.randint(0, 256, (size//2, size//2), dtype=np.uint8)
    # Bottom-left: checkerboard
    checker = np.kron([[0, 255]*4, [255, 0]*4]*4, np.ones((size//16, size//16))).astype(np.uint8)
    img[size//2:, :size//2] = checker[:size//2, :size//2]
    # Bottom-right: stripes
    img[size//2:, size//2:] = np.tile(np.array([0, 255]*128, dtype=np.uint8)[:size//2], (size//2, 1))
    return img

def download_dataset(category, url_dict):
    """Downloads images into their respective category folders."""
    data_dir = os.path.join("datasets", category)
    os.makedirs(data_dir, exist_ok=True)
    
    paths = []
    print(f"\n--- Downloading {category.upper()} Dataset ---")
    for filename, url in url_dict.items():
        path = os.path.join(data_dir, filename)
        if not os.path.exists(path):
            try:
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
                response = requests.get(url, headers=headers, timeout=15)
                if response.status_code == 200 and len(response.content) > 1000:
                    with open(path, 'wb') as f:
                        f.write(response.content)
                    print(f"  [+] Downloaded: {filename}")
                else:
                    print(f"  [-] Failed {filename} (HTTP {response.status_code})")
            except Exception as e:
                print(f"  [-] Error downloading {filename}: {e}")
        else:
            print(f"  [~] Already exists: {filename}")
            
        if os.path.exists(path):
            paths.append(path)
            
    return paths

def get_local_images(data_dir):
    """Collect all valid images from a local directory."""
    paths = []
    if os.path.exists(data_dir):
        for f in sorted(os.listdir(data_dir)):
            if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.tiff')):
                paths.append(os.path.join(data_dir, f))
    return paths

def resize_for_training(image_path, max_dim=MAX_TRAIN_DIM):
    """Load and resize image to max_dim for faster GLCM extraction."""
    img = cv2.imread(image_path)
    if img is None:
        return None
    h, w = img.shape[:2]
    if max(h, w) > max_dim:
        scale = max_dim / max(h, w)
        img = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
    return img

def build_universal_model():
    print("=" * 60)
    print("  UNIVERSAL MODEL TRAINING PIPELINE")
    print("  3-Tier Adaptive: Smooth | Medium | Rough")
    print("=" * 60)
    
    # 1. Download USC-SIPI standard benchmark images
    sipi_paths = download_dataset("USC-SIPI", SIPI_IMAGES)
    
    # 2. Collect benchmark HD images
    bench_paths = get_local_images("datasets/benchmark_hd")
    print(f"\nFound {len(bench_paths)} benchmark HD images.")
    
    # 3. Check for local medical images
    med_paths = get_local_images("datasets/medical_hd")
    print(f"Found {len(med_paths)} medical images.")
    
    # 4. Generate synthetic images as reliable fallback
    print("\n--- Generating Synthetic Texture Dataset ---")
    synth_paths = generate_synthetic_images("datasets/synthetic")
    
    # Combine all sources with balanced sampling
    random.seed(42)
    random.shuffle(med_paths)
    
    # Take a balanced sample: 3 SIPI, 3 Benchmark, 5 Medical, 5 Synthetic = 16 images
    selected_sipi = sipi_paths[:3]
    selected_bench = bench_paths[:3]
    selected_med = med_paths[:5]
    selected_synth = synth_paths[:5]
    all_image_paths = selected_sipi + selected_bench + selected_med + selected_synth
    
    if not all_image_paths:
        print("ERROR: No images available to train. Exiting.")
        return
    
    print(f"\n{'=' * 60}")
    print(f"  Selected Training Images: {len(all_image_paths)}")
    print(f"    USC-SIPI:    {len(selected_sipi)}")
    print(f"    Benchmark:   {len(selected_bench)}")
    print(f"    Medical HD:  {len(selected_med)}")
    print(f"    Synthetic:   {len(selected_synth)}")
    print(f"{'=' * 60}")
    
    # Extract features with progress feedback
    analyzer = TextureAnalyzer()
    all_features = []
    for idx, path in enumerate(all_image_paths):
        basename = os.path.basename(path)
        print(f"  [{idx+1}/{len(all_image_paths)}] Processing: {basename}...", end=" ", flush=True)
        try:
            img = resize_for_training(path)
            if img is None:
                print("SKIP (unreadable)")
                continue
            features, _, _ = analyzer.analyze(image_matrix=img)
            all_features.extend(features)
            print(f"OK ({len(features)} blocks)")
        except Exception as e:
            print(f"ERROR: {e}")
    
    if len(all_features) < 10:
        print("ERROR: Not enough texture blocks extracted. Exiting.")
        return
    
    print(f"\nTotal texture blocks extracted: {len(all_features)}")
    
    # Train the classifier
    classifier = TextureClassifier()
    X = classifier.prepare_data(all_features)
    
    print("Scaling features...")
    from sklearn.preprocessing import StandardScaler
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    print(f"Running K-Means (k=3) to discover texture tiers...")
    from sklearn.cluster import KMeans
    from classifier import FEATURE_KEYS
    kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
    labels = kmeans.fit_predict(X_scaled)
    
    # Sort clusters by variance for deterministic labeling
    cluster_centers = kmeans.cluster_centers_
    variance_idx = FEATURE_KEYS.index('variance')
    cluster_order = np.argsort(cluster_centers[:, variance_idx])
    label_map = {old: new for new, old in enumerate(cluster_order)}
    labels = np.array([label_map[l] for l in labels])
    
    counts = [np.sum(labels == i) for i in range(3)]
    print(f"Discovered: {counts[0]} Smooth, {counts[1]} Medium, {counts[2]} Rough blocks")
    
    print("Training Random Forest Classifier (n_estimators=250)...")
    from sklearn.ensemble import RandomForestClassifier
    model = RandomForestClassifier(n_estimators=250, max_depth=25, random_state=42, n_jobs=-1)
    
    if len(X_scaled) >= 50:
        from sklearn.model_selection import cross_val_score
        cv_scores = cross_val_score(model, X_scaled, labels, cv=5, scoring='accuracy')
        print(f"5-Fold Cross-Validation Accuracy: {cv_scores.mean()*100:.2f}% (± {cv_scores.std()*100:.2f}%)")
    
    model.fit(X_scaled, labels)
    
    importances = model.feature_importances_
    print("\nFeature Importances:")
    for name, imp in sorted(zip(FEATURE_KEYS, importances), key=lambda x: -x[1]):
        print(f"  {name:>15s}: {imp:.4f}")
    
    joblib.dump(model, 'rf_model.pkl')
    joblib.dump(scaler, 'scaler.pkl')
    
    print(f"\n{'=' * 60}")
    print("  SUCCESS: Universal 3-Tier Model Trained!")
    print("  Saved: rf_model.pkl, scaler.pkl")
    print(f"{'=' * 60}")

if __name__ == "__main__":
    build_universal_model()
