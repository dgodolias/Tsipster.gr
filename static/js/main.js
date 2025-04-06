document.addEventListener('DOMContentLoaded', function() {
    const betForm = document.getElementById('betForm');
    const betList = document.getElementById('betList');
    const totalOddsElement = document.getElementById('totalOdds');
    const generateBtn = document.getElementById('generateBtn');
    const acceptAllBtn = document.getElementById('acceptAllBtn');
    const rejectSelectedBtn = document.getElementById('rejectSelectedBtn');
    const selectAllCheckbox = document.getElementById('selectAll');
    const statusLog = document.getElementById('statusLog');
    
    let currentBets = [];
    
    function updateStatusLog(message) {
        const timestamp = new Date().toLocaleTimeString();
        statusLog.innerHTML += `<p><small>${timestamp}</small>: ${message}</p>`;
        statusLog.scrollTop = statusLog.scrollHeight;
    }
    
    betForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const numBets = parseInt(document.getElementById('numBets').value);
        const minOdds = parseFloat(document.getElementById('minOdds').value);
        const maxOdds = parseFloat(document.getElementById('maxOdds').value);
        const uniqueMatchOnly = document.getElementById('uniqueMatchOnly').checked;
        
        updateStatusLog("Generating bets...");
        generateBtn.disabled = true;
        
        fetch('/api/generate-bets', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                numBets: numBets,
                minOdds: minOdds,
                maxOdds: maxOdds,
                uniqueMatchOnly: uniqueMatchOnly
            }),
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
            
            currentBets = data.bets;
            renderBets();
            totalOddsElement.textContent = data.totalOdds.toFixed(2);
            generateBtn.disabled = false;
            acceptAllBtn.disabled = currentBets.length === 0;
            rejectSelectedBtn.disabled = true;
            updateStatusLog(`Generated ${data.bets.length} bets with total odds of ${data.totalOdds.toFixed(2)}`);
        })
        .catch(error => {
            console.error('Error:', error);
            updateStatusLog(`Error generating bets: ${error.message}`);
            generateBtn.disabled = false;
        });
    });
    
    function renderBets() {
        betList.innerHTML = '';
        
        if (currentBets.length === 0) {
            betList.innerHTML = '<tr><td colspan="5" class="text-center">No bets generated yet</td></tr>';
            return;
        }
        
        currentBets.forEach((bet, index) => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td><input type="checkbox" class="bet-checkbox" data-index="${index}"></td>
                <td>${bet.match}</td>
                <td>${bet.market}</td>
                <td>${bet.outcome}</td>
                <td>${bet.odds.toFixed(2)}</td>
            `;
            betList.appendChild(row);
        });
        
        // Add event listeners to checkboxes
        document.querySelectorAll('.bet-checkbox').forEach(checkbox => {
            checkbox.addEventListener('change', updateButtonStates);
        });
    }
    
    function updateButtonStates() {
        const hasCheckedItems = document.querySelectorAll('.bet-checkbox:checked').length > 0;
        rejectSelectedBtn.disabled = !hasCheckedItems;
    }
    
    selectAllCheckbox.addEventListener('change', function() {
        document.querySelectorAll('.bet-checkbox').forEach(checkbox => {
            checkbox.checked = this.checked;
        });
        updateButtonStates();
    });
    
    acceptAllBtn.addEventListener('click', function() {
        if (currentBets.length === 0) {
            updateStatusLog("No bets to accept");
            return;
        }
        
        updateStatusLog("Accepting all bets...");
        acceptAllBtn.disabled = true;
        
        fetch('/accept_bets', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                accept_all: true
            }),
        })
        .then(response => response.json())
        .then(data => {
            updateStatusLog(data.message || "All bets accepted!");
            acceptAllBtn.disabled = false;
        })
        .catch(error => {
            console.error('Error:', error);
            updateStatusLog("Error accepting bets");
            acceptAllBtn.disabled = false;
        });
    });
    
    rejectSelectedBtn.addEventListener('click', function() {
        const selectedIndices = [];
        document.querySelectorAll('.bet-checkbox:checked').forEach(checkbox => {
            selectedIndices.push(parseInt(checkbox.getAttribute('data-index')));
        });
        
        if (selectedIndices.length === 0) {
            updateStatusLog("No bets selected for rejection");
            return;
        }
        
        updateStatusLog(`Rejecting ${selectedIndices.length} bets...`);
        rejectSelectedBtn.disabled = true;
        
        fetch('/reject_bets', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                reject_indices: selectedIndices
            }),
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
            
            updateStatusLog(data.message || "Selected bets rejected");
            
            if (data.updated_bets) {
                currentBets = data.updated_bets;
                renderBets();
                totalOddsElement.textContent = data.total_odds.toFixed(2);
            }
            
            selectAllCheckbox.checked = false;
            rejectSelectedBtn.disabled = true;
            acceptAllBtn.disabled = currentBets.length === 0;
            
            // Ask to replace rejected bets
            if (confirm("Would you like to get replacement bets?")) {
                getReplacementBets(selectedIndices.length);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            updateStatusLog(`Error rejecting bets: ${error.message}`);
            rejectSelectedBtn.disabled = false;
        });
    });
    
    function getReplacementBets(numNeeded) {
        if (numNeeded <= 0) return;
        
        updateStatusLog(`Getting ${numNeeded} replacement bets...`);
        
        const minOdds = parseFloat(document.getElementById('minOdds').value);
        const maxOdds = parseFloat(document.getElementById('maxOdds').value);
        const uniqueMatchOnly = document.getElementById('uniqueMatchOnly').checked;
        
        fetch('/get_replacement_bets', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                num_needed: numNeeded,
                min_odds: minOdds,
                max_odds: maxOdds,
                unique_match_only: uniqueMatchOnly
            }),
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
            
            if (data.all_bets) {
                currentBets = data.all_bets;
                renderBets();
                totalOddsElement.textContent = data.total_odds.toFixed(2);
                updateStatusLog(`Added ${data.new_bets.length} replacement bets`);
            } else {
                updateStatusLog("No replacement bets found");
            }
            
            acceptAllBtn.disabled = currentBets.length === 0;
        })
        .catch(error => {
            console.error('Error:', error);
            updateStatusLog(`Error getting replacement bets: ${error.message}`);
        });
    }
    
    // Initialize the page
    renderBets();

    // Add copyright year update
    document.querySelector('footer p').textContent = '© 2025 Tsipster - The Smart Bet Suggestor';
});
