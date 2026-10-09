// OptiCleaner v4.0 - Interactive Web Ecosystem Controller

// Simulated Live Dashboard Gauges
let cpuVal = 24;
let ramVal = 58;
let diskVal = 42;

function updateGauges() {
    // Subtle realistic fluctuation
    cpuVal = Math.max(12, Math.min(85, cpuVal + (Math.random() * 8 - 4)));
    ramVal = Math.max(45, Math.min(75, ramVal + (Math.random() * 2 - 1)));

    const cpuEl = document.getElementById("gauge-cpu");
    const ramEl = document.getElementById("gauge-ram");
    const cpuTxt = document.getElementById("gauge-cpu-val");
    const ramTxt = document.getElementById("gauge-ram-val");

    if (cpuEl && cpuTxt) {
        cpuEl.style.setProperty("--val", Math.round(cpuVal));
        cpuTxt.innerText = `${Math.round(cpuVal)}%`;
    }
    if (ramEl && ramTxt) {
        ramEl.style.setProperty("--val", Math.round(ramVal));
        ramTxt.innerText = `${Math.round(ramVal)}%`;
    }
}

setInterval(updateGauges, 2000);

// Switch Dashboard Tabs
function switchDashTab(tabIdx) {
    const tabs = document.querySelectorAll(".dash-nav-item");
    tabs.forEach((t, i) => {
        if (i === tabIdx) t.classList.add("active");
        else t.classList.remove("active");
    });

    const term = document.getElementById("dash-log");
    if (!term) return;

    if (tabIdx === 0) {
        term.innerHTML = `
            <div class="log-line">[SCANNER] Analyzing %TEMP% and user crash dumps...</div>
            <div class="log-line text-cyan">[SCANNER] Browser caches calculated: 1,420 MB reclaimable.</div>
            <div class="log-line text-green">[STATUS] Ready to purge.</div>
        `;
    } else if (tabIdx === 1) {
        term.innerHTML = `
            <div class="log-line">[OPTIMIZER] Ultimate Performance profile active.</div>
            <div class="log-line text-cyan">[OPTIMIZER] Game Booster Daemon watching 14 titles.</div>
            <div class="log-line text-purple">[KERNEL] High precision timer 0.5ms confirmed.</div>
        `;
    } else if (tabIdx === 2) {
        term.innerHTML = `
            <div class="log-line">[HARDWARE] CPU: AMD Ryzen 9 / Intel Core i9 (16 Cores).</div>
            <div class="log-line text-blue">[MEMORY] 32.0 GB DDR5 @ 6000 MHz.</div>
            <div class="log-line text-green">[STORAGE] Samsung 990 PRO NVMe (Healthy 99%).</div>
        `;
    }
}

// Simulate Quick Boost Button
function simulateOptimize() {
    const term = document.getElementById("dash-log");
    if (!term) return;

    term.innerHTML = `
        <div class="log-line text-cyan">[BOOST] Triggering NtSetSystemInformation MemoryPurgeStandbyList...</div>
        <div class="log-line text-cyan">[BOOST] EmptyWorkingSet executed on 48 processes...</div>
        <div class="log-line text-green">[SUCCESS] Freed 3,420 MB of RAM! Kernel timer locked to 0.5ms.</div>
    `;

    ramVal = 38;
    cpuVal = 14;
    updateGauges();
}

// Checkout Modal Logic
function openCheckout(planTitle, planPrice) {
    document.getElementById("modalPlanTitle").innerText = `${planTitle} License`;
    document.getElementById("modalPlanPrice").innerText = planPrice;
    document.getElementById("payForm").style.display = "block";
    document.getElementById("paySuccess").style.display = "none";
    document.getElementById("checkoutModal").style.display = "flex";
}

function closeCheckout() {
    document.getElementById("checkoutModal").style.display = "none";
}

function switchPayMethod(method) {
    const tabs = document.querySelectorAll(".pay-tab");
    tabs.forEach(t => t.classList.remove("active"));
    if (method === "card") tabs[0].classList.add("active");
    else tabs[1].classList.add("active");
}

function processMockPayment() {
    const hwid = document.getElementById("payHwid").value.trim() || "OC-8B42-19FA-E821";
    document.getElementById("payForm").style.display = "none";
    document.getElementById("paySuccess").style.display = "block";

    // Simulate Ed25519 Token Generation
    const payload = btoa(JSON.stringify({
        hwid: hwid,
        tier: "PRO",
        issued: new Date().toISOString(),
        expires: "Never"
    }));
    // Mock signature
    const mockSig = btoa("ED25519_SIG_" + Math.random().toString(36).substring(2) + "_VERIFIED_BY_OPTICLEANER_CA");
    const token = `${payload}.${mockSig}`;

    document.getElementById("tokenResult").value = token;
}

function copyToken() {
    const box = document.getElementById("tokenResult");
    box.select();
    navigator.clipboard.writeText(box.value);
    alert("License token copied to clipboard! Paste it inside the OptiCleaner desktop app.");
}
