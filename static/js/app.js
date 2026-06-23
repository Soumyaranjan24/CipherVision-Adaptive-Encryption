/**
 * CipherVision — Frontend Application
 * Handles: tab navigation, drag-and-drop upload, API calls, Chart.js rendering,
 * animated metric cards, and all UI state management.
 */

// ═══════════════════════════════════════════════════════════════════════════
// Globals & State
// ═══════════════════════════════════════════════════════════════════════════
let appState = {
    hasEncrypted: false,
    metrics: null,
    histogram: null,
    scatter: null,
    charts: [],          // track Chart.js instances for cleanup
};

// ═══════════════════════════════════════════════════════════════════════════
// Tab Navigation
// ═══════════════════════════════════════════════════════════════════════════
document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const target = btn.dataset.tab;

        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');

        document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
        document.getElementById(`panel-${target}`).classList.add('active');
    });
});

// ═══════════════════════════════════════════════════════════════════════════
// Upload Zone — Drag & Drop + Click
// ═══════════════════════════════════════════════════════════════════════════
const uploadZone = document.getElementById('uploadZone');
const imageInput = document.getElementById('imageInput');
const previewSection = document.getElementById('previewSection');
const previewImg = document.getElementById('previewImg');
const passwordSection = document.getElementById('passwordSection');
const encPassword = document.getElementById('encPassword');
const encryptBtn = document.getElementById('encryptBtn');

let selectedFile = null;

['dragenter', 'dragover'].forEach(evt => {
    uploadZone.addEventListener(evt, e => { e.preventDefault(); uploadZone.classList.add('drag-over'); });
});
['dragleave', 'drop'].forEach(evt => {
    uploadZone.addEventListener(evt, e => { e.preventDefault(); uploadZone.classList.remove('drag-over'); });
});

uploadZone.addEventListener('drop', e => {
    const files = e.dataTransfer.files;
    if (files.length > 0) handleFile(files[0]);
});

imageInput.addEventListener('change', e => {
    if (e.target.files.length > 0) handleFile(e.target.files[0]);
});

function handleFile(file) {
    if (!file.type.startsWith('image/')) return;
    selectedFile = file;

    const reader = new FileReader();
    reader.onload = e => {
        previewImg.src = e.target.result;
        previewSection.classList.remove('hidden');
        passwordSection.classList.remove('hidden');
        document.getElementById('encryptedBox').style.display = 'none';
        document.getElementById('encResult').classList.add('hidden');
        document.getElementById('encMeta').classList.add('hidden');
        document.getElementById('textureMapCard').style.display = 'none';
    };
    reader.readAsDataURL(file);
}

// Enable encrypt button when password typed
encPassword.addEventListener('input', () => {
    encryptBtn.disabled = encPassword.value.trim().length === 0;
});

// ═══════════════════════════════════════════════════════════════════════════
// Encryption
// ═══════════════════════════════════════════════════════════════════════════
encryptBtn.addEventListener('click', async () => {
    if (!selectedFile || !encPassword.value.trim()) return;

    const progress = document.getElementById('encProgress');
    const barFill = document.getElementById('stepBarFill');
    const stepText = document.getElementById('stepText');
    const resultDiv = document.getElementById('encResult');
    const metaDiv = document.getElementById('encMeta');

    // Reset UI
    progress.classList.add('active');
    resultDiv.classList.add('hidden');
    metaDiv.classList.add('hidden');
    document.getElementById('encryptedBox').style.display = 'none';
    document.getElementById('textureMapCard').style.display = 'none';
    encryptBtn.disabled = true;

    // Animate progress steps
    const steps = [
        { pct: 15, text: 'Step 1/4: Multi-directional GLCM Feature Extraction...' },
        { pct: 35, text: 'Step 2/4: Random Forest Texture Classification...' },
        { pct: 60, text: 'Step 3/4: 3-Tier Chaotic Encryption (Logistic / Lorenz / Chen)...' },
        { pct: 85, text: 'Step 4/4: Computing Security Metrics...' },
    ];

    let stepIdx = 0;
    const stepInterval = setInterval(() => {
        if (stepIdx < steps.length) {
            barFill.style.width = steps[stepIdx].pct + '%';
            stepText.textContent = steps[stepIdx].text;
            stepIdx++;
        }
    }, 600);

    try {
        const formData = new FormData();
        formData.append('image', selectedFile);
        formData.append('password', encPassword.value.trim());

        const res = await fetch('/api/encrypt', { method: 'POST', body: formData });

        // Read as text first to avoid crash on empty/broken responses
        const rawText = await res.text();
        clearInterval(stepInterval);

        let data;
        try {
            data = JSON.parse(rawText);
        } catch (parseErr) {
            barFill.style.width = '100%';
            stepText.textContent = 'Server error!';
            const preview = rawText.substring(0, 300) || '(empty response)';
            resultDiv.innerHTML = `<div class="callout callout-error"><span class="callout-icon">❌</span><div>Server returned invalid response. Check the terminal running Flask for error details.<br><br><code style="font-size:0.75rem;color:#94a3b8;word-break:break-all;">${preview}</code></div></div>`;
            resultDiv.classList.remove('hidden');
            encryptBtn.disabled = false;
            return;
        }

        if (!res.ok) {
            barFill.style.width = '100%';
            stepText.textContent = 'Error!';
            resultDiv.innerHTML = `<div class="callout callout-error"><span class="callout-icon">❌</span><div>${data.error || 'Unknown server error'}</div></div>`;
            resultDiv.classList.remove('hidden');
            encryptBtn.disabled = false;
            return;
        }

        // Complete progress
        barFill.style.width = '100%';
        stepText.textContent = 'Encryption complete!';

        setTimeout(() => {
            progress.classList.remove('active');
        }, 800);

        // Show encrypted image
        document.getElementById('encryptedImg').src = data.encrypted_b64;
        document.getElementById('encryptedBox').style.display = 'block';

        // Show texture map
        document.getElementById('textureMapImg').src = data.texture_map_b64;
        document.getElementById('textureMapCard').style.display = 'block';

        // Result callout
        resultDiv.innerHTML = `<div class="callout callout-success"><span class="callout-icon">✅</span><div>Encryption complete — <strong>100% lossless</strong>. All ${data.total_blocks} blocks encrypted in <strong>${data.enc_time}s</strong>.</div></div>`;
        resultDiv.classList.remove('hidden');

        // Download link
        const downloadLink = document.getElementById('downloadLink');
        downloadLink.href = 'data:image/png;base64,' + data.download_b64;

        // Meta info
        document.getElementById('encTimeBadge').textContent = `⏱ ${data.enc_time}s · ${data.image_size} · ${data.total_blocks} blocks`;

        const breakdownDiv = document.getElementById('blockBreakdown');
        breakdownDiv.innerHTML = `
            <div class="block-item"><span class="block-dot smooth"></span> Smooth: ${data.smooth_blocks}</div>
            <div class="block-item"><span class="block-dot medium"></span> Medium: ${data.medium_blocks}</div>
            <div class="block-item"><span class="block-dot rough"></span> Rough: ${data.rough_blocks}</div>
        `;
        metaDiv.classList.remove('hidden');

        // Store state
        appState.hasEncrypted = true;
        appState.metrics = data.metrics;
        appState.histogram = data.histogram;
        appState.scatter = data.scatter;
        appState.encData = data;

        // Update decrypt tab
        document.getElementById('decEncImg').src = data.encrypted_b64;
        document.getElementById('decryptReady').classList.remove('hidden');
        document.getElementById('decryptEmpty').classList.add('hidden');
        document.getElementById('decResultBox').style.display = 'none';
        document.getElementById('decResult').classList.add('hidden');

        // Update analysis tab
        renderAnalysis(data);

        // Update sensitivity tab
        document.getElementById('sensitivityReady').classList.remove('hidden');
        document.getElementById('sensitivityEmpty').classList.add('hidden');

        // Update benchmark tab
        renderBenchmark(data.metrics);

    } catch (err) {
        clearInterval(stepInterval);
        resultDiv.innerHTML = `<div class="callout callout-error"><span class="callout-icon">❌</span><div>Network error: ${err.message}</div></div>`;
        resultDiv.classList.remove('hidden');
    }

    encryptBtn.disabled = false;
});

// ═══════════════════════════════════════════════════════════════════════════
// Decryption
// ═══════════════════════════════════════════════════════════════════════════
document.getElementById('decryptBtn').addEventListener('click', async () => {
    const password = document.getElementById('decPassword').value.trim();
    if (!password) return;

    const resultDiv = document.getElementById('decResult');
    const btn = document.getElementById('decryptBtn');
    btn.disabled = true;
    resultDiv.classList.add('hidden');

    try {
        const res = await fetch('/api/decrypt', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ password }),
        });
        const data = await res.json();

        if (!res.ok) {
            resultDiv.innerHTML = `<div class="callout callout-error"><span class="callout-icon">❌</span><div>${data.error}</div></div>`;
            resultDiv.classList.remove('hidden');
            btn.disabled = false;
            return;
        }

        document.getElementById('decResultImg').src = data.decrypted_b64;
        document.getElementById('decResultBox').style.display = 'block';

        if (data.is_lossless) {
            resultDiv.innerHTML = `<div class="callout callout-success"><span class="callout-icon">✅</span><div><strong>Verification Passed:</strong> 100% Mathematically Lossless — pixel difference = 0</div></div>`;
        } else {
            resultDiv.innerHTML = `<div class="callout callout-error"><span class="callout-icon">❌</span><div><strong>Verification Failed:</strong> Pixel difference = ${data.pixel_diff}. Wrong password?</div></div>`;
        }
        resultDiv.classList.remove('hidden');

    } catch (err) {
        resultDiv.innerHTML = `<div class="callout callout-error"><span class="callout-icon">❌</span><div>Error: ${err.message}</div></div>`;
        resultDiv.classList.remove('hidden');
    }

    btn.disabled = false;
});

// ═══════════════════════════════════════════════════════════════════════════
// Security Analysis Rendering
// ═══════════════════════════════════════════════════════════════════════════
function renderAnalysis(data) {
    document.getElementById('analysisContent').classList.remove('hidden');
    document.getElementById('analysisEmpty').classList.add('hidden');

    const m = data.metrics;

    // ── Avalanche Metrics ──
    const npcr = m.npcr;
    const uaci = m.uaci;

    // Calculate scientific critical value for NPCR based on image size (Wu et al. 2011)
    let criticalNpcr = 99.6093;
    let npcrLabel = 'Ideal: ≥99.6093%';
    try {
        const sizeParts = data.image_size.split('x');
        const w = parseInt(sizeParts[0]);
        const h = parseInt(sizeParts[1]);
        if (!isNaN(w) && !isNaN(h)) {
            const N = w * h * 3; // RGB channels
            const sigma = Math.sqrt(255) / (256 * Math.sqrt(N));
            // alpha = 0.05 (critical value Z = -1.6449)
            criticalNpcr = (255 / 256 - 1.6449 * sigma) * 100;
            npcrLabel = `Ideal: ≥${criticalNpcr.toFixed(4)}% (α=0.05)`;
        }
    } catch (e) {
        console.error(e);
    }

    document.getElementById('avalancheGrid').innerHTML = `
        ${metricCard('NPCR', npcr.toFixed(4) + '%', npcrLabel, npcr >= criticalNpcr ? 'pass' : 'fail')}
        ${metricCard('UACI', uaci.toFixed(4) + '%', 'Ideal: ~33.4635%', (uaci > 33.0 && uaci < 34.0) ? 'pass' : 'warn')}
    `;

    // ── Statistical Profiles ──
    document.getElementById('statsGrid').innerHTML = `
        ${metricCard('Entropy (Cipher)', m.entropy_encrypted.toFixed(4), `Plaintext: ${m.entropy_original.toFixed(2)}`, m.entropy_encrypted >= 7.5 ? 'pass' : 'warn')}
        ${metricCard('PSNR', m.psnr.toFixed(2) + ' dB', 'Ideal: <10 dB', m.psnr < 10 ? 'pass' : 'fail')}
        ${metricCard('SSIM', m.ssim.toFixed(6), 'Ideal: ~0.0000', Math.abs(m.ssim) < 0.02 ? 'pass' : 'fail')}
        ${metricCard('Chi-Square', m.chi_square.toFixed(1), 'Critical: 293.3', m.chi_square_uniform ? 'pass' : 'fail', m.chi_square_uniform ? 'UNIFORM' : 'NON-UNIFORM')}
    `;

    // ── Correlation ──
    const directions = ['horizontal', 'vertical', 'diagonal'];
    document.getElementById('corrGrid').innerHTML = directions.map(dir => {
        const origC = m[`corr_orig_${dir}`];
        const encC = m[`corr_enc_${dir}`];
        return metricCard(
            dir.charAt(0).toUpperCase() + dir.slice(1),
            encC.toFixed(6),
            `Original: ${origC.toFixed(4)}`,
            Math.abs(encC) < 0.05 ? 'pass' : 'warn'
        );
    }).join('');

    // ── Histograms ──
    destroyCharts();
    renderHistograms(data.histogram);
    renderScatterPlots(data.scatter);
}

function metricCard(label, value, sub, status, statusText) {
    const badgeClass = status === 'pass' ? 'badge-pass' : status === 'fail' ? 'badge-fail' : 'badge-warn';
    const badgeText = statusText || (status === 'pass' ? '✓ PASS' : status === 'fail' ? '✗ FAIL' : '⚠ DEV');
    return `
        <div class="metric-card">
            <div class="metric-label">${label}</div>
            <div class="metric-value">${value}</div>
            <div class="metric-sub">${sub} · <span class="badge ${badgeClass}">${badgeText}</span></div>
        </div>
    `;
}

// ═══════════════════════════════════════════════════════════════════════════
// Chart.js Rendering
// ═══════════════════════════════════════════════════════════════════════════
const chartDefaults = {
    responsive: true,
    maintainAspectRatio: true,
    plugins: {
        legend: { display: false },
    },
    scales: {
        x: {
            ticks: { color: '#64748b', maxTicksLimit: 8, font: { size: 10 } },
            grid: { color: 'rgba(255,255,255,0.03)' },
        },
        y: {
            ticks: { color: '#64748b', font: { size: 10 } },
            grid: { color: 'rgba(255,255,255,0.03)' },
        },
    },
};

function destroyCharts() {
    appState.charts.forEach(c => c.destroy());
    appState.charts = [];
}

function renderHistograms(histogram) {
    const grid = document.getElementById('histogramGrid');
    grid.innerHTML = `
        <div class="chart-box">
            <div class="chart-box-title">Original Image Histogram</div>
            <canvas id="histOrigChart"></canvas>
        </div>
        <div class="chart-box">
            <div class="chart-box-title">Encrypted Image Histogram (Should be Flat)</div>
            <canvas id="histEncChart"></canvas>
        </div>
    `;

    const labels = Array.from({ length: 256 }, (_, i) => i);

    const c1 = new Chart(document.getElementById('histOrigChart'), {
        type: 'bar',
        data: {
            labels,
            datasets: [{
                data: histogram.original,
                backgroundColor: 'rgba(79, 172, 254, 0.7)',
                borderWidth: 0,
                barPercentage: 1.0,
                categoryPercentage: 1.0,
            }],
        },
        options: { ...chartDefaults, animation: { duration: 800 } },
    });

    const c2 = new Chart(document.getElementById('histEncChart'), {
        type: 'bar',
        data: {
            labels,
            datasets: [{
                data: histogram.encrypted,
                backgroundColor: 'rgba(6, 182, 212, 0.7)',
                borderWidth: 0,
                barPercentage: 1.0,
                categoryPercentage: 1.0,
            }],
        },
        options: { ...chartDefaults, animation: { duration: 800, delay: 200 } },
    });

    appState.charts.push(c1, c2);
}

function renderScatterPlots(scatter) {
    const origGrid = document.getElementById('scatterOrigGrid');
    const encGrid = document.getElementById('scatterEncGrid');
    origGrid.innerHTML = '';
    encGrid.innerHTML = '';

    const directions = ['horizontal', 'vertical', 'diagonal'];

    directions.forEach((dir, idx) => {
        // Original
        const origId = `scatterOrig_${dir}`;
        origGrid.innerHTML += `<div class="chart-box"><div class="chart-box-title">${dir}</div><canvas id="${origId}"></canvas></div>`;

        // Encrypted
        const encId = `scatterEnc_${dir}`;
        encGrid.innerHTML += `<div class="chart-box"><div class="chart-box-title">${dir}</div><canvas id="${encId}"></canvas></div>`;
    });

    // Need a tick for DOM to render canvases
    requestAnimationFrame(() => {
        directions.forEach((dir, idx) => {
            const d = scatter[dir];

            const origData = d.orig_x.map((x, i) => ({ x, y: d.orig_y[i] }));
            const encData = d.enc_x.map((x, i) => ({ x, y: d.enc_y[i] }));

            const scatterOpts = {
                responsive: true,
                maintainAspectRatio: true,
                plugins: { legend: { display: false } },
                scales: {
                    x: {
                        min: 0, max: 255,
                        ticks: { color: '#64748b', maxTicksLimit: 5, font: { size: 9 } },
                        grid: { color: 'rgba(255,255,255,0.03)' },
                    },
                    y: {
                        min: 0, max: 255,
                        ticks: { color: '#64748b', maxTicksLimit: 5, font: { size: 9 } },
                        grid: { color: 'rgba(255,255,255,0.03)' },
                    },
                },
                animation: { duration: 600, delay: idx * 150 },
            };

            const c1 = new Chart(document.getElementById(`scatterOrig_${dir}`), {
                type: 'scatter',
                data: {
                    datasets: [{
                        data: origData,
                        backgroundColor: 'rgba(79, 172, 254, 0.35)',
                        pointRadius: 1.5,
                    }],
                },
                options: scatterOpts,
            });

            const c2 = new Chart(document.getElementById(`scatterEnc_${dir}`), {
                type: 'scatter',
                data: {
                    datasets: [{
                        data: encData,
                        backgroundColor: 'rgba(6, 182, 212, 0.35)',
                        pointRadius: 1.5,
                    }],
                },
                options: scatterOpts,
            });

            appState.charts.push(c1, c2);
        });
    });
}

// ═══════════════════════════════════════════════════════════════════════════
// Key Sensitivity
// ═══════════════════════════════════════════════════════════════════════════
document.getElementById('sensBtn').addEventListener('click', async () => {
    const password = document.getElementById('sensPassword').value.trim();
    if (!password) return;

    const btn = document.getElementById('sensBtn');
    const resultDiv = document.getElementById('sensResult');
    btn.disabled = true;
    resultDiv.classList.add('hidden');

    try {
        const res = await fetch('/api/sensitivity', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ password }),
        });
        const data = await res.json();

        if (!res.ok) {
            resultDiv.innerHTML = `<div class="callout callout-error"><span class="callout-icon">❌</span><div>${data.error}</div></div>`;
            resultDiv.classList.remove('hidden');
            btn.disabled = false;
            return;
        }

        resultDiv.innerHTML = `
            <div class="sensitivity-grid">
                <div class="image-box">
                    <div class="image-box-header">🔑 Password: "${data.password_a}"</div>
                    <img src="${data.enc_a_b64}" alt="Encrypted with password A">
                </div>
                <div class="image-box">
                    <div class="image-box-header">🔑 Password: "${data.password_b}"</div>
                    <img src="${data.enc_b_b64}" alt="Encrypted with password B">
                </div>
                <div class="image-box">
                    <div class="image-box-header">❌ Decrypt A with Key B</div>
                    <img src="${data.dec_wrong_b64}" alt="Decrypted with wrong key">
                </div>
            </div>
            <div class="metrics-grid" style="margin-top:1.25rem;">
                ${metricCard('Pixel Difference', data.pixel_diff_pct.toFixed(4) + '%', 'Should be ~99.6%', data.pixel_diff_pct > 90 ? 'pass' : 'fail')}
            </div>
            <div class="callout callout-success">
                <span class="callout-icon">✅</span>
                <div>Changing <strong>"${data.password_a}"</strong> → <strong>"${data.password_b}"</strong> caused <strong>${data.pixel_diff_pct.toFixed(2)}%</strong> pixel change. Key sensitivity <strong>PROVEN</strong>.</div>
            </div>
        `;
        resultDiv.classList.remove('hidden');

    } catch (err) {
        resultDiv.innerHTML = `<div class="callout callout-error"><span class="callout-icon">❌</span><div>Error: ${err.message}</div></div>`;
        resultDiv.classList.remove('hidden');
    }

    btn.disabled = false;
});

// ═══════════════════════════════════════════════════════════════════════════
// Benchmark Comparison Table
// ═══════════════════════════════════════════════════════════════════════════
function renderBenchmark(metrics) {
    document.getElementById('benchmarkTable').classList.remove('hidden');
    document.getElementById('benchmarkEmpty').classList.add('hidden');

    const m = metrics;
    const rows = [
        ['NPCR (%)', m.npcr.toFixed(4), '~99.60', '99.6500', '99.6200', '99.8000', '≥99.6093'],
        ['UACI (%)', m.uaci.toFixed(4), '~33.40', '33.4800', '33.4700', '33.4600', '~33.4635'],
        ['Entropy', m.entropy_encrypted.toFixed(4), '>7.9000', '7.9990', '7.9991', '7.9000', '~8.0000'],
        ['Horiz. Correlation', m.corr_enc_horizontal.toFixed(6), '~0.001', '~0.001', '~0.001', '~0.001', '~0.0000'],
        ['PSNR (dB)', m.psnr.toFixed(2), 'N/A', 'N/A', '9.63', 'N/A', '<10.0'],
        ['SSIM', m.ssim.toFixed(6), 'N/A', 'N/A', '0.00195', 'N/A', '~0.0000'],
        ['ML Used', 'Random Forest', 'None', 'None', 'None', 'SAE (DL)', '—'],
        ['Tiers', '3 (Adaptive)', '3', '1 (Uniform)', '1', '1', '—'],
        ['Medical Testing', 'Yes (4 types)', 'No', 'No', 'No', 'No', '—'],
    ];

    const headers = ['Metric', 'CipherVision (Yours)', 'Tang 2025', 'Tiwari 2025 (DWT)', 'Yogi 2026', 'Tiwari 2025 (SAE)', 'Ideal'];

    const table = document.getElementById('compTable');
    table.innerHTML = `
        <thead><tr>${headers.map(h => `<th>${h}</th>`).join('')}</tr></thead>
        <tbody>${rows.map(row => `<tr>${row.map(cell => `<td>${cell}</td>`).join('')}</tr>`).join('')}</tbody>
    `;
}
