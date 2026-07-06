# CipherVision: Adaptive Chaotic Image Encryption

CipherVision is an adaptive, texture-aware image encryption system that combines machine learning classification with multi-dimensional chaotic maps to provide region-specific encryption. By partitioning images into localized blocks, analyzing their textural complexity, and dynamically routing them to appropriate chaotic systems, it balances high security with computational efficiency.

The project is designed for securing sensitive image domains, particularly medical imaging (MRI, CT, ultrasound, retinal scans) and standard benchmark formats, with full mathematical reversibility (lossless decryption).

---

## Architecture & Methodology

CipherVision works in a 4-phase pipeline:

1. **Texture Feature Extraction (GLCM)**

   - The input image is divided into $16 \times 16$ non-overlapping blocks.
   - For each block, Gray-Level Co-occurrence Matrix (GLCM) features are calculated across 4 directions ($0^{\circ}$, $45^{\circ}$, $90^{\circ}$, $135^{\circ}$) and 3 distances ($d = 1, 2, 3$).
   - To optimize speed, block pixel intensities are quantized to 32 grey levels (achieving a $64\times$ speedup over a standard 256-level GLCM while preserving texture discrimination).
   - Eight rotationally invariant features are calculated per block: Contrast, Correlation, Energy, Homogeneity, Dissimilarity, Angular Second Moment (ASM), Variance, and Local Entropy.
2. **Random Forest Classification**

   - A Random Forest Classifier (250 estimators, maximum depth 25) categorizes each block into one of three texture tiers:
     - **Class 0 (Smooth):** Low contrast, high homogeneity.
     - **Class 1 (Medium):** Moderate complexity.
     - **Class 2 (Rough/Complex):** High contrast, high variance, high entropy (edges and fine details).
   - The classifier is trained on clusters discovered using unsupervised K-Means (ordered by variance for deterministic labeling).
3. **3-Tier Adaptive Chaotic Encryption**

   - Blocks are routed to a chaotic system matched to their texture complexity:
     - **Class 0 (Smooth):** 1D Chaotic Logistic Map (lightweight, rapid keystream generation).
     - **Class 1 (Medium):** 3D Chaotic Lorenz Attractor integrated using Runge-Kutta 4th order (RK4) for numerical stability.
     - **Class 2 (Rough):** 4D Hyperchaotic Chen System (highest mathematical complexity and security).
   - Each system is perturbed using initial values derived from a SHA-256 hash of the user password, block index, and cryptographic feedback.
4. **Multi-Stage Security Layers**

   - **Inter-Block Feedback:** Each block's encryption is chained to the sum of the previous block's ciphertext (CBC-like behavior).
   - **Block-Level Permutation & Substitution:** Pixel locations are shuffled (confusion) and values are modified (diffusion) via forward/backward diffusion passes.
   - **Global Pixel Diffusion:** A final full-image bitwise XOR pass using a secondary chaotic keystream is applied to break remaining boundary correlations between blocks.

---

## Tech Stack

### Backend

- **Core Language:** Python 3.10+
- **Web Framework:** Flask (REST API backend)
- **Computer Vision & Image Processing:** OpenCV (`opencv-python`), Pillow, scikit-image (`skimage`)
- **Machine Learning:** scikit-learn (`sklearn`), joblib
- **Scientific Computing:** NumPy, SciPy
- **Data & Utilities:** pandas, python-dotenv, requests

### Frontend

- **Structure:** Semantic HTML5, Single Page Application (SPA) layout
- **Styling:** Vanilla CSS3 (glassmorphic dark UI, responsive layout, CSS variables)
- **Logic:** Vanilla ES6+ JavaScript (async/await APIs)
- **Charts & Visualization:** Chart.js (used for real-time histograms, adjacent pixel correlation scatter plots, and per-tier metrics comparisons)
- **Report Generation:** jsPDF & html2canvas (generates and downloads detailed security analysis PDF reports)

---

## Project Structure

```
├── app_flask.py            # Main Flask application and REST API endpoints
├── classifier.py           # Random Forest texture classification pipeline
├── texture_analysis.py     # GLCM block partitioning and feature extraction
├── encryption.py           # Chaotic maps (Logistic, Lorenz, Chen) encryption engine
├── metrics.py              # Cryptographic security metrics suite
├── train_model.py          # Script to download benchmarks, generate synthetic data, and train model
├── test_pipeline.py        # Benchmark runner for standard images and medical datasets
├── requirements.txt        # Backend dependencies list
├── static/                 # Frontend client files
│   ├── index.html          # Main SPA interface
│   ├── css/
│   │   └── style.css       # Custom stylesheets (glassmorphism/dark mode)
│   └── js/
│       └── app.js          # Client-side API integration, Chart.js logic, PDF generator
├── datasets/               # Directory created by train_model.py (contains training images)
└── .sessions/              # Directory created at runtime for server-side encryption sessions
```

---

## Getting Started

### 1. Install Dependencies

Set up a Python virtual environment and install the required libraries:

```bash
pip install -r requirements.txt
```

### 2. Train the Classifier

Before running the encryption engine, train the Random Forest model on the texture dataset:

```bash
python train_model.py
```

This script downloads standard academic images (e.g., Lena, Baboon from the USC-SIPI database), collects local benchmark files, generates synthetic texture patterns as a fallback, runs K-Means clustering, and saves the trained classifier (`rf_model.pkl`) and scaler (`scaler.pkl`).

### 3. Run the Web Server

Launch the Flask backend:

```bash
python app_flask.py
```

By default, the server runs on `http://127.0.0.1:5000`. Open this URL in your web browser.

### 4. Run the Verification Tests

To execute a headless benchmark across standard and medical images (MRI, skin cancer, ultrasound) and generate a CSV of result metrics:

```bash
python test_pipeline.py
```

---

## Verification & Cryptographic Quality Metrics

The system evaluates ciphertexts against standard cryptographic benchmarks defined in the security metrics suite (`metrics.py`):

- **Information Entropy:** Ideal value is $8.0$ for a completely random 8-bit image distribution. CipherVision typically achieves $\approx 7.61 - 7.62$ average entropy.
- **NPCR (Number of Pixels Change Rate):** Measures resistance to differential cryptanalysis. Ideal value is $\approx 99.609\%$. CipherVision achieves $>99.90\%$ NPCR, exceeding standard expectations.
- **UACI (Unified Average Changing Intensity):** Measures the average intensity difference. Ideal value is $\approx 33.464\%$. CipherVision outputs $\approx 33.0\% - 34.5\%$.
- **Adjacent Pixel Correlation:** Original images show strong correlation ($\approx 0.95 - 0.99$) appearing as diagonal lines in scatter plots. CipherVision's encrypted outputs yield correlation coefficients of $\approx 0.00$, visible as uniform, unstructured point clouds.
- **Chi-Square ($\chi^2$) Uniformity Test:** Evaluates if pixel intensities are uniformly distributed. Tests are verified against the critical value ($293.25$ for $df=255$ at $\alpha=0.05$).
- **Decryption Losslessness:** The pipeline checks pixel-by-pixel mathematical reversibility, ensuring that original and decrypted images are identical down to the bit level (verified via absolute sum of differences, yielding exactly $0$ difference).
- **Ablation & Sensitivity Analysis:** Supports comparing the adaptive routing method against uniform encryption modes (Uniform Logistic vs. Uniform Chen) to prove speed-to-security trade-offs, and validates key sensitivity by verifying that a 1-bit key change yields completely randomized decryption failure.
