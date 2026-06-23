import numpy as np
import hashlib

class AdaptiveEncryptor:
    """
    3-Tier Adaptive Chaotic Encryption Engine.
    
    Classification-based adaptive encryption:
      - Class 0 (Smooth): Logistic Map (lightweight, fast)
      - Class 1 (Medium): Lorenz Attractor (moderate complexity)
      - Class 2 (Rough/Complex): Hyperchaotic Chen System (strongest security)
    
    Each tier applies Permutation (confusion) + Substitution (diffusion).
    Key derivation uses SHA-256 for extreme key sensitivity.
    """
    def __init__(self, password="default_password"):
        # Hash the password using SHA-256 to generate a 256-bit key
        self.password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        # Split the 64-character hex hash into mathematical chunks for chaotic maps
        # Logistic Map parameters (from first 32 hex chars)
        self.logistic_x0 = (int(self.password_hash[:16], 16) / (16**16 - 1)) * 0.9 + 0.05
        self.logistic_r = (int(self.password_hash[16:32], 16) / (16**16 - 1)) * 0.04 + 3.96
        
        # Lorenz system initial conditions (from chars 32-62)
        self.lorenz_state0 = [
            (int(self.password_hash[32:42], 16) / (16**10 - 1)) * 10 + 1,
            (int(self.password_hash[42:52], 16) / (16**10 - 1)) * 10 + 1,
            (int(self.password_hash[52:62], 16) / (16**10 - 1)) * 10 + 1
        ]
        
        # Lorenz Parameters
        self.lorenz_sigma = 10.0
        self.lorenz_rho = 28.0
        self.lorenz_beta = 8.0 / 3.0
        
        # Hyperchaotic Chen parameters (from a secondary hash for independence)
        secondary_hash = hashlib.sha256((password + "_chen").encode()).hexdigest()
        self.chen_state0 = [
            (int(secondary_hash[:16], 16) / (16**16 - 1)) * 10 + 1,
            (int(secondary_hash[16:32], 16) / (16**16 - 1)) * 10 + 1,
            (int(secondary_hash[32:48], 16) / (16**16 - 1)) * 10 + 1,
            (int(secondary_hash[48:64], 16) / (16**16 - 1)) * 10 + 1
        ]

    def _logistic_map_sequence(self, length, x0):
        """Vectorized Logistic Map for speed. Used for smooth texture blocks."""
        seq = np.empty(length, dtype=np.float64)
        x = x0
        # Burn-in: skip first 200 transients for better chaotic behavior
        for _ in range(200):
            x = self.logistic_r * x * (1 - x)
        for i in range(length):
            x = self.logistic_r * x * (1 - x)
            seq[i] = x
        return seq

    def _lorenz_system_sequence(self, length, state0):
        """Lorenz attractor with RK4 integration for numerical stability."""
        seq = np.empty(length, dtype=np.float64)
        dt = 0.005
        x, y, z = state0
        sigma, rho, beta = self.lorenz_sigma, self.lorenz_rho, self.lorenz_beta
        
        # Burn-in
        for _ in range(500):
            # RK4 integration step
            k1x = sigma * (y - x)
            k1y = x * (rho - z) - y
            k1z = x * y - beta * z

            k2x = sigma * ((y + 0.5*dt*k1y) - (x + 0.5*dt*k1x))
            k2y = (x + 0.5*dt*k1x) * (rho - (z + 0.5*dt*k1z)) - (y + 0.5*dt*k1y)
            k2z = (x + 0.5*dt*k1x) * (y + 0.5*dt*k1y) - beta * (z + 0.5*dt*k1z)

            k3x = sigma * ((y + 0.5*dt*k2y) - (x + 0.5*dt*k2x))
            k3y = (x + 0.5*dt*k2x) * (rho - (z + 0.5*dt*k2z)) - (y + 0.5*dt*k2y)
            k3z = (x + 0.5*dt*k2x) * (y + 0.5*dt*k2y) - beta * (z + 0.5*dt*k2z)

            k4x = sigma * ((y + dt*k3y) - (x + dt*k3x))
            k4y = (x + dt*k3x) * (rho - (z + dt*k3z)) - (y + dt*k3y)
            k4z = (x + dt*k3x) * (y + dt*k3y) - beta * (z + dt*k3z)

            x += (dt / 6.0) * (k1x + 2*k2x + 2*k3x + k4x)
            y += (dt / 6.0) * (k1y + 2*k2y + 2*k3y + k4y)
            z += (dt / 6.0) * (k1z + 2*k2z + 2*k3z + k4z)
        
        for i in range(length):
            k1x = sigma * (y - x)
            k1y = x * (rho - z) - y
            k1z = x * y - beta * z

            k2x = sigma * ((y + 0.5*dt*k1y) - (x + 0.5*dt*k1x))
            k2y = (x + 0.5*dt*k1x) * (rho - (z + 0.5*dt*k1z)) - (y + 0.5*dt*k1y)
            k2z = (x + 0.5*dt*k1x) * (y + 0.5*dt*k1y) - beta * (z + 0.5*dt*k1z)

            k3x = sigma * ((y + 0.5*dt*k2y) - (x + 0.5*dt*k2x))
            k3y = (x + 0.5*dt*k2x) * (rho - (z + 0.5*dt*k2z)) - (y + 0.5*dt*k2y)
            k3z = (x + 0.5*dt*k2x) * (y + 0.5*dt*k2y) - beta * (z + 0.5*dt*k2z)

            k4x = sigma * ((y + dt*k3y) - (x + dt*k3x))
            k4y = (x + dt*k3x) * (rho - (z + dt*k3z)) - (y + dt*k3y)
            k4z = (x + dt*k3x) * (y + dt*k3y) - beta * (z + dt*k3z)

            x += (dt / 6.0) * (k1x + 2*k2x + 2*k3x + k4x)
            y += (dt / 6.0) * (k1y + 2*k2y + 2*k3y + k4y)
            z += (dt / 6.0) * (k1z + 2*k2z + 2*k3z + k4z)
            
            # Using X + Y + Z for higher entropy mixing
            seq[i] = x + y + z
            
        seq = (seq - np.min(seq)) / (np.max(seq) - np.min(seq) + 1e-12)
        return seq

    def _hyperchaotic_chen_sequence(self, length, state0):
        """
        4D Hyperchaotic Chen System — strongest tier for complex/rough textures.
        Reference: Paper 4 (Tang 2025) uses 4D Hyperchaos for high-complexity blocks.
        
        dx/dt = a*(y - x) + w
        dy/dt = d*x - x*z + c*y
        dz/dt = x*y - b*z
        dw/dt = y*z + r*w
        """
        a, b, c, d, r_param = 35.0, 3.0, 12.0, 7.0, 0.5
        dt = 0.001
        x, y, z, w = state0
        
        seq = np.empty(length, dtype=np.float64)
        
        # Burn-in for 1000 steps
        for _ in range(1000):
            dx = a * (y - x) + w
            dy = d * x - x * z + c * y
            dz = x * y - b * z
            dw = y * z + r_param * w
            x += dx * dt
            y += dy * dt
            z += dz * dt
            w += dw * dt
        
        for i in range(length):
            dx = a * (y - x) + w
            dy = d * x - x * z + c * y
            dz = x * y - b * z
            dw = y * z + r_param * w
            x += dx * dt
            y += dy * dt
            z += dz * dt
            w += dw * dt
            # Combine all 4 dimensions for maximum entropy
            seq[i] = x + y + z + w
        
        seq = (seq - np.min(seq)) / (np.max(seq) - np.min(seq) + 1e-12)
        return seq

    def _get_chaotic_sequence(self, length, texture_class, block_idx=0, feedback=0):
        """Select and dynamically perturb chaotic system based on texture classification tier, index, and feedback."""
        perturbation = ((block_idx * 2654435761) ^ feedback) & 0xFFFFFFFF
        norm_val = perturbation / 0xFFFFFFFF
        
        if texture_class == 0:
            # Logistic Map: perturb initial coordinate x0 by a scale of 1e-4
            perturbed_x0 = max(0.01, min(0.99, self.logistic_x0 + norm_val * 1e-4))
            return self._logistic_map_sequence(length, perturbed_x0)
        elif texture_class == 1:
            # Lorenz System: perturb initial state coordinates by a scale of 1.0
            perturbed_state = [
                self.lorenz_state0[0] + norm_val * 1.0,
                self.lorenz_state0[1] + norm_val * 1.0,
                self.lorenz_state0[2] + norm_val * 1.0
            ]
            return self._lorenz_system_sequence(length, perturbed_state)
        else:  # class 2 — complex/rough texture
            # Hyperchaotic Chen System: perturb initial state coordinates by a scale of 1.0
            perturbed_state = [
                self.chen_state0[0] + norm_val * 1.0,
                self.chen_state0[1] + norm_val * 1.0,
                self.chen_state0[2] + norm_val * 1.0,
                self.chen_state0[3] + norm_val * 1.0
            ]
            return self._hyperchaotic_chen_sequence(length, perturbed_state)

    def _permute_block(self, flat_block, chaotic_seq):
        """Scrambles pixel locations (Confusion phase)."""
        sort_indices = np.argsort(chaotic_seq)
        permuted_block = flat_block[sort_indices]
        return permuted_block, sort_indices

    def _inverse_permute_block(self, flat_block, sort_indices):
        """Reverses the permutation."""
        inverse_indices = np.argsort(sort_indices)
        original_block = flat_block[inverse_indices]
        return original_block

    def _encrypt_block(self, block, texture_class, block_idx=0, feedback=0):
        flat_block = block.flatten()
        length = len(flat_block)
        
        # 1. Generate perturbed chaotic sequence for this block
        chaotic_seq = self._get_chaotic_sequence(length, texture_class, block_idx=block_idx, feedback=feedback)
        keys = np.mod(np.abs(chaotic_seq) * 1e12, 256).astype(np.uint8)
            
        # 2. PERMUTATION (Scramble Pixel Locations — Confusion)
        permuted_block, _ = self._permute_block(flat_block, chaotic_seq)
            
        # 3. 2-PASS SUBSTITUTION & DIFFUSION (CBC-like inner pixel feedback with Addition Mod 256)
        # Pass 1: Forward Diffusion
        encrypted_flat = np.empty(length, dtype=np.uint8)
        prev = np.uint8(feedback & 0xFF)
        for i in range(length):
            curr_c = (int(permuted_block[i]) ^ int(keys[i])) + int(prev)
            curr_c = np.uint8(curr_c & 0xFF)
            encrypted_flat[i] = curr_c
            prev = curr_c
            
        # Pass 2: Backward Diffusion
        prev = np.uint8((feedback >> 8) & 0xFF)
        for i in range(length - 1, -1, -1):
            curr_c = (int(encrypted_flat[i]) ^ int(keys[(i + 17) % length])) + int(prev)
            curr_c = np.uint8(curr_c & 0xFF)
            encrypted_flat[i] = curr_c
            prev = curr_c
        
        return encrypted_flat.reshape(block.shape)
        
    def _decrypt_block(self, block, texture_class, block_idx=0, feedback=0):
        flat_block = block.flatten()
        length = len(flat_block)
        
        # 1. Generate identical perturbed chaotic sequence for this block
        chaotic_seq = self._get_chaotic_sequence(length, texture_class, block_idx=block_idx, feedback=feedback)
        keys = np.mod(np.abs(chaotic_seq) * 1e12, 256).astype(np.uint8)
        sort_indices = np.argsort(chaotic_seq)
        
        # 2. REVERSE 2-PASS SUBSTITUTION & DIFFUSION (with Subtraction Mod 256)
        # Reverse Pass 2: Backward Decryption
        decrypted_flat = np.empty(length, dtype=np.uint8)
        prev = np.uint8((feedback >> 8) & 0xFF)
        for i in range(length - 1, -1, -1):
            curr_c = flat_block[i]
            diff_val = (int(curr_c) - int(prev)) % 256
            curr_p = np.uint8(diff_val ^ int(keys[(i + 17) % length]))
            decrypted_flat[i] = curr_p
            prev = curr_c
            
        # Reverse Pass 1: Forward Decryption
        prev = np.uint8(feedback & 0xFF)
        for i in range(length):
            curr_c = decrypted_flat[i]
            diff_val = (int(curr_c) - int(prev)) % 256
            curr_p = np.uint8(diff_val ^ int(keys[i]))
            decrypted_flat[i] = curr_p
            prev = curr_c
        
        # 3. REVERSE PERMUTATION (Put pixels back in original spots)
        original_flat = self._inverse_permute_block(decrypted_flat, sort_indices)
        
        return original_flat.reshape(block.shape)


    def _global_diffusion(self, image):
        """
        Global pixel-level diffusion using logistic map (vectorized).
        Breaks cross-block correlations by XOR-ing a chaotic sequence
        across the entire flattened image. This is the final diffusion layer.
        """
        flat = image.flatten().astype(np.uint8)
        length = len(flat)
        
        # Use a different seed from block-level encryption
        x = (int(self.password_hash[8:24], 16) / (16**16 - 1)) * 0.9 + 0.05
        r = 3.9999
        
        # Vectorized chaotic sequence generation (process in chunks for speed)
        keys = np.empty(length, dtype=np.uint8)
        chunk_size = 10000
        for start in range(0, length, chunk_size):
            end = min(start + chunk_size, length)
            chunk_len = end - start
            chunk = np.empty(chunk_len, dtype=np.float64)
            for j in range(chunk_len):
                x = r * x * (1 - x)
                chunk[j] = x
            keys[start:end] = np.mod(np.abs(chunk) * 1e12, 256).astype(np.uint8)
        
        diffused = np.bitwise_xor(flat, keys)
        return diffused.reshape(image.shape)

    def _feedback_bytes(self, feedback, shape):
        """Spread 32-bit feedback across all pixels using 4-byte rotation."""
        b0 = np.uint8(feedback & 0xFF)
        b1 = np.uint8((feedback >> 8) & 0xFF)
        b2 = np.uint8((feedback >> 16) & 0xFF)
        b3 = np.uint8((feedback >> 24) & 0xFF)
        h, w = shape[:2]
        fb = np.empty(shape, dtype=np.uint8)
        if len(shape) == 3:
            fb[:, :, 0] = b0 ^ b2
            fb[:, :, 1] = b1 ^ b3
            fb[:, :, 2] = b0 ^ b1
        else:
            fb[:, :] = b0 ^ b1 ^ b2 ^ b3
        return fb

    def encrypt_image(self, original_img, features_list, predictions):
        """
        3-phase encryption:
          1. Inter-block feedback diffusion (full 32-bit spread)
          2. Per-block adaptive chaotic encryption (permutation + substitution)
          3. Global pixel-level diffusion (breaks cross-block correlation)
        """
        encrypted_img = original_img.copy()
        feedback = int(self.password_hash[:8], 16)
        
        for i, features in enumerate(features_list):
            y_start, y_end, x_start, x_end = features['coords']
            pred = predictions[i]
            
            block = original_img[y_start:y_end, x_start:x_end].copy()
            
            # Phase 1: Inter-block feedback (spread 32 bits across all pixels)
            fb = self._feedback_bytes(feedback, block.shape)
            block = np.bitwise_xor(block, fb)
            
            # Phase 2: Block-level chaotic encryption (perturbed by block index + feedback)
            encrypted_block = self._encrypt_block(block, pred, block_idx=i, feedback=feedback)
            encrypted_img[y_start:y_end, x_start:x_end] = encrypted_block
            
            # Stronger feedback: hash-like mixing of block sum + position
            block_sum = int(np.sum(encrypted_block))
            feedback = ((feedback * 1103515245 + block_sum) ^ (i * 2654435761)) & 0xFFFFFFFF
        
        # Phase 3: Global diffusion
        encrypted_img = self._global_diffusion(encrypted_img)
        
        return encrypted_img

    def decrypt_image(self, encrypted_img, features_list, predictions):
        """
        Reverse 3-phase decryption (in reverse order).
        """
        # Reverse Phase 3: Global diffusion (XOR is self-inverse with same key)
        decrypted_img = self._global_diffusion(encrypted_img)
        
        # We need to reconstruct the feedback chain from the block-encrypted state
        # (before global diffusion was applied during encryption)
        feedback = int(self.password_hash[:8], 16)
        
        # First pass: compute all feedback values from block-encrypted image
        feedbacks = [feedback]
        for i, features in enumerate(features_list):
            y_start, y_end, x_start, x_end = features['coords']
            block = decrypted_img[y_start:y_end, x_start:x_end]
            block_sum = int(np.sum(block))
            feedback = ((feedback * 1103515245 + block_sum) ^ (i * 2654435761)) & 0xFFFFFFFF
            feedbacks.append(feedback)
        
        # Second pass: decrypt blocks
        for i, features in enumerate(features_list):
            y_start, y_end, x_start, x_end = features['coords']
            pred = predictions[i]
            
            block = decrypted_img[y_start:y_end, x_start:x_end].copy()
            
            # Reverse Phase 2: Block-level decryption (same perturbation)
            decrypted_block = self._decrypt_block(block, pred, block_idx=i, feedback=feedbacks[i])
            
            # Reverse Phase 1: Inter-block feedback (same 32-bit spread)
            fb = self._feedback_bytes(feedbacks[i], decrypted_block.shape)
            decrypted_block = np.bitwise_xor(decrypted_block, fb)
            
            decrypted_img[y_start:y_end, x_start:x_end] = decrypted_block
            
        return decrypted_img
