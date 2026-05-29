// =========================
// DARK MODE TOGGLE
// =========================

document.addEventListener("DOMContentLoaded", () => {

    // INJECT MISSING LIGHT MODE CSS GLOBALLY
    const style = document.createElement('style');
    style.innerHTML = `
        body.light-mode { background-color: #f1f5f9 !important; color: #0f172a !important; }
        body.light-mode .sidebar { background-color: #ffffff !important; border-right: 1px solid #e2e8f0 !important; }
        body.light-mode .sidebar a { color: #475569 !important; }
        body.light-mode .sidebar a.active-link, body.light-mode .sidebar a:hover { background-color: #f8fafc !important; color: #0f172a !important; }
        body.light-mode .main-content, body.light-mode .dashboard, body.light-mode .upload-page, body.light-mode .search-page { background-color: #f1f5f9 !important; }
        body.light-mode .card, body.light-mode .storage-card, body.light-mode .table-section, body.light-mode .upload-card, body.light-mode .search-card, body.light-mode .info-card { background-color: #ffffff !important; border: 1px solid #e2e8f0 !important; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05) !important; }
        body.light-mode h1, body.light-mode h2, body.light-mode h3, body.light-mode h4, body.light-mode .topbar h2, body.light-mode .topbar h3 { color: #0f172a !important; }
        body.light-mode p, body.light-mode span:not(.slider):not(.badge) { color: #475569 !important; }
        body.light-mode table th { background-color: #f8fafc !important; color: #0f172a !important; border-bottom: 2px solid #e2e8f0 !important; }
        body.light-mode table td { color: #475569 !important; border-bottom: 1px solid #e2e8f0 !important; }
        body.light-mode input[type="text"], body.light-mode input[type="password"], body.light-mode input[type="email"] { background-color: #ffffff !important; color: #0f172a !important; border: 1px solid #cbd5e1 !important; }
        body.light-mode .empty-state, body.light-mode .empty-search { background-color: #f8fafc !important; color: #64748b !important; border: 1px dashed #cbd5e1 !important; }
        body.light-mode .profile-box { background-color: #e2e8f0 !important; color: #0f172a !important; border: 1px solid #cbd5e1 !important; }
        body.light-mode .auth-container { background-color: #ffffff !important; border: 1px solid #e2e8f0 !important; box-shadow: 0 10px 25px rgba(0,0,0,0.1) !important; }
        body.light-mode .background-blur { background: #f1f5f9 !important; }
        body.light-mode .logo { color: #0f172a !important; }
        body.light-mode .drop-area { background: #f8fafc !important; border-color: #93c5fd !important; }
    `;
    document.head.appendChild(style);

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