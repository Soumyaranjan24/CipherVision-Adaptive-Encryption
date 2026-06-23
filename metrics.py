import numpy as np
import cv2
import math
import io

class SecurityMetrics:
    """
    Comprehensive security analysis suite for image encryption evaluation.
    Includes: Entropy, NPCR, UACI, 3-direction Correlation, Histogram Analysis,
    Chi-Square Test, PSNR, and SSIM.
    """
    
    @staticmethod
    def information_entropy(image):
        """
        Calculates Information Entropy of the image.
        For multi-channel (color) images, returns the average entropy across all channels.
        Ideal value for a perfectly encrypted 8-bit channel is 8.0.
        """
        if len(image.shape) == 3:
            entropies = []
            for c in range(image.shape[2]):
                channel = image[:, :, c]
                histogram, _ = np.histogram(channel.flatten(), bins=256, range=(0, 256))
                histogram = histogram / float(np.sum(histogram))
                c_entropy = -np.sum([p * math.log2(p) for p in histogram if p > 0])
                entropies.append(c_entropy)
            return float(np.mean(entropies))
        else:
            histogram, _ = np.histogram(image.flatten(), bins=256, range=(0, 256))
            histogram = histogram / float(np.sum(histogram))
            return float(-np.sum([p * math.log2(p) for p in histogram if p > 0]))


    @staticmethod
    def npcr(c1, c2):
        """
        Number of Pixels Change Rate (NPCR).
        Measures sensitivity to plaintext changes.
        Ideal value ~ 99.6093% (for 8-bit images).
        """
        diff = np.where(c1 != c2, 1, 0)
        return (np.sum(diff) / float(c1.size)) * 100

    @staticmethod
    def uaci(c1, c2):
        """
        Unified Average Changing Intensity (UACI).
        Measures average intensity of differences.
        Ideal value ~ 33.4635%.
        """
        diff = np.abs(c1.astype(np.float64) - c2.astype(np.float64))
        return (np.sum(diff) / (255.0 * c1.size)) * 100

    @staticmethod
    def correlation_coefficient(image, direction='horizontal', num_pairs=5000):
        """
        Calculates correlation coefficient of adjacent pixel pairs.
        
        Args:
            image: Input image
            direction: 'horizontal', 'vertical', or 'diagonal'
            num_pairs: Number of random pairs to sample
            
        Returns:
            Correlation coefficient. Ideal for encrypted: ~0.0
        """
        if len(image.shape) == 3:
            img_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            img_gray = image
            
        h, w = img_gray.shape
        N = min(num_pairs, (h - 1) * (w - 1))
        
        np.random.seed(42)  # Reproducible results
        
        if direction == 'horizontal':
            x = np.random.randint(0, w - 1, N)
            y = np.random.randint(0, h, N)
            pixels_1 = img_gray[y, x].astype(np.float64)
            pixels_2 = img_gray[y, x + 1].astype(np.float64)
        elif direction == 'vertical':
            x = np.random.randint(0, w, N)
            y = np.random.randint(0, h - 1, N)
            pixels_1 = img_gray[y, x].astype(np.float64)
            pixels_2 = img_gray[y + 1, x].astype(np.float64)
        elif direction == 'diagonal':
            x = np.random.randint(0, w - 1, N)
            y = np.random.randint(0, h - 1, N)
            pixels_1 = img_gray[y, x].astype(np.float64)
            pixels_2 = img_gray[y + 1, x + 1].astype(np.float64)
        else:
            raise ValueError(f"Unknown direction: {direction}")
        
        mean_1 = np.mean(pixels_1)
        mean_2 = np.mean(pixels_2)
        
        numerator = np.sum((pixels_1 - mean_1) * (pixels_2 - mean_2))
        var_1 = np.sum((pixels_1 - mean_1)**2)
        var_2 = np.sum((pixels_2 - mean_2)**2)
        
        if var_1 == 0 or var_2 == 0:
            return 0.0
            
        corr = numerator / np.sqrt(var_1 * var_2)
        return corr

    @staticmethod
    def all_correlations(image, num_pairs=5000):
        """Compute correlation in all 3 directions."""
        return {
            'horizontal': SecurityMetrics.correlation_coefficient(image, 'horizontal', num_pairs),
            'vertical': SecurityMetrics.correlation_coefficient(image, 'vertical', num_pairs),
            'diagonal': SecurityMetrics.correlation_coefficient(image, 'diagonal', num_pairs)
        }

    @staticmethod
    def histogram_data(image):
        """Get histogram data for all byte values across all channels."""
        histogram, bin_edges = np.histogram(image.flatten(), bins=256, range=(0, 256))
        return histogram, bin_edges

    @staticmethod
    def chi_square_test(image):
        """
        Chi-Square Uniformity Test for encrypted image histogram.
        Tests whether the histogram is uniformly distributed across channels.
        A well-encrypted image should have average chi-square < 293.25 
        (critical value for df=255 at α=0.05).
        """
        if len(image.shape) == 3:
            chi_squares = []
            uniform_flags = []
            for c in range(image.shape[2]):
                channel = image[:, :, c]
                histogram, _ = np.histogram(channel.flatten(), bins=256, range=(0, 256))
                expected = channel.size / 256.0
                chi_sq = np.sum((histogram - expected) ** 2 / expected)
                chi_squares.append(chi_sq)
                uniform_flags.append(chi_sq < 293.25)
            return float(np.mean(chi_squares)), all(uniform_flags), 293.25
        else:
            histogram, _ = np.histogram(image.flatten(), bins=256, range=(0, 256))
            expected = image.size / 256.0
            chi_sq = np.sum((histogram - expected) ** 2 / expected)
            critical_value = 293.25
            is_uniform = chi_sq < critical_value
            return float(chi_sq), is_uniform, critical_value


    @staticmethod
    def psnr(original, encrypted):
        """
        Peak Signal-to-Noise Ratio between original and encrypted image.
        Lower PSNR = better encryption (images are more dissimilar).
        Typically should be < 10 dB for good encryption.
        """
        mse = np.mean((original.astype(np.float64) - encrypted.astype(np.float64)) ** 2)
        if mse == 0:
            return float('inf')
        return 20 * math.log10(255.0 / math.sqrt(mse))

    @staticmethod
    def ssim(original, encrypted):
        """
        Structural Similarity Index (simplified implementation).
        Value close to 0 = good encryption (no structural similarity preserved).
        Value close to 1 = bad (structure is preserved).
        """
        if len(original.shape) == 3:
            original = cv2.cvtColor(original, cv2.COLOR_BGR2GRAY)
        if len(encrypted.shape) == 3:
            encrypted = cv2.cvtColor(encrypted, cv2.COLOR_BGR2GRAY)
        
        original = original.astype(np.float64)
        encrypted = encrypted.astype(np.float64)
        
        C1 = (0.01 * 255) ** 2
        C2 = (0.03 * 255) ** 2
        
        mu_x = np.mean(original)
        mu_y = np.mean(encrypted)
        sigma_x = np.std(original)
        sigma_y = np.std(encrypted)
        sigma_xy = np.mean((original - mu_x) * (encrypted - mu_y))
        
        numerator = (2 * mu_x * mu_y + C1) * (2 * sigma_xy + C2)
        denominator = (mu_x**2 + mu_y**2 + C1) * (sigma_x**2 + sigma_y**2 + C2)
        
        return numerator / denominator

    @staticmethod
    def get_scatter_data(image, direction='horizontal', num_pairs=3000):
        """
        Get adjacent pixel pair data for scatter plot visualization.
        
        Returns (pixels_1, pixels_2) arrays for plotting.
        Original image: shows a dense diagonal line (high correlation).
        Encrypted image: shows a uniform cloud (no correlation).
        """
        if len(image.shape) == 3:
            img_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            img_gray = image
            
        h, w = img_gray.shape
        N = min(num_pairs, (h - 1) * (w - 1))
        
        np.random.seed(42)
        
        if direction == 'horizontal':
            x = np.random.randint(0, w - 1, N)
            y = np.random.randint(0, h, N)
            p1 = img_gray[y, x].astype(np.float64)
            p2 = img_gray[y, x + 1].astype(np.float64)
        elif direction == 'vertical':
            x = np.random.randint(0, w, N)
            y = np.random.randint(0, h - 1, N)
            p1 = img_gray[y, x].astype(np.float64)
            p2 = img_gray[y + 1, x].astype(np.float64)
        else:  # diagonal
            x = np.random.randint(0, w - 1, N)
            y = np.random.randint(0, h - 1, N)
            p1 = img_gray[y, x].astype(np.float64)
            p2 = img_gray[y + 1, x + 1].astype(np.float64)
        
        return p1, p2

    @staticmethod
    def full_analysis(original, encrypted, encrypted_modified=None):
        """
        Run the complete security analysis suite.
        
        Args:
            original: Original plaintext image
            encrypted: Encrypted ciphertext image
            encrypted_modified: Encrypted version of 1-pixel-changed plaintext (for NPCR/UACI)
            
        Returns:
            Dictionary with all metrics
        """
        results = {
            'entropy_original': SecurityMetrics.information_entropy(original),
            'entropy_encrypted': SecurityMetrics.information_entropy(encrypted),
            'psnr': SecurityMetrics.psnr(original, encrypted),
            'ssim': SecurityMetrics.ssim(original, encrypted),
        }
        
        # 3-direction correlations
        for direction in ['horizontal', 'vertical', 'diagonal']:
            results[f'corr_orig_{direction}'] = SecurityMetrics.correlation_coefficient(
                original, direction
            )
            results[f'corr_enc_{direction}'] = SecurityMetrics.correlation_coefficient(
                encrypted, direction
            )
        
        # Chi-square test
        chi_sq, is_uniform, critical = SecurityMetrics.chi_square_test(encrypted)
        results['chi_square'] = chi_sq
        results['chi_square_uniform'] = is_uniform
        results['chi_square_critical'] = critical
        
        # NPCR / UACI (if modified encrypted image is provided)
        if encrypted_modified is not None:
            results['npcr'] = SecurityMetrics.npcr(encrypted, encrypted_modified)
            results['uaci'] = SecurityMetrics.uaci(encrypted, encrypted_modified)
        
        return results


if __name__ == "__main__":
    print("Security Metrics Module Loaded.")
    try:
        orig_img = cv2.imread('test.jpg')
        enc_img = cv2.imread('encrypted_test.png')
        
        if orig_img is not None and enc_img is not None:
            results = SecurityMetrics.full_analysis(orig_img, enc_img)
            print("\n=== Full Security Analysis ===")
            for key, value in results.items():
                if isinstance(value, float):
                    print(f"  {key:>25s}: {value:.6f}")
                else:
                    print(f"  {key:>25s}: {value}")
    except Exception as e:
        print(f"Error computing metrics: {e}")
