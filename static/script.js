// Valcore Dashboard

const form = document.querySelector("form");
const button = document.getElementById("analyzeBtn");
const fileInput = document.getElementById("fileInput");

// Upload animation
if (form && button) {

    form.addEventListener("submit", () => {

        button.disabled = true;

        const steps = [
            "Initializing...",
            "Reading CSV...",
            "Encoding Features...",
            "Running Random Forest...",
            "Generating Report..."
        ];

        let i = 0;

        button.innerText = steps[0];

        const timer = setInterval(() => {

            i++;

            if (i < steps.length) {
                button.innerText = steps[i];
            } else {
                clearInterval(timer);
            }

        }, 350);

    });

}

// Show selected filename
if (fileInput) {

    fileInput.addEventListener("change", function () {

        const old = document.querySelector(".filename");

        if (old) old.remove();

        if (this.files.length > 0) {

            const div = document.createElement("div");

            div.className = "filename";

            div.textContent = "Selected: " + this.files[0].name;

            this.parentElement.insertBefore(div, button);

        }

    });

}

// Fade cards
document.querySelectorAll(".card, .small-card").forEach((card, i) => {

    card.style.opacity = "0";
    card.style.transform = "translateY(12px)";

    setTimeout(() => {

        card.style.transition = "all .45s ease";
        card.style.opacity = "1";
        card.style.transform = "translateY(0px)";

    }, i * 120);

});

// Doughnut Chart
const canvas = document.getElementById("trafficChart");

if (canvas && typeof Chart !== "undefined") {

    new Chart(canvas, {

        type: "doughnut",

        data: {

            labels: ["Attack", "Normal"],

            datasets: [{

                data: [
                    window.attackPackets || 0,
                    window.normalPackets || 0
                ],

                backgroundColor: [
                    "#FF5C5C",
                    "#69F38C"
                ],

                borderWidth: 0,
                hoverOffset: 12

            }]

        },

        options: {

            responsive: true,

            maintainAspectRatio: false,

            cutout: "72%",

            plugins: {

                legend: {

                    position: "bottom",

                    labels: {

                        color: "#F5F5F5",

                        font: {

                            family: "IBM Plex Mono",
                            size: 12

                        }

                    }

                }

            }

        }

    });

}

// Online status pulse
const dot = document.querySelector(".dot");

if (dot) {

    setInterval(() => {

        dot.style.opacity = ".5";

        setTimeout(() => {

            dot.style.opacity = "1";

        }, 450);

    }, 1500);

}

const input = document.getElementById("fileInput");
const filename = document.getElementById("filename");

if (input && filename) {
    input.addEventListener("change", () => {
        if (input.files.length > 0) {
            filename.textContent = "✓ " + input.files[0].name;
        } else {
            filename.textContent = "No file selected";
        }
    });
}