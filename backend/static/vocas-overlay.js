(function() {
    console.log("Vocas Overlay Initializing...");

    // --- UI Setup ---
    const overlay = document.createElement('div');
    overlay.id = 'vocas-overlay';
    
    const homeBtn = document.createElement('button');
    homeBtn.className = 'vocas-btn vocas-btn-home';
    homeBtn.innerHTML = '🏠 Domů';
    homeBtn.onclick = () => window.location.href = window.location.origin;
    
    const readBtn = document.createElement('button');
    readBtn.className = 'vocas-btn vocas-btn-read';
    readBtn.innerHTML = '▶ Přečíst';
    
    const summaryBtn = document.createElement('button');
    summaryBtn.className = 'vocas-btn vocas-btn-summary';
    summaryBtn.innerHTML = '📝 Shrnout';

    const stopBtn = document.createElement('button');
    stopBtn.className = 'vocas-btn vocas-btn-stop';
    stopBtn.innerHTML = '⏹ Stop';
    
    const statusEl = document.createElement('div');
    statusEl.id = 'vocas-status';
    
    overlay.appendChild(homeBtn);
    overlay.appendChild(readBtn);
    overlay.appendChild(summaryBtn);
    overlay.appendChild(stopBtn);
    overlay.appendChild(statusEl);
    document.body.appendChild(overlay);

    let audioPlayer = new Audio();

    // --- Link Interception ---
    document.addEventListener('click', function(e) {
        let target = e.target.closest('a');
        if (target && target.href) {
            // Ignore non-http links (mailto, tel, javascript)
            if (!target.href.startsWith('http')) return;

            e.preventDefault();
            
            try {
                // Check if it's already a proxied URL
                const url = new URL(target.href);
                
                // If we are already on the proxy origin, check path
                if (url.origin === window.location.origin && url.pathname.startsWith('/read/')) {
                     window.location.href = target.href;
                     return;
                }
                
                // Otherwise, wrap it
                // Use window.location.origin to ensure we stay on the proxy domain (ignoring <base>)
                window.location.href = window.location.origin + '/read/' + target.href;
            } catch (err) {
                console.error("Vocas: Invalid URL click", err);
                // Fallback: let browser handle it (might break if base tag issues, but better than crash)
                window.location.href = target.href;
            }
        }
    });

    // --- Content Extraction & Processing ---

    function showStatus(msg, timeout=3000) {
        statusEl.textContent = msg;
        statusEl.style.display = 'block';
        if (timeout) setTimeout(() => statusEl.style.display = 'none', timeout);
    }

    async function processPage(mode) {
        showStatus(mode === 'read' ? 'Zpracovávám text...' : 'Vytvářím souhrn...', 0);
        
        // Use Readability to find content
        // We clone the document because Readability mutates the DOM
        const documentClone = document.cloneNode(true); 
        // We need to verify if Readability is loaded
        if (typeof Readability === 'undefined') {
            showStatus("Chyba: Readability library not loaded!");
            return;
        }

        const reader = new Readability(documentClone);
        const article = reader.parse();

        if (!article || !article.textContent) {
            showStatus("Nepodařilo se najít hlavní obsah článku.");
            return;
        }

        const textContent = article.textContent;
        console.log("Extracted text length:", textContent.length);

        try {
            // ROBUST URL STRATEGY: Use window.location.origin
            // This always points to the proxy server (e.g. http://localhost:5000)
            // ignoring the <base> tag which points to the target site.
            const apiOrigin = window.location.origin;
            const apiUrl = apiOrigin + '/api/process';
            
            console.log("Vocas calling API:", apiUrl);
            
            const response = await fetch(apiUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    text: textContent,
                    mode: mode
                })
            });

            if (!response.ok) throw new Error('API Error: ' + response.status);

            const data = await response.json();
            
            showStatus('Přehrávám audio...');
            
            // Ensure audio URL is absolute
            let audioUrl = data.audio_url;
            if (audioUrl.startsWith('/')) {
                audioUrl = apiOrigin + audioUrl;
            }
            
            audioPlayer.src = audioUrl;
            audioPlayer.play();

        } catch (e) {
            console.error(e);
            showStatus('Chyba: ' + e.message);
        }
    }

    readBtn.onclick = () => processPage('read');
    summaryBtn.onclick = () => processPage('summarize');
    stopBtn.onclick = () => {
        audioPlayer.pause();
        audioPlayer.currentTime = 0;
        showStatus('Přehrávání zastaveno');
    };

})();
