document.addEventListener('DOMContentLoaded', async () => {
    const statusMessage = document.getElementById('statusMessage');
    
    try {
        const tabs = await chrome.tabs.query({active: true, currentWindow: true});
        
        if (!tabs[0] || !tabs[0].url) {
            throw new Error('No active tab found');
        }

        const response = await fetch('http://localhost:5000/save', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                url: tabs[0].url
            })
        });

        const result = await response.json();
        
        statusMessage.textContent = result.message;
        statusMessage.className = 'message success';

        // Close popup after brief delay
        setTimeout(() => window.close(), 1000);

    } catch (error) {
        statusMessage.textContent = 'Error: ' + error.message;
        statusMessage.className = 'message error';
        
        // Close popup after brief delay
        setTimeout(() => window.close(), 1500);
    }
}); 