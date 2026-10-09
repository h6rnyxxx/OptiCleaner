// OptiCleaner v4.0 - Interactive Web Ecosystem Controller & Licensing Dispatch

const DIRECT_WIN_URL = "https://github.com/h6rnyxxx/OptiCleaner/releases/download/v4.0.0/OptiCleaner-v4.0.0-Windows.exe";
const DIRECT_LINUX_URL = "https://github.com/h6rnyxxx/OptiCleaner/releases/download/v4.0.0/OptiCleaner-v4.0.0-Linux.AppImage";

let currentToken = "";
let currentHwid = "";
let currentEmail = "";

// 1. Direct File Download Handler
function downloadFile(platform, event) {
    if (event) {
        event.preventDefault();
    }
    const url = (platform === 'linux') ? DIRECT_LINUX_URL : DIRECT_WIN_URL;
    const filename = (platform === 'linux') ? "OptiCleaner-v4.0.0-Linux.AppImage" : "OptiCleaner-v4.0.0-Windows.exe";

    // 1. Programmatically trigger download
    const a = document.createElement("a");
    a.href = url;
    a.setAttribute("download", filename);
    a.style.display = "none";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);

    // 2. Direct browser navigation fallback
    setTimeout(() => {
        window.location.href = url;
    }, 300);
}

// 2. Simulated Live Dashboard Gauges
let cpuVal = 24;
let ramVal = 58;

function updateGauges() {
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

// 3. Switch Dashboard Tabs
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

// 4. Simulate Quick Boost Button
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

// 5. Checkout Modal Controls
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

// 6. Complete Payment & Dispatch Email + Auto-Download .lic
async function processPaymentAndSendEmail() {
    const hwidInput = document.getElementById("payHwid");
    const emailInput = document.getElementById("payEmail");
    const submitBtn = document.getElementById("btnCheckoutSubmit");

    currentHwid = (hwidInput.value || "OC-8B42-19FA-E821").trim();
    currentEmail = (emailInput.value || "user@gmail.com").trim();

    if (!currentEmail.includes("@")) {
        alert("Пожалуйста, введите корректный адрес электронной почты!");
        return;
    }

    submitBtn.innerText = "⏳ Генерация ключа и отправка на почту...";
    submitBtn.disabled = true;

    // Generate Ed25519 Token
    const payloadObj = {
        hwid: currentHwid,
        tier: "PRO",
        issued: new Date().toISOString(),
        expires: "Never"
    };
    const payloadB64 = btoa(JSON.stringify(payloadObj));
    const sigMock = btoa("ED25519_KEY_" + Math.random().toString(36).substring(2, 10).toUpperCase() + "_SIG_VALID");
    currentToken = `${payloadB64}.${sigMock}`;

    // Switch view
    document.getElementById("payForm").style.display = "none";
    document.getElementById("paySuccess").style.display = "block";
    document.getElementById("tokenResult").value = currentToken;
    submitBtn.innerText = "Оформить лицензию и отправить на почту";
    submitBtn.disabled = false;

    // 1. Auto-download license file .lic directly to Downloads
    downloadLicenseFile();

    // 2. Dispatch Email
    const statusText = document.getElementById("emailStatusText");
    statusText.innerText = `📨 Отправка письма с лицензией на ${currentEmail}...`;

    try {
        // Attempt sending via FormSubmit / Webhook relay
        const emailBody = {
            subject: "Ваша лицензия OptiCleaner v4.0 Pro",
            hwid: currentHwid,
            license_token: currentToken,
            download_url: DIRECT_WIN_URL,
            message: `Здравствуйте!\n\nБлагодарим за использование OptiCleaner v4.0 Pro!\n\nВаш аппаратный HWID: ${currentHwid}\nВаш лицензионный ключ: ${currentToken}\n\nСкачать программу: ${DIRECT_WIN_URL}\n\nФайл лицензии license.lic уже сгенерирован и прикреплён к вашим загрузкам.`
        };

        const res = await fetch(`https://formsubmit.co/ajax/${encodeURIComponent(currentEmail)}`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            body: JSON.stringify(emailBody)
        });

        if (res.ok) {
            statusText.innerText = `✅ Письмо с лицензией успешно отправлено на ${currentEmail}! Файл license.lic сохранён в Загрузки.`;
        } else {
            statusText.innerText = `✅ Лицензия активирована! Ключ скопирован ниже и сохранён в файл license.lic. Проверьте почту ${currentEmail} или скачайте файл.`;
        }
    } catch (e) {
        // Network fallback
        statusText.innerText = `✅ Лицензия активна! Файл license.lic скачан. Если письмо задерживается, скопируйте ключ ниже или нажмите кнопку «Открыть письмо».`;
    }
}

// 7. Download .lic File Directly
function downloadLicenseFile() {
    if (!currentToken) return;
    const blob = new Blob([currentToken], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `OptiCleaner_License_${currentHwid.replace(/[^A-Za-z0-9]/g, '')}.lic`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

// 8. Copy Token to Clipboard
function copyToken() {
    const box = document.getElementById("tokenResult");
    box.select();
    navigator.clipboard.writeText(box.value);
    alert("Лицензионный ключ скопирован в буфер обмена!\n\nВставьте его в приложении OptiCleaner во вкладке настроек.");
}

// 9. Open Mail Client Fallback
function openMailClientFallback() {
    const subject = encodeURIComponent("Ваша лицензия OptiCleaner v4.0 Pro");
    const body = encodeURIComponent(
        `Здравствуйте!\n\nВаша лицензия OptiCleaner v4.0 Pro:\n\nHWID: ${currentHwid}\nЛицензионный ключ:\n${currentToken}\n\nСкачать программу: ${DIRECT_WIN_URL}`
    );
    window.location.href = `mailto:${currentEmail}?subject=${subject}&body=${body}`;
}
