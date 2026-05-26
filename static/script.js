// =========================
// DARK MODE TOGGLE
// =========================

document.addEventListener("DOMContentLoaded", () => {

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