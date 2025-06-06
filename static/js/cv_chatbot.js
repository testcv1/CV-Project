document.addEventListener('DOMContentLoaded', function() {
    const chatMessages = document.getElementById('chatbot-messages');
    const fileUpload = document.getElementById('cv-upload');
    const fileInfo = document.getElementById('file-info');

    // Add message to chat
    function addMessage(sender, text, isAnalysis = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        if (isAnalysis) {
            contentDiv.innerHTML = formatAnalysis(text);
        } else {
            contentDiv.innerHTML = `<p>${text}</p>`;
        }
        
        // Add timestamp
        const timeDiv = document.createElement('div');
        timeDiv.className = 'message-time';
        timeDiv.textContent = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        
        contentDiv.appendChild(timeDiv);
        messageDiv.appendChild(contentDiv);
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // Show typing indicator
    function showTypingIndicator() {
        const indicator = document.createElement('div');
        indicator.className = 'message bot-message';
        indicator.id = 'typing-indicator';
        indicator.innerHTML = `
            <div class="message-content">
                <div class="typing-indicator">
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                </div>
            </div>`;
        chatMessages.appendChild(indicator);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // Hide typing indicator
    function hideTypingIndicator() {
        const indicator = document.getElementById('typing-indicator');
        if (indicator) {
            indicator.remove();
        }
    }

    // Format analysis results
    function formatAnalysis(analysis) {
        let html = `
        <div class="score-display">
            Your CV Score: ${analysis.overall_score}/100
        </div>
        <div class="analysis-section">
            <div class="section-title"><i class="fas fa-star"></i> Strengths</div>`;
        
        if (analysis.strengths && analysis.strengths.length > 0) {
            analysis.strengths.forEach(strength => {
                html += `<div class="suggestion-item strength">${strength}</div>`;
            });
        } else {
            html += `<p>No significant strengths identified yet.</p>`;
        }
        
        html += `</div><div class="analysis-section">
            <div class="section-title weakness"><i class="fas fa-exclamation-triangle"></i> Areas for Improvement</div>`;
        
        if (analysis.areas_for_improvement && analysis.areas_for_improvement.length > 0) {
            analysis.areas_for_improvement.forEach(improvement => {
                html += `<div class="suggestion-item">${improvement}</div>`;
            });
        } else {
            html += `<p>Your CV looks good overall!</p>`;
        }
        
        html += `</div>`;
        
        // Add detailed analysis if available
        if (analysis.detailed_analysis) {
            html += `<div class="analysis-section">
                <div class="section-title"><i class="fas fa-chart-bar"></i> Detailed Analysis</div>
                <p><strong>Skills Found:</strong> ${Object.values(analysis.detailed_analysis.skills_found).flat().join(', ') || 'None'}</p>
                <p><strong>Years of Experience:</strong> ${analysis.detailed_analysis.experience_metrics.years_of_experience}</p>
                <p><strong>Education Level:</strong> ${getEducationLevelText(analysis.detailed_analysis.education_level)}</p>
            </div>`;
        }
        
        return html;
    }

    function getEducationLevelText(level) {
        const levels = {
            0: 'No formal education identified',
            1: 'Associate/Diploma level',
            2: 'Bachelor degree',
            3: 'Master degree',
            4: 'PhD/Doctorate'
        };
        return levels[level] || 'Not specified';
    }

    // Handle file upload
    fileUpload.addEventListener('change', async function(e) {
        const file = e.target.files[0];
        if (file) {
            fileInfo.textContent = `Selected: ${file.name}`;
            addMessage('user', `Uploaded CV: ${file.name}`);
            
            // Validate file type
            if (!file.name.toLowerCase().endsWith('.pdf')) {
                addMessage('bot', 'Please upload only PDF files. Your CV must be in PDF format for analysis.');
                return;
            }
            
            showTypingIndicator();
            
            try {
                const formData = new FormData();
                formData.append('cv', file);
                
                const response = await fetch('/api/analyze_cv', {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                
                if (data.status === 'success') {
                    addMessage('bot', data.analysis, true);
                    addMessage('bot', "Would you like me to explain any of these suggestions in more detail?");
                } else {
                    addMessage('bot', data.message || "Sorry, I couldn't analyze your CV. Please try again.");
                }
            } catch (error) {
                console.error('Error analyzing CV:', error);
                addMessage('bot', "I encountered an error analyzing your CV. Please try again.");
            } finally {
                hideTypingIndicator();
            }
        }
    });
});