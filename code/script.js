let failedNodes = 0;
let currentFilename = null;

const API = "";


// ============================================================
// ACTIVITY LOG
// ============================================================

function addActivity(title, message, type = "success") {

    const activity = document.getElementById("activity");

    activity.innerHTML = `
        <div class="event ${type}">
            <span>${type === "warning" ? "⚠" : "✓"}</span>
            <div>
                <b>${title}</b>
                <small>${message}</small>
            </div>
        </div>
    ` + activity.innerHTML;
}


// ============================================================
// FAIL NODE
// ============================================================

async function failNode(number) {

    const nodeName = "node" + number;

    try {

        const response = await fetch(
            `${API}/fail/${nodeName}`,
            {
                method: "POST"
            }
        );

        const data = await response.json();

        if (data.error) {
            alert(data.error);
            return;
        }

        const node = document.getElementById("node" + number);

        if (node) {
            node.style.borderColor = "#ff4d4d";

            const badge = node.querySelector(".badge");

            if (badge) {
                badge.innerText = "FAILED";
                badge.className = "badge offline";
            }
        }

        failedNodes++;

        addActivity(
            `Node ${number} failure detected`,
            "Vault is checking replica availability...",
            "warning"
        );

        document.getElementById("aiMessage").innerHTML = `
            <b>⚠ Node ${number} has failed</b>
            <p>Vault detected the node failure. Data remains available from healthy replicas.</p>
        `;

    } catch (error) {

        alert("Could not connect to Vault backend.");
        console.error(error);
    }
}


// ============================================================
// REPAIR
// ============================================================

async function repair() {

    if (!currentFilename) {
        alert("Upload a file first.");
        return;
    }

    try {

        const response = await fetch(
            `${API}/repair/${encodeURIComponent(currentFilename)}`,
            {
                method: "POST"
            }
        );

        const data = await response.json();

        if (data.error) {
            alert(data.error);
            return;
        }

        // Reset failed node cards
        for (let i = 1; i <= 4; i++) {

            const node = document.getElementById("node" + i);

            if (!node) continue;

            node.style.borderColor = "";

            const badge = node.querySelector(".badge");

            if (badge) {
                badge.innerText = "HEALTHY";
                badge.className = "badge";
            }
        }

        // Highlight Node 4 as the repaired replica
        const node4 = document.getElementById("node4");

        if (node4) {
            node4.style.borderColor = "#00ff99";

            const badge = node4.querySelector(".badge");

            if (badge) {
                badge.innerText = "REPAIRED";
                badge.className = "badge";
            }
            const circle = node4.querySelector(".circle");

if (circle) {
    circle.innerText = "100%";
}

const label = node4.querySelector("p");

if (label) {
    label.innerText = "Replica Restored";
}

const button = node4.querySelector("button");

if (button) {
    button.innerText = "Replica Healthy";
    button.disabled = false;
}
        }

        addActivity(
            "Replica repair completed",
            `Replica restored on ${data.new_replica}. Integrity verified.`,
            "success"
        );

        document.getElementById("aiMessage").innerHTML = `
            <b>✓ Recovery completed</b>
            <p>Vault restored the missing replica on Node 4 and verified its integrity.</p>
        `;

        failedNodes = 0;

    } catch (error) {

        alert("Could not connect to Vault backend.");
        console.error(error);
    }
}

// ============================================================
// UPLOAD FILE
// ============================================================

async function uploadFile() {

    const input = document.createElement("input");

    input.type = "file";

    input.onchange = async function () {

        const file = input.files[0];

        if (!file) {
            return;
        }

        const formData = new FormData();

        formData.append("file", file);

        try {

            const response = await fetch(
                `${API}/upload`,
                {
                    method: "POST",
                    body: formData
                }
            );

            const data = await response.json();

            if (data.error) {

                alert(data.error);

                return;
            }

            currentFilename = data.filename;

            const count = document.getElementById("objectCount");

            if (count) {
                count.innerText =
                    parseInt(count.innerText || "0") + 1;
            }

            addActivity(
                "Object uploaded",
                `${data.filename} replicated across ${data.replicas.length} storage nodes.`,
                "success"
            );

            document.getElementById("aiMessage").innerHTML = `
                <b>✓ Object stored successfully</b>
                <p>${data.filename} has been replicated across Node 1, Node 2 and Node 3.</p>
            `;

            alert(
                "Upload successful!\n\n" +
                "File: " + data.filename +
                "\nReplicas: " + data.replicas.join(", ")
            );

        } catch (error) {

            alert(
                "Could not connect to Vault backend.\n\n" +
                "Make sure FastAPI is running."
            );

            console.error(error);
        }
    };

    input.click();
}


// ============================================================
// CORRUPTION SIMULATION
// ============================================================

async function corruptReplica() {

    if (!currentFilename) {

        alert("Upload a file first.");

        return;
    }

    try {

        const response = await fetch(
            `${API}/corrupt/node1/${encodeURIComponent(currentFilename)}`,
            {
                method: "POST"
            }
        );

        const data = await response.json();

        if (data.error) {

            // Backend corruption endpoint may not exist.
            // We still show the demo state.
            showCorruptionDemo();

            return;
        }

        addActivity(
            "Replica corruption detected",
            "Checksum mismatch found on Node 1.",
            "warning"
        );

        document.getElementById("aiMessage").innerHTML = `
            <b>⚠ Data integrity violation</b>
            <p>Node 1 contains a corrupted replica. Vault recommends replacing it using a verified healthy replica.</p>
        `;

    } catch (error) {

        // Keep the UI demo working even if corruption endpoint
        // is unavailable.
        showCorruptionDemo();
    }
}


// ============================================================
// VISUAL CORRUPTION DEMO
// ============================================================

function showCorruptionDemo() {

    addActivity(
        "Replica corruption detected",
        "Checksum mismatch found on a storage replica.",
        "warning"
    );

    document.getElementById("aiMessage").innerHTML = `
        <b>⚠ Data integrity violation</b>
        <p>A corrupted replica was detected. Vault recommends replacing it using a verified healthy replica.</p>
    `;
}