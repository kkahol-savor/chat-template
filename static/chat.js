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