import cv2
import numpy as np
from skimage.feature import graycomatrix, graycoprops

class TextureAnalyzer:
    """
    Texture Analyzer using multi-directional, multi-distance GLCM.
    Extracts 8 averaged features across 4 angles × 2 distances = 8 GLCM combinations.
    
    Performance: Quantizes blocks to 32 grey levels for fast GLCM computation.
    A 16×16 block only has 256 pixels — a 32-level GLCM (32×32 matrix) captures
    texture patterns just as effectively as 256-level while being ~64× faster.
    """
    def __init__(self, block_size=16):
        self.block_size = block_size
        # 4 directions for rotational invariance, 3 distances for multi-scale
        self.distances = [1, 2, 3]
        self.angles = [0, np.pi/4, np.pi/2, 3*np.pi/4]
        # Quantize to 32 levels: 64x faster GLCM than 256 levels
        self.glcm_levels = 32

    def load_image(self, image_path):
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Image not found at {image_path}")
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        return img, gray

    def _pad_to_block_size(self, img, gray):
        """
        Pad image so dimensions are exact multiples of block_size.
        Uses reflect padding to avoid black borders affecting texture analysis.
        """
        h, w = gray.shape
        pad_h = (self.block_size - h % self.block_size) % self.block_size
        pad_w = (self.block_size - w % self.block_size) % self.block_size

        if pad_h > 0 or pad_w > 0:
            gray = cv2.copyMakeBorder(gray, 0, pad_h, 0, pad_w, cv2.BORDER_REFLECT)
            if len(img.shape) == 3:
                img = cv2.copyMakeBorder(img, 0, pad_h, 0, pad_w, cv2.BORDER_REFLECT)
            else:
                img = gray.copy()
        return img, gray

    def partition_image(self, gray_img):
        h, w = gray_img.shape
        blocks = []
        coordinates = []
        h_blocks = h // self.block_size
        w_blocks = w // self.block_size
        for i in range(h_blocks):
            for j in range(w_blocks):
                y_start, y_end = i * self.block_size, (i + 1) * self.block_size
                x_start, x_end = j * self.block_size, (j + 1) * self.block_size
                block = gray_img[y_start:y_end, x_start:x_end]
                blocks.append(block)
                coordinates.append((y_start, y_end, x_start, x_end))
        return blocks, coordinates

    def extract_features(self, block):
        """
        Extract 8 texture features averaged over 4 angles × 2 distances.
        Block is quantized to 32 grey levels for fast GLCM computation.
        """
        # Quantize to fewer grey levels for speed
        quantized = (block // (256 // self.glcm_levels)).astype(np.uint8)

        glcm = graycomatrix(
            quantized,
            distances=self.distances,
            angles=self.angles,
            levels=self.glcm_levels,
            symmetric=True,
            normed=True
        )

        # Average across all distance-angle combinations for rotation invariance
        contrast = graycoprops(glcm, 'contrast').mean()
        correlation = graycoprops(glcm, 'correlation').mean()
        energy = graycoprops(glcm, 'energy').mean()
        homogeneity = graycoprops(glcm, 'homogeneity').mean()
        dissimilarity = graycoprops(glcm, 'dissimilarity').mean()
        asm = graycoprops(glcm, 'ASM').mean()
        variance = np.var(block.astype(np.float64))

        # Local entropy (vectorized — no Python loop)
        hist = np.histogram(block, bins=256, range=(0, 256))[0]
        hist = hist / hist.sum()
        nonzero = hist[hist > 0]
        local_entropy = -np.sum(nonzero * np.log2(nonzero))

        return {
            'contrast': contrast,
            'correlation': correlation,
            'energy': energy,
            'homogeneity': homogeneity,
            'dissimilarity': dissimilarity,
            'asm': asm,
            'variance': variance,
            'local_entropy': local_entropy
        }

    def analyze(self, image_path=None, image_matrix=None):
        if image_matrix is not None:
            original = image_matrix.copy()
            if len(original.shape) == 3:
                gray = cv2.cvtColor(original, cv2.COLOR_BGR2GRAY)
            else:
                gray = original
        else:
            original, gray = self.load_image(image_path)

        # Pad to block size instead of discarding edge pixels
        original, gray = self._pad_to_block_size(original, gray)

        blocks, coords = self.partition_image(gray)
        features_list = []
        for i, block in enumerate(blocks):
            features = self.extract_features(block)
            features['block_idx'] = i
            features['coords'] = coords[i]
            features_list.append(features)
        return features_list, original, gray
