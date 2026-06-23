"""
CipherVision — Flask Backend
Lightweight API server for the 3-Tier Adaptive Chaotic Encryption system.
Replaces Streamlit with a proper REST API + static SPA frontend.
"""

import os
import io
import sys
import base64
import time
import traceback
import numpy as np
import cv2
from flask import Flask, request, jsonify, send_from_directory, Response

from texture_analysis import TextureAnalyzer
from classifier import TextureClassifier
from encryption import AdaptiveEncryptor
from metrics import SecurityMetrics

app = Flask(__name__, static_folder='static', static_url_path='/static')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB upload limit

# ── Globals ──────────────────────────────────────────────────────────────────
analyzer = TextureAnalyzer()
classifier = TextureClassifier()

# In-memory session store (single-user; fine for local demo)
session_store = {}

# Max dimension for processing (resize larger images)
MAX_DIM = 512


def numpy_to_base64_jpeg(img, quality=85):
    """Encode numpy image to base64 JPEG data-URI (smaller than PNG)."""
    params = [cv2.IMWRITE_JPEG_QUALITY, quality]
    success, buffer = cv2.imencode('.jpg', img, params)
    if not success:
        raise ValueError("Failed to encode image")
    b64 = base64.b64encode(buffer).decode('utf-8')
    return f"data:image/jpeg;base64,{b64}"


def numpy_to_base64_png(img):
    """Encode numpy image to base64 PNG data-URI (lossless for download)."""
    success, buffer = cv2.imencode('.png', img)
    if not success:
        raise ValueError("Failed to encode image")
    b64 = base64.b64encode(buffer).decode('utf-8')
    return f"data:image/png;base64,{b64}"


def decode_upload(file_storage):
    """Decode a Flask FileStorage upload into a BGR numpy array."""
    file_bytes = np.frombuffer(file_storage.read(), np.uint8)
    img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Could not decode uploaded image")
    return img


def resize_if_needed(img, max_dim=MAX_DIM):
    """Resize image if either dimension exceeds max_dim."""
    h, w = img.shape[:2]
    if max(h, w) > max_dim:
        scale = max_dim / max(h, w)
        new_w, new_h = int(w * scale), int(h * scale)
        img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
    return img


# ── Routes ───────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')


@app.route('/api/encrypt', methods=['POST'])
def api_encrypt():
    """
    Accepts: multipart form with 'image' file and 'password' field.
    Returns: JSON with encrypted image, metrics, texture map, and timing.
    """
    try:
        print("[API] /api/encrypt called", flush=True)

        if 'image' not in request.files or 'password' not in request.form:
            return jsonify({'error': 'Missing image or password'}), 400

        password = request.form['password']
        if not password:
            return jsonify({'error': 'Password cannot be empty'}), 400

        img_bgr = decode_upload(request.files['image'])
        print(f"[API] Image decoded: {img_bgr.shape}", flush=True)

        # Resize for performance
        img_bgr = resize_if_needed(img_bgr)
        print(f"[API] After resize: {img_bgr.shape}", flush=True)

        # Phase 1: Texture Analysis
        print("[API] Phase 1: Texture analysis...", flush=True)
        features, orig, gray = analyzer.analyze(image_matrix=img_bgr)
        print(f"[API] Extracted {len(features)} blocks", flush=True)

        # Phase 2: Classification
        if classifier.model is None:
            return jsonify({'error': 'Model not trained. Run `python train_model.py` first.'}), 500

        print("[API] Phase 2: Classification...", flush=True)
        predictions = classifier.predict(features)
        print(f"[API] Predictions done. Classes: {np.bincount(predictions, minlength=3).tolist()}", flush=True)

        # Build texture visualization map
        vis_img = orig.copy()
        colors = {0: (255, 100, 50), 1: (50, 220, 100), 2: (50, 100, 255)}
        for i, feat in enumerate(features):
            y_s, y_e, x_s, x_e = feat['coords']
            cv2.rectangle(vis_img, (x_s, y_s), (x_e, y_e),
                          colors.get(int(predictions[i]), (200, 200, 200)), 1)

        # Phase 3: Encryption
        print("[API] Phase 3: Encryption...", flush=True)
        encryptor = AdaptiveEncryptor(password)
        t_start = time.perf_counter()
        encrypted_img = encryptor.encrypt_image(orig, features, predictions)
        enc_time = time.perf_counter() - t_start
        print(f"[API] Encryption done in {enc_time:.3f}s", flush=True)

        # Phase 4: Metrics (NPCR/UACI need 1-pixel-modified encryption)
        print("[API] Phase 4: Metrics...", flush=True)
        mod_orig = orig.copy()
        mod_orig[0, 0, 0] = (int(orig[0, 0, 0]) + 1) % 256
        enc_mod = encryptor.encrypt_image(mod_orig, features, predictions)
        metrics = SecurityMetrics.full_analysis(orig, encrypted_img, enc_mod)
        print("[API] Metrics computed", flush=True)

        # Block counts
        counts = {0: 0, 1: 0, 2: 0}
        for p in predictions:
            counts[int(p)] = counts.get(int(p), 0) + 1

        # Histogram data
        hist_orig, _ = SecurityMetrics.histogram_data(orig)
        hist_enc, _ = SecurityMetrics.histogram_data(encrypted_img)

        # Scatter data (reduced to 1000 points for payload size)
        scatter = {}
        for direction in ['horizontal', 'vertical', 'diagonal']:
            p1_o, p2_o = SecurityMetrics.get_scatter_data(orig, direction, 1000)
            p1_e, p2_e = SecurityMetrics.get_scatter_data(encrypted_img, direction, 1000)
            scatter[direction] = {
                'orig_x': [round(v, 1) for v in p1_o.tolist()],
                'orig_y': [round(v, 1) for v in p2_o.tolist()],
                'enc_x': [round(v, 1) for v in p1_e.tolist()],
                'enc_y': [round(v, 1) for v in p2_e.tolist()],
            }

        # Store in session for decryption
        session_store['original_img'] = orig
        session_store['encrypted_img'] = encrypted_img
        session_store['features_list'] = features
        session_store['predictions'] = predictions

        # Build response — use JPEG for display images (much smaller), PNG for download
        print("[API] Encoding response images...", flush=True)
        orig_rgb = cv2.cvtColor(orig, cv2.COLOR_BGR2RGB)
        enc_rgb = cv2.cvtColor(encrypted_img, cv2.COLOR_BGR2RGB)
        vis_rgb = cv2.cvtColor(vis_img, cv2.COLOR_BGR2RGB)

        response = {
            'original_b64': numpy_to_base64_jpeg(orig_rgb),
            'encrypted_b64': numpy_to_base64_jpeg(enc_rgb),
            'texture_map_b64': numpy_to_base64_jpeg(vis_rgb),
            'enc_time': round(enc_time, 4),
            'image_size': f"{orig.shape[1]}x{orig.shape[0]}",
            'total_blocks': len(features),
            'smooth_blocks': counts[0],
            'medium_blocks': counts[1],
            'rough_blocks': counts[2],
            'metrics': {
                'entropy_original': round(float(metrics['entropy_original']), 4),
                'entropy_encrypted': round(float(metrics['entropy_encrypted']), 4),
                'npcr': round(float(metrics.get('npcr', 0)), 4),
                'uaci': round(float(metrics.get('uaci', 0)), 4),
                'psnr': round(float(metrics['psnr']), 2),
                'ssim': round(float(metrics['ssim']), 6),
                'chi_square': round(float(metrics['chi_square']), 1),
                'chi_square_uniform': bool(metrics['chi_square_uniform']),
                'corr_orig_horizontal': round(float(metrics['corr_orig_horizontal']), 6),
                'corr_orig_vertical': round(float(metrics['corr_orig_vertical']), 6),
                'corr_orig_diagonal': round(float(metrics['corr_orig_diagonal']), 6),
                'corr_enc_horizontal': round(float(metrics['corr_enc_horizontal']), 6),
                'corr_enc_vertical': round(float(metrics['corr_enc_vertical']), 6),
                'corr_enc_diagonal': round(float(metrics['corr_enc_diagonal']), 6),
            },
            'histogram': {
                'original': hist_orig.tolist(),
                'encrypted': hist_enc.tolist(),
            },
            'scatter': scatter,
        }

        # Provide downloadable encrypted PNG as separate base64 (no data: prefix)
        _, enc_buffer = cv2.imencode('.png', encrypted_img)
        response['download_b64'] = base64.b64encode(enc_buffer).decode('utf-8')

        print(f"[API] Response ready. Sending...", flush=True)
        return jsonify(response)

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/decrypt', methods=['POST'])
def api_decrypt():
    """
    Accepts: JSON with 'password' field.
    Returns: JSON with decrypted image and lossless verification.
    """
    try:
        data = request.get_json()
        if data is None:
            return jsonify({'error': 'Invalid JSON body'}), 400

        password = data.get('password', '')
        if not password:
            return jsonify({'error': 'Password cannot be empty'}), 400

        if 'encrypted_img' not in session_store:
            return jsonify({'error': 'No encrypted image in session. Encrypt first.'}), 400

        encryptor = AdaptiveEncryptor(password)
        decrypted_img = encryptor.decrypt_image(
            session_store['encrypted_img'],
            session_store['features_list'],
            session_store['predictions']
        )

        # Lossless check
        diff = int(np.sum(np.abs(
            session_store['original_img'].astype(np.int16) - decrypted_img.astype(np.int16)
        )))
        is_lossless = diff == 0

        dec_rgb = cv2.cvtColor(decrypted_img, cv2.COLOR_BGR2RGB)
        return jsonify({
            'decrypted_b64': numpy_to_base64_jpeg(dec_rgb),
            'is_lossless': is_lossless,
            'pixel_diff': diff,
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/sensitivity', methods=['POST'])
def api_sensitivity():
    """
    Key sensitivity test: encrypts with base password and base+1 char,
    then decrypts with wrong key.
    """
    try:
        data = request.get_json()
        if data is None:
            return jsonify({'error': 'Invalid JSON body'}), 400

        password = data.get('password', 'MySecretKey123')

        if 'original_img' not in session_store:
            return jsonify({'error': 'No image in session. Encrypt first.'}), 400

        orig = session_store['original_img']
        feats = session_store['features_list']
        preds = session_store['predictions']

        # Encrypt with base password
        enc1 = AdaptiveEncryptor(password)
        img1 = enc1.encrypt_image(orig, feats, preds)

        # Encrypt with 1-char-modified password
        modified_pass = password[:-1] + chr(ord(password[-1]) + 1)
        enc2 = AdaptiveEncryptor(modified_pass)
        img2 = enc2.encrypt_image(orig, feats, preds)

        # Decrypt with wrong key
        dec_wrong = enc2.decrypt_image(img1, feats, preds)

        # Pixel difference percentage
        diff_pct = float((np.sum(img1 != img2) / img1.size) * 100)

        return jsonify({
            'password_a': password,
            'password_b': modified_pass,
            'enc_a_b64': numpy_to_base64_jpeg(cv2.cvtColor(img1, cv2.COLOR_BGR2RGB)),
            'enc_b_b64': numpy_to_base64_jpeg(cv2.cvtColor(img2, cv2.COLOR_BGR2RGB)),
            'dec_wrong_b64': numpy_to_base64_jpeg(cv2.cvtColor(dec_wrong, cv2.COLOR_BGR2RGB)),
            'pixel_diff_pct': round(diff_pct, 4),
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    # Verify model is loaded
    if classifier.model is None:
        print("\n  WARNING: rf_model.pkl not found!")
        print("  Run 'python train_model.py' to train the model first.\n")
    else:
        print("  Model loaded successfully.")

    print("\n" + "=" * 60)
    print("  CipherVision — Flask Server")
    print("  Open http://127.0.0.1:5000 in your browser")
    print("=" * 60 + "\n")
    app.run(debug=False, port=5000)
