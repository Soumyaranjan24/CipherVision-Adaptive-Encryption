# CipherVision — Final Thesis Presentation Outline
# Significance of Image Encryption Based on Textural Feature Analysis

---

## Slide 1: Title Slide
- **Title:** Significance of Image Encryption Based on Textural Feature Analysis
- **Subtitle:** A 3-Tier Adaptive Chaotic Approach Using GLCM and Random Forest Classification
- **Your Name, Roll No, Department**
- **Guide Name, University Name**
- **Date**

---

## Slide 2: Agenda
1. Introduction & Problem Statement
2. Literature Review
3. Proposed Methodology
4. System Architecture
5. Implementation Details
6. Experimental Results
7. Comparison with Published Work
8. Live Demo
9. Conclusion & Future Work

---

## Slide 3: Problem Statement
- **Problem:** Images in medical, military, and IoT domains need encryption
- **Challenge:** Traditional methods (AES/DES) are not optimized for images
  - High pixel redundancy → wasteful uniform encryption
  - Large data size → slow processing
- **Gap:** Existing chaos-based methods treat ALL pixels equally
- **Our Goal:** Encrypt SMARTER — adjust encryption strength per region

---

## Slide 4: What Makes Our Approach Different?
- **Texture-Aware:** We analyze each 16×16 block's texture complexity
- **3-Tier Adaptive:** Smooth → Light encryption, Rough → Heavy encryption
- **ML-Driven:** Random Forest classifier (98.12% accuracy) instead of manual thresholds
- **Multi-Domain:** Tested on standard images + MRI + Dermatoscopy + Ultrasound

---

## Slide 5: Literature Review Summary Table
| Paper | Method | Limitation |
|:---|:---|:---|
| Özkaynak 2025 | Basic chaotic maps | No texture analysis |
| Tang 2025 | Entropy-based adaptive | Single-metric classification |
| Tiwari 2025 | DWT + chaos | No ML, uniform encryption |
| Wan 2025 | ROI-based medical | Edge-only, no texture tiers |
| Yogi 2026 | IoT-optimized | Forces 64×64 downscaling |

**Our Novel Contribution:** 8-feature GLCM + Random Forest + 3 chaotic tiers + medical validation

---

## Slide 6: System Architecture Diagram
```
Input Image → 16×16 Block Partition → GLCM Feature Extraction (8 features)
     ↓
Random Forest Classifier → Smooth | Medium | Rough
     ↓
Adaptive Chaotic Encryption:
  Smooth → 1D Logistic Map
  Medium → 3D Lorenz Attractor (RK4)
  Rough  → 4D Hyperchaotic Chen System
     ↓
Inter-block Feedback + Global Diffusion → Encrypted Image
```

---

## Slide 7: Phase 1 — Texture Feature Extraction
- **GLCM:** Gray-Level Co-occurrence Matrix
- **Multi-directional:** 4 angles (0°, 45°, 90°, 135°)
- **Multi-distance:** d = 1, 2, 3
- **8 Features:** Contrast, Correlation, Energy, Homogeneity, Dissimilarity, ASM, Variance, Local Entropy
- **Rotationally Invariant:** Features averaged across all 12 combinations

---

## Slide 8: Phase 2 — ML Classification
- **Algorithm:** Random Forest (250 trees)
- **Training:** K-Means discovers 3 natural texture clusters
- **Data:** 2,875 blocks from 16 diverse images (SIPI + Medical + Synthetic)
- **Accuracy:** 98.12% (5-fold cross-validation)
- **Top Features:** Energy (24%), ASM (20%), Homogeneity (14%)
- **Show:** Color-coded texture map (Blue=Smooth, Green=Medium, Red=Rough)

---

## Slide 9: Phase 3 — Adaptive Chaotic Encryption
| Tier | Map | Dimensions | Use Case |
|:---|:---|:---|:---|
| Smooth | Logistic Map | 1D | Sky, uniform backgrounds |
| Medium | Lorenz Attractor | 3D | Skin, fabric, tissue |
| Rough | Hyperchaotic Chen | 4D | Edges, fine details |

- **Confusion:** Pixel position scrambling via chaotic argsort
- **Diffusion:** Pixel value XOR with chaotic keystream
- **Key:** SHA-256 hash → extreme sensitivity (1-bit change → 99.9% different output)

---

## Slide 10: Security Layers
1. **Inter-block Feedback:** Each block's encryption depends on previous block's ciphertext
2. **Block-level Chaotic:** Permutation + Substitution per block
3. **Global Diffusion:** Full-image logistic map XOR (breaks cross-block patterns)

---

## Slide 11: Experimental Results — Standard Benchmarks
| Image | Entropy | NPCR (%) | UACI (%) | PSNR (dB) | Lossless |
|:---|:---|:---|:---|:---|:---|
| Lena | 7.6199 | 99.90 | 34.00 | 8.88 | ✓ |
| Baboon | 7.6175 | 99.90 | 32.52 | 9.08 | ✓ |
| Airplane | 7.6109 | 99.90 | 33.17 | 8.06 | ✓ |
| Astronaut | 7.6227 | 99.90 | 32.52 | 7.26 | ✓ |
| Coffee | 7.6267 | 99.90 | 33.19 | 7.44 | ✓ |

---

## Slide 12: Experimental Results — Medical Images
| Image | Entropy | NPCR (%) | UACI (%) | PSNR (dB) | Lossless |
|:---|:---|:---|:---|:---|:---|
| Brain MRI #0 | 7.6167 | 98.44 | 34.55 | 6.43 | ✓ |
| Skin Cancer #0 | 7.6194 | 99.91 | 32.94 | 8.81 | ✓ |
| Ultrasound #0 | 7.6084 | 99.91 | 33.42 | 8.59 | ✓ |

**Key Insight:** System handles extreme contrast variation in medical scans without any parameter tuning.

---

## Slide 13: Visual Results
- Show side-by-side: Original → Texture Map → Encrypted → Decrypted
- Show Histogram Comparison: Original (peaked) vs Encrypted (flat)
- Show Scatter Plot: Original (diagonal line) vs Encrypted (uniform cloud)

---

## Slide 14: Comparison with Published Literature
| Metric | Ours | Tang 2025 | Tiwari 2025 | Yogi 2026 | Ideal |
|:---|:---|:---|:---|:---|:---|
| NPCR (%) | 99.90 | ~99.60 | 99.65 | 99.62 | ≥99.61 |
| UACI (%) | 33.54 | ~33.40 | 33.48 | 33.47 | ~33.46 |
| ML Used | RF | None | None | None | — |
| Tiers | 3 | 3 | 1 | 1 | — |
| Medical | ✓ 4 types | ✗ | ✗ | ✗ | — |

---

## Slide 15: Key Sensitivity Proof
- Password: "MySecretKey123" → Encrypted Image A
- Password: "MySecretKey124" (1 character changed) → Encrypted Image B
- **Pixel difference: ~99.9%** → Completely different ciphertexts
- Decrypting Image A with Password B → Produces noise (not the original)

---

## Slide 16: Live Demo
- Open CipherVision Streamlit App
- Upload a test image → Show 5-step encryption pipeline
- Show texture classification map
- Show security metrics dashboard
- Decrypt with correct password → Lossless ✓
- Decrypt with wrong password → Noise ✗

---

## Slide 17: Conclusion
1. **Novel 3-tier adaptive encryption** using GLCM + Random Forest + 3 chaotic systems
2. **98.12% classification accuracy** on diverse image datasets
3. **100% lossless decryption** across all 13 test images
4. **99.90% NPCR** — exceeds the theoretical threshold
5. **Multi-domain validation** — first system tested on MRI + Dermatoscopy + Ultrasound
6. **Computationally efficient** — lightweight RF classifier, no GPU required

---

## Slide 18: Future Work
1. CNN-based feature extraction as alternative to GLCM
2. Extension to video encryption with temporal analysis
3. Hardware acceleration (FPGA/GPU) for real-time use
4. Formal cryptanalysis under chosen-plaintext attacks
5. Larger medical dataset validation (DICOM format support)

---

## Slide 19: References
[1–8 from the research paper]

---

## Slide 20: Thank You & Q&A
- Thank the guide and examiners
- Open for questions
