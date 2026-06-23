"""
CipherVision — Comprehensive Benchmark Suite
Tests standard benchmarks + medical images (MRI, Skin Cancer, Ultrasound).
Generates thesis-ready results table.
"""
import cv2
import numpy as np
from texture_analysis import TextureAnalyzer
from classifier import TextureClassifier
from encryption import AdaptiveEncryptor
from metrics import SecurityMetrics
import time
import os
import sys

# Reconfigure stdout to handle Unicode characters on Windows
try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

PASSWORD = 'MySecretKey2026!'

def run_test(name, img, analyzer, classifier, results_list):
    """Run full encrypt → decrypt → verify → metrics pipeline on one image."""
    feats, orig, gray = analyzer.analyze(image_matrix=img)
    preds = classifier.predict(feats)

    encryptor = AdaptiveEncryptor(PASSWORD)
    t0 = time.perf_counter()
    enc = encryptor.encrypt_image(orig, feats, preds)
    enc_time = time.perf_counter() - t0

    # Lossless decryption check
    dec = encryptor.decrypt_image(enc, feats, preds)
    lossless = np.array_equal(orig, dec)

    # NPCR/UACI — encrypt a 1-pixel-modified plaintext
    mod = orig.copy()
    mod[0, 0, 0] = (int(orig[0, 0, 0]) + 1) % 256
    enc_mod = encryptor.encrypt_image(mod, feats, preds)

    m = SecurityMetrics.full_analysis(orig, enc, enc_mod)

    s = int(np.sum(preds == 0))
    md = int(np.sum(preds == 1))
    r = int(np.sum(preds == 2))
    h, w = orig.shape[:2]

    row = {
        'name': name,
        'size': f"{w}×{h}",
        'blocks': len(feats),
        'smooth': s, 'medium': md, 'rough': r,
        'time': enc_time,
        'lossless': lossless,
        'entropy': m['entropy_encrypted'],
        'npcr': m.get('npcr', 0),
        'uaci': m.get('uaci', 0),
        'psnr': m['psnr'],
        'ssim': m['ssim'],
        'corr_h': m['corr_enc_horizontal'],
        'corr_v': m['corr_enc_vertical'],
        'corr_d': m['corr_enc_diagonal'],
        'chi_sq': m['chi_square'],
        'chi_uniform': m['chi_square_uniform'],
    }
    results_list.append(row)

    # Print live progress
    status = "✓ PASS" if lossless else "✗ FAIL"
    print(f"  [{status}] {name:<30s} | {w}×{h} | Entropy: {m['entropy_encrypted']:.4f} | "
          f"NPCR: {m.get('npcr',0):.2f}% | Time: {enc_time:.2f}s")
    return row


def print_thesis_table(results):
    """Print a formatted table suitable for thesis/paper reporting."""
    print("\n" + "=" * 110)
    print("  THESIS-READY RESULTS TABLE")
    print("=" * 110)
    header = (f"  {'Image':<25s} {'Size':<10s} {'Entropy':<10s} {'NPCR(%)':<10s} {'UACI(%)':<10s} "
              f"{'PSNR(dB)':<10s} {'SSIM':<10s} {'Corr(H)':<10s} {'Lossless':<10s}")
    print(header)
    print("  " + "-" * 105)
    for r in results:
        print(f"  {r['name']:<25s} {r['size']:<10s} {r['entropy']:<10.4f} {r['npcr']:<10.4f} "
              f"{r['uaci']:<10.4f} {r['psnr']:<10.2f} {r['ssim']:<10.6f} {r['corr_h']:<10.6f} "
              f"{'Yes' if r['lossless'] else 'NO':<10s}")
    print("  " + "-" * 105)

    # Summary statistics
    entropies = [r['entropy'] for r in results]
    npcrs = [r['npcr'] for r in results]
    uacis = [r['uaci'] for r in results]
    psnrs = [r['psnr'] for r in results]
    ssims = [r['ssim'] for r in results]
    all_lossless = all(r['lossless'] for r in results)

    print(f"  {'AVERAGE':<25s} {'—':<10s} {np.mean(entropies):<10.4f} {np.mean(npcrs):<10.4f} "
          f"{np.mean(uacis):<10.4f} {np.mean(psnrs):<10.2f} {np.mean(ssims):<10.6f} {'—':<10s} "
          f"{'ALL PASS' if all_lossless else 'FAIL':<10s}")
    print(f"  {'IDEAL':<25s} {'—':<10s} {'~8.0000':<10s} {'≥99.6093':<10s} {'~33.4635':<10s} "
          f"{'<10.00':<10s} {'~0.0000':<10s} {'~0.0000':<10s} {'Yes':<10s}")
    print("=" * 110)


def save_results_csv(results, filepath="test_results.csv"):
    """Save results to CSV for thesis appendix."""
    with open(filepath, 'w') as f:
        headers = ['Image', 'Size', 'Blocks', 'Smooth', 'Medium', 'Rough',
                    'Enc_Time(s)', 'Lossless', 'Entropy', 'NPCR(%)', 'UACI(%)',
                    'PSNR(dB)', 'SSIM', 'Corr_H', 'Corr_V', 'Corr_D',
                    'Chi_Square', 'Chi_Uniform']
        f.write(','.join(headers) + '\n')
        for r in results:
            vals = [r['name'], r['size'], str(r['blocks']),
                    str(r['smooth']), str(r['medium']), str(r['rough']),
                    f"{r['time']:.4f}", str(r['lossless']),
                    f"{r['entropy']:.6f}", f"{r['npcr']:.4f}", f"{r['uaci']:.4f}",
                    f"{r['psnr']:.4f}", f"{r['ssim']:.6f}",
                    f"{r['corr_h']:.6f}", f"{r['corr_v']:.6f}", f"{r['corr_d']:.6f}",
                    f"{r['chi_sq']:.2f}", str(r['chi_uniform'])]
            f.write(','.join(vals) + '\n')
    print(f"\n  Results saved to: {filepath}")


if __name__ == "__main__":
    print("=" * 70)
    print("  CipherVision — Comprehensive Benchmark Suite")
    print("  3-Tier Adaptive Chaotic Encryption Engine")
    print("=" * 70)

    analyzer = TextureAnalyzer()
    classifier = TextureClassifier()
    results = []

    # ── Section 1: Standard Benchmark Images ──
    print("\n─── Standard Benchmark Images ───")
    benchmarks = {
        "Lena (SIPI)":       "datasets/benchmark_hd/sipi_lena.png",
        "Baboon (SIPI)":     "datasets/benchmark_hd/sipi_baboon.png",
        "Airplane (SIPI)":   "datasets/benchmark_hd/sipi_airplane.png",
        "Astronaut":         "datasets/benchmark_hd/astronaut.png",
        "Coffee":            "datasets/benchmark_hd/coffee.png",
    }
    for name, path in benchmarks.items():
        img = cv2.imread(path)
        if img is None:
            print(f"  [SKIP] {name}: file not found at {path}")
            continue
        run_test(name, img, analyzer, classifier, results)

    # ── Section 2: Medical Imaging — Brain MRI ──
    print("\n─── Medical Imaging: Brain MRI (Alzheimer's Dataset) ───")
    mri_files = sorted([f for f in os.listdir("datasets/medical_hd") if f.startswith("brain_mri_") and not f.startswith("brain_mri_extra")])
    for f in mri_files[:3]:  # Test 3 diverse MRI scans
        path = os.path.join("datasets/medical_hd", f)
        img = cv2.imread(path)
        if img is None:
            continue
        run_test(f"Brain MRI ({f})", img, analyzer, classifier, results)

    # ── Section 3: Medical Imaging — Skin Cancer (Dermatoscopy) ──
    print("\n─── Medical Imaging: Skin Cancer (HAM10000 Dermatoscopy) ───")
    skin_files = sorted([f for f in os.listdir("datasets/medical_hd") if f.startswith("skin_cancer_")])
    for f in skin_files[:3]:  # Test 3 diverse skin lesion images
        path = os.path.join("datasets/medical_hd", f)
        img = cv2.imread(path)
        if img is None:
            continue
        run_test(f"Skin Cancer ({f})", img, analyzer, classifier, results)

    # ── Section 4: Medical Imaging — Ultrasound ──
    print("\n─── Medical Imaging: Breast Ultrasound ───")
    us_files = sorted([f for f in os.listdir("datasets/medical_hd") if f.startswith("ultrasound_")])
    for f in us_files[:2]:  # Test available ultrasound images
        path = os.path.join("datasets/medical_hd", f)
        img = cv2.imread(path)
        if img is None:
            continue
        run_test(f"Ultrasound ({f})", img, analyzer, classifier, results)

    # ── Final Report ──
    print_thesis_table(results)
    save_results_csv(results)

    # ── Overall Verdict ──
    all_lossless = all(r['lossless'] for r in results)
    avg_npcr = np.mean([r['npcr'] for r in results])
    avg_entropy = np.mean([r['entropy'] for r in results])
    
    print(f"\n  OVERALL VERDICT:")
    print(f"    Total images tested: {len(results)}")
    print(f"    Lossless decryption: {'ALL PASS ✓' if all_lossless else 'SOME FAILED ✗'}")
    print(f"    Avg NPCR: {avg_npcr:.4f}% (ideal ≥99.6093%)")
    print(f"    Avg Entropy: {avg_entropy:.4f} (ideal ~8.0)")
    print()
