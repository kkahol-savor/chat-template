// Generate a session ID and store it in session storage if not already present
if (!sessionStorage.getItem('sessionID')) {
    sessionStorage.setItem('sessionID', crypto.randomUUID());
}
const sessionID = sessionStorage.getItem('sessionID');

const form = document.getElementById('input-container');
const chatBox = document.getElementById('chat-box');

form.addEventListener('submit', (event) => {
    event.preventDefault();
    const searchQuery = document.getElementById('search_query').value;
    const topNDocuments = document.getElementById('topNDocuments').value;

    // Add user query to chat box
    chatBox.innerHTML += `<div><strong>You:</strong> ${searchQuery}</div>`;
    const botMessage = document.createElement('div');
    botMessage.innerHTML = `<strong>Bot:</strong> `;
    chatBox.appendChild(botMessage);

    // Open SSE connection
    const eventSource = new EventSource(`/stream?search_query=${encodeURIComponent(searchQuery)}&topNDocuments=${topNDocuments}&sessionID=${sessionID}`);

    // Buffer for assembling chunks
    let responseBuffer = "";
    let citationsBuffer = "";

    eventSource.onmessage = function(event) {
        console.log("raw event data", event.data);
        const data = JSON.parse(event.data);
        console.log(data);

        if (data.type === 'response') {
            // Append chunk to the buffer
            responseBuffer += data.data;

            // Process and render Markdown
            const renderedMarkdown = marked.parse(responseBuffer);
            botMessage.innerHTML = `<strong>Agent:</strong> ${renderedMarkdown}`;
        } else if (data.type === 'citations' || data.type === 'citation') {
            // Append citation to the buffer
            citationsBuffer += `<div class="citation">${marked.parse(data.data)}</div>`;
        }

        // Scroll to the latest message
        chatBox.scrollTop = chatBox.scrollHeight;
    };

    eventSource.onerror = function() {
        // Close the connection and reset the buffer
        eventSource.close();

        // Append citations to the bot message
        if (citationsBuffer) {
            botMessage.innerHTML += `<div class="citation-title"><strong>References:</strong></div>${citationsBuffer}`;
        }
    };

    form.reset();
});

// Replace the upload button logic
document.getElementById("uploadButton").addEventListener("click", () => {
    // Display the drag-and-drop modal instead of opening a Python script
    uploadModal.style.display = "block";
});

document.getElementById("fileInput").addEventListener("change", async (event) => {
    const files = event.target.files;

    if (files.length === 0) {
        alert("Please select a file to upload.");
        return;
    }

    const formData = new FormData();
    for (const file of files) {
        formData.append("file", file);
    }

    try {
        const response = await fetch("/upload", {
            method: "POST",
            body: formData,
        });

        if (response.ok) {
            const result = await response.json();
            alert(`File(s) uploaded successfully: ${result.filename}`);
        } else {
            const error = await response.json();
            alert(`Error: ${error.detail}`);
        }
    } catch (err) {
        console.error("Error uploading file:", err);
        alert("An error occurred while uploading the file.");
    }
});

const uploadModal = document.getElementById("uploadModal");
const closeModal = document.getElementById("closeModal");
const dropZone = document.getElementById("dropZone");
const modalFileInput = document.getElementById("modalFileInput");
const selectFilesButton = document.getElementById("selectFilesButton");
const indexingModal = document.getElementById("indexingModal");

// Show the modal when "Upload" is clicked
document.getElementById("uploadButton").addEventListener("click", () => {
    uploadModal.style.display = "block";
});

// Close the modal
closeModal.addEventListener("click", () => {
    uploadModal.style.display = "none";
});

// Allow file selection via button
selectFilesButton.addEventListener("click", () => {
    modalFileInput.click();
});

// Handle drag-and-drop functionality
dropZone.addEventListener("dragover", (event) => {
    event.preventDefault();
    dropZone.classList.add("drag-over");
});

dropZone.addEventListener("dragleave", () => {
    dropZone.classList.remove("drag-over");
});

dropZone.addEventListener("drop", async (event) => {
    event.preventDefault();
    dropZone.classList.remove("drag-over");
    const files = event.dataTransfer.files;
    await handleFileUpload(files);
});

// Handle file selection via input
modalFileInput.addEventListener("change", async (event) => {
    const files = event.target.files;
    await handleFileUpload(files);
});

// Function to handle file uploads
async function handleFileUpload(files) {
    const allowedExtensions = [".pdf", ".json", ".csv", ".xlsx", ".xls", ".docx", ".doc"];
    const formData = new FormData();

    for (const file of files) {
        const fileExtension = file.name.split('.').pop().toLowerCase();
        if (!allowedExtensions.includes(`.${fileExtension}`)) {
            alert(`File type not allowed: ${file.name}`);
            continue;
        }
        formData.append("file", file);
    }

    try {
        // Show the indexing modal
        indexingModal.style.display = "block";

        const response = await fetch("/upload", {
            method: "POST",
            body: formData,
        });

        if (response.ok) {
            const result = await response.json();
            alert(`File(s) uploaded and indexed successfully: ${result.filename}`);
        } else {
            const error = await response.json();
            alert(`Error: ${error.detail}`);
        }
    } catch (err) {
        console.error("Error uploading file:", err);
        alert("An error occurred while uploading the file.");
    } finally {
        // Hide the indexing modal
        indexingModal.style.display = "none";
    }

    // Close the modal after upload
    uploadModal.style.display = "none";
}