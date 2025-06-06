
        // Chat functionality
        document.getElementById('sendButton')?.addEventListener('click', function() {
            const messageInput = document.getElementById('messageInput');
            const message = messageInput.value.trim();
            
            if (message) {
                addMessageToChat(message, 'user-message', 'You');
                messageInput.value = '';
                
                setTimeout(() => {
                    addMessageToChat("Thanks for your message! I'll get back to you shortly.", 
                                    'consultant-message', 'Consultant');
                }, 1000);
            }
        });
        
        function addMessageToChat(message, messageClass, sender) {
            const chatContainer = document.getElementById('chatContainer');
            if (!chatContainer) return;
            
            const messageDiv = document.createElement('div');
            messageDiv.className = `chat-message ${messageClass}`;
            messageDiv.innerHTML = `<strong>${sender}:</strong> ${message}`;
            chatContainer.appendChild(messageDiv);
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
        
        // Delete functionality
        let itemToDelete = null;
        let deleteType = null;

        document.querySelectorAll('.delete-blog').forEach(btn => {
            btn.addEventListener('click', function() {
                itemToDelete = this.getAttribute('data-blog-id');
                deleteType = 'blog';
                const deleteModal = new bootstrap.Modal(document.getElementById('deleteConfirmModal'));
                deleteModal.show();
            });
        });

        document.querySelectorAll('.delete-mcq').forEach(btn => {
            btn.addEventListener('click', function() {
                itemToDelete = this.getAttribute('data-question-id');
                deleteType = 'mcq';
                const deleteModal = new bootstrap.Modal(document.getElementById('deleteConfirmModal'));
                deleteModal.show();
            });
        });

        document.getElementById('confirmDelete')?.addEventListener('click', function() {
            if (itemToDelete && deleteType) {
                fetch(`/delete_${deleteType}/${itemToDelete}`, {
                    method: 'DELETE'
                })
                .then(response => {
                    if (response.ok) {
                        window.location.reload();
                    }
                });
            }
        });
        
        // View MCQ details
        document.querySelectorAll('.view-mcq').forEach(btn => {
            btn.addEventListener('click', function() {
                const questionId = this.getAttribute('data-question-id');
                fetch(`/get_mcq/${questionId}`)
                    .then(response => response.json())
                    .then(data => {
                        // Format the date nicely
                        const createdDate = new Date(data.created_at);
                        const formattedDate = createdDate.toLocaleDateString('en-US', {
                            year: 'numeric',
                            month: 'long',
                            day: 'numeric',
                            hour: '2-digit',
                            minute: '2-digit'
                        });

                        // Create modal HTML with all question details
                        const modalHtml = `
                            <div class="modal fade" id="mcqDetailModal" tabindex="-1">
                                <div class="modal-dialog modal-lg">
                                    <div class="modal-content">
                                        <div class="modal-header bg-primary text-white">
                                            <h5 class="modal-title">MCQ Question Details</h5>
                                            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                                        </div>
                                        <div class="modal-body">
                                            <div class="row mb-3">
                                                <div class="col-md-6">
                                                    <p><strong>Job Role:</strong> ${data.job_role}</p>
                                                </div>
                                                <div class="col-md-6">
                                                    <p><strong>Experience Level:</strong> ${data.experience_level}</p>
                                                </div>
                                            </div>
                                            
                                            <div class="card mb-3">
                                                <div class="card-header bg-light">
                                                    <h6>Question</h6>
                                                </div>
                                                <div class="card-body">
                                                    <p class="lead">${data.question_text}</p>
                                                </div>
                                            </div>
                                            
                                            <div class="card mb-3">
                                                <div class="card-header bg-light">
                                                    <h6>Options</h6>
                                                </div>
                                                <div class="card-body">
                                                    <div class="list-group">
                                                        <div class="list-group-item ${data.correct_option === 1 ? 'list-group-item-success' : ''}">
                                                            <strong>Option 1:</strong> ${data.option1}
                                                            ${data.correct_option === 1 ? '<span class="badge bg-success float-end">Correct</span>' : ''}
                                                        </div>
                                                        <div class="list-group-item ${data.correct_option === 2 ? 'list-group-item-success' : ''}">
                                                            <strong>Option 2:</strong> ${data.option2}
                                                            ${data.correct_option === 2 ? '<span class="badge bg-success float-end">Correct</span>' : ''}
                                                        </div>
                                                        <div class="list-group-item ${data.correct_option === 3 ? 'list-group-item-success' : ''}">
                                                            <strong>Option 3:</strong> ${data.option3}
                                                            ${data.correct_option === 3 ? '<span class="badge bg-success float-end">Correct</span>' : ''}
                                                        </div>
                                                        <div class="list-group-item ${data.correct_option === 4 ? 'list-group-item-success' : ''}">
                                                            <strong>Option 4:</strong> ${data.option4}
                                                            ${data.correct_option === 4 ? '<span class="badge bg-success float-end">Correct</span>' : ''}
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                            
                                            ${data.explanation ? `
                                            <div class="card">
                                                <div class="card-header bg-light">
                                                    <h6>Explanation</h6>
                                                </div>
                                                <div class="card-body">
                                                    <p>${data.explanation}</p>
                                                </div>
                                            </div>
                                            ` : ''}
                                            
                                            <div class="mt-3 text-muted">
                                                <small>Created: ${formattedDate}</small>
                                            </div>
                                        </div>
                                        <div class="modal-footer">
                                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        `;
                        
                        // Add modal to DOM and show it
                        document.body.insertAdjacentHTML('beforeend', modalHtml);
                        const modal = new bootstrap.Modal(document.getElementById('mcqDetailModal'));
                        modal.show();
                        
                        // Clean up after modal is closed
                        document.getElementById('mcqDetailModal').addEventListener('hidden.bs.modal', function() {
                            this.remove();
                        });
                    })
                    .catch(error => {
                        console.error('Error loading MCQ:', error);
                        alert('Error loading question details. Please try again.');
                    });
            });
        });
        
        // Session request handling
        document.querySelectorAll('.accept-session').forEach(btn => {
            btn.addEventListener('click', function() {
                const requestId = this.getAttribute('data-request-id');
                fetch(`/accept_session/${requestId}`, {
                    method: 'POST'
                })
                .then(response => {
                    if (response.ok) {
                        window.location.reload();
                    }
                });
            });
        });
        
        document.querySelectorAll('.decline-session').forEach(btn => {
            btn.addEventListener('click', function() {
                const requestId = this.getAttribute('data-request-id');
                if (confirm('Are you sure you want to decline this session request?')) {
                    fetch(`/decline_session/${requestId}`, {
                        method: 'POST'
                    })
                    .then(response => {
                        if (response.ok) {
                            window.location.reload();
                        }
                    });
                }
            });
        });
        
        // Tab switching
        var triggerTabList = [].slice.call(document.querySelectorAll('a[data-bs-toggle="tab"]'));
        triggerTabList.forEach(function (triggerEl) {
            var tabTrigger =                triggerEl.addEventListener('click', function (event) {
                    event.preventDefault();
                    tabTrigger.show();
                });
            });
            
            // Auto-dismiss flash messages after 5 seconds
            setTimeout(() => {
                const alerts = document.querySelectorAll('.alert');
                alerts.forEach(alert => {
                    new bootstrap.Alert(alert).close();
                });
            }, 5000);

            // Language switching functionality
            let googleTranslateInstance = null;

            function googleTranslateElementInit() {
                googleTranslateInstance = new google.translate.TranslateElement({
                    pageLanguage: 'en',
                    includedLanguages: 'en,ar',
                    layout: google.translate.TranslateElement.InlineLayout.SIMPLE,
                    autoDisplay: false
                }, 'google_translate_element');
            }

            function switchLanguage(select) {
                const lang = select.value;

                if (lang === 'en') {
                    document.cookie = "googtrans=; path=/; expires=Thu, 01 Jan 1970 00:00:00 UTC;";
                    document.cookie = "googtrans=; domain=" + location.hostname + "; path=/; expires=Thu, 01 Jan 1970 00:00:00 UTC;";
                } else {
                    const cookieValue = `/en/${lang}`;
                    document.cookie = `googtrans=${cookieValue}; path=/;`;
                    document.cookie = `googtrans=${cookieValue}; domain=${location.hostname}; path=/;`;
                }

                window.location.reload();
            }

            function hideGoogleTranslateUI() {
                const selectors = [
                    '.goog-te-banner-frame',
                    '.goog-te-balloon-frame',
                    '#goog-gt-tt',
                    '.goog-te-menu-value',
                    '.goog-te-gadget-icon',
                    '.goog-te-gadget',
                    '.goog-te-combo',
                    '.skiptranslate'
                ];

                selectors.forEach(selector => {
                    const el = document.querySelector(selector);
                    if (el) {
                        el.style.display = 'none';
                        el.style.visibility = 'hidden';
                        el.style.height = '0';
                        el.style.width = '0';
                        el.style.overflow = 'hidden';
                        el.style.position = 'absolute';
                        el.style.top = '-9999px';
                        el.style.left = '-9999px';
                    }
                });
            }

            function forceLTR() {
                document.documentElement.setAttribute("dir", "ltr");
                document.body.setAttribute("dir", "ltr");
            }

            function forceLTRHeader() {
                const headerElements = document.querySelectorAll('.sidebar, .nav, .profile-card, .lang-select');
                headerElements.forEach(el => {
                    el.style.direction = 'ltr';
                    el.style.textAlign = 'left';
                });
            }

            window.addEventListener('DOMContentLoaded', function () {
                if (!document.cookie.includes("googtrans")) {
                    document.cookie = "googtrans=/en/en; path=/;";
                    document.cookie = "googtrans=/en/en; domain=" + location.hostname + "; path=/;";
                }

                const select = document.getElementById("lang-select");
                if (document.cookie.includes("googtrans=/en/ar")) {
                    select.value = "ar";
                } else {
                    select.value = "en";
                }

                if (!document.querySelector('script[src*="translate.google.com"]')) {
                    const script = document.createElement('script');
                    script.src = 'https://translate.google.com/translate_a/element.js?cb=googleTranslateElementInit';
                    document.body.appendChild(script);
                }
            });

            const observer = new MutationObserver(function (mutations) {
                mutations.forEach(function (mutation) {
                    if (mutation.addedNodes) {
                        hideGoogleTranslateUI();
                    }
                });
            });

            observer.observe(document.body, {
                childList: true,
                subtree: true
            });

            window.addEventListener('load', () => {
                setTimeout(() => {
                    forceLTR();
                    forceLTRHeader();
                }, 1000);
            });