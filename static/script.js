// =========================
// DARK MODE TOGGLE
// =========================

document.addEventListener("DOMContentLoaded", () => {

    // INJECT MISSING LIGHT MODE CSS GLOBALLY
    const style = document.createElement('style');
    style.innerHTML = `
        body.light-mode { background: linear-gradient(-45deg, #f8fafc, #e2e8f0, #e0e7ff, #f1f5f9) !important; background-size: 400% 400% !important; color: #0f172a !important; }
        body.light-mode .sidebar { background-color: #ffffff !important; border-right: 1px solid #e2e8f0 !important; }
        body.light-mode .sidebar a { color: #475569 !important; }
        body.light-mode .sidebar a.active-link, body.light-mode .sidebar a:hover { background-color: #f8fafc !important; color: #0f172a !important; }
        body.light-mode .main-content, body.light-mode .dashboard, body.light-mode .upload-page, body.light-mode .search-page { background-color: #f1f5f9 !important; }
        body.light-mode .card, body.light-mode .storage-card, body.light-mode .table-section, body.light-mode .upload-card, body.light-mode .search-card, body.light-mode .info-card { background-color: rgba(255, 255, 255, 0.8) !important; backdrop-filter: blur(20px) !important; border: 1px solid #e2e8f0 !important; box-shadow: 0 10px 30px rgba(0,0,0,0.05) !important; }
        body.light-mode h1, body.light-mode h2, body.light-mode h3, body.light-mode h4, body.light-mode .topbar h2, body.light-mode .topbar h3 { color: #0f172a !important; }
        body.light-mode p, body.light-mode span:not(.slider):not(.badge) { color: #475569 !important; }
        body.light-mode table th { background-color: #f8fafc !important; color: #0f172a !important; border-bottom: 2px solid #e2e8f0 !important; }
        body.light-mode table td { color: #475569 !important; border-bottom: 1px solid #e2e8f0 !important; }
        body.light-mode input[type="text"], body.light-mode input[type="password"], body.light-mode input[type="email"] { background-color: #ffffff !important; color: #0f172a !important; border: 1px solid #cbd5e1 !important; transition: 0.3s; }
        body.light-mode input[type="text"]:focus, body.light-mode input[type="password"]:focus, body.light-mode input[type="email"]:focus { border-color: #7c3aed !important; box-shadow: 0 0 20px rgba(124, 58, 237, 0.15) !important; transform: translateY(-2px); }
        body.light-mode .empty-state, body.light-mode .empty-search { background-color: #f8fafc !important; color: #64748b !important; border: 1px dashed #cbd5e1 !important; }
        body.light-mode .profile-box { background-color: #e2e8f0 !important; color: #0f172a !important; border: 1px solid #cbd5e1 !important; }
        body.light-mode .auth-container { background-color: rgba(255, 255, 255, 0.9) !important; backdrop-filter: blur(20px) !important; border: 1px solid rgba(255, 255, 255, 0.5) !important; box-shadow: 0 20px 40px rgba(0,0,0,0.1) !important; }
        body.light-mode .background-blur { background: transparent !important; background-image: radial-gradient(rgba(0, 0, 0, 0.05) 1px, transparent 1px) !important; background-size: 30px 30px !important; }
        body.light-mode .background-blur::before { background: radial-gradient(circle, rgba(139, 92, 246, 0.2), transparent 70%) !important; }
        body.light-mode .background-blur::after { background: radial-gradient(circle, rgba(59, 130, 246, 0.2), transparent 70%) !important; }
        body.light-mode .logo { color: #0f172a !important; }
        body.light-mode .drop-area { background: #f8fafc !important; border-color: #93c5fd !important; }
        body.light-mode .card:hover, body.light-mode .upload-card:hover, body.light-mode .search-card:hover { transform: translateY(-8px) scale(1.02) !important; box-shadow: 0 15px 40px rgba(124, 58, 237, 0.15), inset 0 0 0 1px rgba(124, 58, 237, 0.2) !important; border-color: rgba(124, 58, 237, 0.2) !important; }
    `;
    document.head.appendChild(style);

    // ISOLATE AND ENHANCE CLOUD ICON GLOBALLY
    const cloudElements = document.querySelectorAll('.sidebar h1, .logo');
    cloudElements.forEach(el => {
        if (el.innerHTML.includes('☁')) {
            el.innerHTML = el.innerHTML.replace('☁', '<span class="cloud-icon"></span>');
        }
    });

    const darkToggle =
        document.getElementById("darkModeToggle");

    // LOAD SAVED MODE

    if(localStorage.getItem("theme") === "light"){

        document.body.classList.add("light-mode");

        if(darkToggle){

            darkToggle.checked = false;

        }

    }

    else{

        if(darkToggle){

            darkToggle.checked = true;

        }

    }

    // TOGGLE MODE

    if(darkToggle){

        darkToggle.addEventListener("change", () => {

            if(darkToggle.checked){

                document.body.classList.remove(
                    "light-mode"
                )

                localStorage.setItem(
                    "theme",
                    "dark"
                )

            }

            else{

                document.body.classList.add(
                    "light-mode"
                )

                localStorage.setItem(
                    "theme",
                    "light"
                )

            }

        })

    }

})