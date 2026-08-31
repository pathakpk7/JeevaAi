import { chatApi } from './api.js';
import { appState } from './state.js';
import { renderMarkdown } from './markdown.js';

document.addEventListener('DOMContentLoaded', () => {
    // DOM ELEMENTS — CHAT
    const emptyState = document.getElementById('empty-state');
    const messagesThread = document.getElementById('messages-thread');
    const composerForm = document.getElementById('composer-form');
    const userInput = document.getElementById('user-input');
    const charCounter = document.getElementById('char-counter');
    const sendBtn = document.getElementById('send-btn');
    const conversationsList = document.getElementById('conversations-list');
    const drawerToggleBtn = document.getElementById('drawer-toggle-btn');
    const sidebarDrawer = document.getElementById('sidebar-drawer');
    const drawerOverlay = document.getElementById('drawer-overlay');
    const headerNewChatBtn = document.getElementById('header-new-chat-btn');
    const sidebarNewChatBtn = document.getElementById('sidebar-new-chat-btn');

    // DOM ELEMENTS — VIEW NAV SWITCHER
    const navChatBtn = document.getElementById('nav-chat-btn');
    const navExplorerBtn = document.getElementById('nav-explorer-btn');
    const chatView = document.getElementById('chat-view');
    const explorerView = document.getElementById('explorer-view');

    // DOM ELEMENTS — KNOWLEDGE EXPLORER
    const explorerSearchForm = document.getElementById('explorer-search-form');
    const explorerSearchInput = document.getElementById('explorer-search-input');
    const explorerModeSelect = document.getElementById('explorer-mode-select');
    const explorerResultsContainer = document.getElementById('explorer-results-container');
    const explorerEmptyNotice = document.getElementById('explorer-empty-state');
    const explorerResultsFeed = document.getElementById('explorer-results-feed');

    // DOM ELEMENTS — MODALS
    const disclaimerModalBtn = document.getElementById('disclaimer-modal-btn');
    const safetyModal = document.getElementById('safety-modal');
    const modalCloseBtn = document.getElementById('modal-close-btn');
    const articleDetailModal = document.getElementById('article-detail-modal');
    const articleModalCloseBtn = document.getElementById('article-modal-close-btn');
    const articleModalBody = document.getElementById('article-modal-body');
    const articleModalTitle = document.getElementById('article-modal-title');

    // DOM ELEMENTS — NEW FEATURES
    const languageSelect = document.getElementById('language-select');
    const symptomWizardBtn = document.getElementById('symptom-wizard-btn');
    const exportChatBtn = document.getElementById('export-chat-btn');
    const reportFileInput = document.getElementById('report-file-input');
    const attachedFileBadge = document.getElementById('attached-file-badge');
    const attachedFileName = document.getElementById('attached-file-name');
    const removeFileBtn = document.getElementById('remove-file-btn');
    const symptomWizardModal = document.getElementById('symptom-wizard-modal');
    const wizardCloseBtn = document.getElementById('wizard-close-btn');
    const wizardSubmitBtn = document.getElementById('wizard-submit-btn');
    const wizardNotesInput = document.getElementById('wizard-notes-input');
    const voiceInputBtn = document.getElementById('voice-input-btn');

    // 1. VIEW TAB SWITCHING
    if (navChatBtn && navExplorerBtn) {
        navChatBtn.addEventListener('click', () => switchView('chat'));
        navExplorerBtn.addEventListener('click', () => switchView('explorer'));
    }

    function switchView(viewName) {
        if (viewName === 'chat') {
            if (navChatBtn) { navChatBtn.classList.add('active'); navChatBtn.setAttribute('aria-selected', 'true'); }
            if (navExplorerBtn) { navExplorerBtn.classList.remove('active'); navExplorerBtn.setAttribute('aria-selected', 'false'); }
            if (chatView) chatView.classList.add('active');
            if (explorerView) explorerView.classList.remove('active');
        } else {
            if (navExplorerBtn) { navExplorerBtn.classList.add('active'); navExplorerBtn.setAttribute('aria-selected', 'true'); }
            if (navChatBtn) { navChatBtn.classList.remove('active'); navChatBtn.setAttribute('aria-selected', 'false'); }
            if (explorerView) explorerView.classList.add('active');
            if (chatView) chatView.classList.remove('active');
            if (explorerSearchInput) explorerSearchInput.focus();
        }
        closeMobileDrawer();
    }

    // 2. VOICE SPEECH-TO-TEXT INPUT
    let recognition = null;
    if ('SpeechRecognition' in window || 'webkitSpeechRecognition' in window) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;

        recognition.onstart = () => {
            if (voiceInputBtn) voiceInputBtn.classList.add('listening');
        };

        recognition.onresult = (e) => {
            const transcript = e.results[0][0].transcript;
            if (transcript && userInput) {
                userInput.value = (userInput.value ? userInput.value + ' ' : '') + transcript;
                userInput.dispatchEvent(new Event('input'));
                userInput.focus();
            }
        };

        recognition.onend = () => {
            if (voiceInputBtn) voiceInputBtn.classList.remove('listening');
        };

        recognition.onerror = () => {
            if (voiceInputBtn) voiceInputBtn.classList.remove('listening');
        };
    }

    if (voiceInputBtn) {
        voiceInputBtn.addEventListener('click', () => {
            if (!recognition) {
                alert('Voice speech recognition is not supported in this browser. Please type your query.');
                return;
            }
            if (voiceInputBtn.classList.contains('listening')) {
                recognition.stop();
            } else {
                const lang = getSelectedLanguage();
                recognition.lang = lang === 'Hindi' ? 'hi-IN' : (lang === 'Spanish' ? 'es-ES' : 'en-US');
                recognition.start();
            }
        });
    }

    // LANGUAGE SELECTION PERSISTENCE
    const savedLang = localStorage.getItem('jeeva_language') || 'English';
    if (languageSelect) {
        languageSelect.value = savedLang;
        languageSelect.addEventListener('change', () => {
            localStorage.setItem('jeeva_language', languageSelect.value);
        });
    }

    function getSelectedLanguage() {
        return languageSelect ? languageSelect.value : 'English';
    }

    // FILE ATTACHMENT STATE
    let currentAttachedFile = null;

    if (reportFileInput) {
        reportFileInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) {
                currentAttachedFile = file;
                attachedFileName.textContent = file.name;
                attachedFileBadge.classList.remove('hidden');
                userInput.placeholder = `Add notes for ${file.name} (or leave empty and send)...`;
                sendBtn.disabled = false;
            }
        });
    }

    if (removeFileBtn) {
        removeFileBtn.addEventListener('click', () => {
            clearAttachedFile();
        });
    }

    function clearAttachedFile() {
        currentAttachedFile = null;
        if (reportFileInput) reportFileInput.value = '';
        if (attachedFileBadge) attachedFileBadge.classList.add('hidden');
        if (userInput) {
            userInput.placeholder = "Ask a medical question or attach a lab report...";
            sendBtn.disabled = userInput.value.trim().length === 0;
        }
    }

    // USER TEXTAREA AUTO-RESIZE & SEND BUTTON DISABLING
    if (userInput) {
        function autoResizeTextarea() {
            userInput.style.height = '44px';
            const newHeight = Math.max(44, Math.min(userInput.scrollHeight, 320));
            userInput.style.height = newHeight + 'px';
        }

        userInput.addEventListener('input', () => {
            const len = userInput.value.trim().length;
            if (charCounter) charCounter.textContent = `${userInput.value.length} / 2000`;
            if (sendBtn) sendBtn.disabled = (len === 0 && !currentAttachedFile) || appState.isLoading;

            autoResizeTextarea();
        });
    }

    // CHAT FORM SUBMIT (TEXT OR FILE REPORT)
    composerForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const text = userInput.value.trim();
        const lang = getSelectedLanguage();

        if (!text && !currentAttachedFile) return;
        if (appState.isLoading) return;

        appState.setLoading(true);
        appState.clearError();

        // 1. IF REPORT FILE IS ATTACHED
        if (currentAttachedFile) {
            const fileToUpload = currentAttachedFile;
            const userMsgText = text ? `[Attached Report: ${fileToUpload.name}] ${text}` : `[Attached Report Analysis: ${fileToUpload.name}]`;
            
            clearAttachedFile();
            userInput.value = '';
            userInput.style.height = '44px';
            charCounter.textContent = '0 / 2000';
            sendBtn.disabled = true;

            appState.addMessage({ role: 'user', content: userMsgText });

            try {
                const data = await chatApi.uploadReport(fileToUpload, lang);
                appState.addMessage({
                    role: 'assistant',
                    content: data.analysis,
                    match_quality: data.match_quality || 'Report Analyzed',
                    sources: data.citations || [],
                });
            } catch (err) {
                appState.setError({
                    code: err.code || 'UPLOAD_ERROR',
                    message: err.message || 'Failed to process report. Please try again.',
                    failedText: userMsgText
                });
            } finally {
                appState.setLoading(false);
            }
            return;
        }

        // 2. STANDARD CHAT QUERY
        userInput.value = '';
        userInput.style.height = '44px';
        charCounter.textContent = '0 / 2000';
        sendBtn.disabled = true;

        appState.addMessage({ role: 'user', content: text });

        try {
            const data = await chatApi.sendMessage(text, appState.conversationId, lang);
            
            if (data.conversation_id) {
                appState.conversationId = data.conversation_id;
                appState.saveCurrentConversationTitle(data.message || text);
            }

            appState.addMessage({
                role: 'assistant',
                content: data.answer,
                match_quality: data.match_quality,
                sources: data.sources || [],
                query_used: data.query_used_for_retrieval,
                metrics: data.metrics
            });
        } catch (err) {
            appState.setError({
                code: err.code || 'ERROR',
                message: err.message || 'An unexpected error occurred. Please try again.',
                failedText: text
            });
        } finally {
            appState.setLoading(false);
        }
    });

    // EXPORT CONSULTATION SUMMARY (.MD DOWNLOAD)
    if (exportChatBtn) {
        exportChatBtn.addEventListener('click', () => {
            if (appState.messages.length === 0) {
                alert('No active conversation to export.');
                return;
            }

            const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
            let mdContent = `# JeevaAi MedeBot — Consultation Summary\n`;
            mdContent += `**Date:** ${new Date().toLocaleString()}\n`;
            mdContent += `**Language:** ${getSelectedLanguage()}\n\n`;
            mdContent += `---\n\n`;

            appState.messages.forEach((msg, idx) => {
                const speaker = msg.role === 'user' ? '👤 User' : '🩺 JeevaAi MedeBot';
                mdContent += `### ${speaker}\n${msg.content}\n\n`;
                if (msg.sources && msg.sources.length > 0) {
                    mdContent += `**Citations:**\n`;
                    msg.sources.forEach((src, i) => {
                        mdContent += `- [${i + 1}] ${src.article_title} (Page ${src.page})\n`;
                    });
                    mdContent += `\n`;
                }
            });

            mdContent += `---\n*Educational use only. Not medical advice.*\n`;

            const blob = new Blob([mdContent], { type: 'text/markdown;charset=utf-8' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `JeevaAi_Consultation_${timestamp}.md`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        });
    }

    // SYMPTOM CHECKER WIZARD MODAL LOGIC
    let wizardData = { category: '', duration: '', severity: '' };

    if (symptomWizardBtn) {
        symptomWizardBtn.addEventListener('click', (e) => {
            e.preventDefault();
            resetWizard();
            if (symptomWizardModal) {
                symptomWizardModal.classList.add('open');
                symptomWizardModal.setAttribute('aria-hidden', 'false');
            }
        });
    }

    if (wizardCloseBtn) {
        wizardCloseBtn.addEventListener('click', () => closeWizardModal());
    }

    if (symptomWizardModal) {
        symptomWizardModal.addEventListener('click', (e) => {
            if (e.target === symptomWizardModal) {
                closeWizardModal();
                return;
            }

            const optionBtn = e.target.closest('.wizard-option-btn');
            if (!optionBtn) return;

            // Step 1: Category / Location Selection
            if (optionBtn.hasAttribute('data-category')) {
                wizardData.category = optionBtn.getAttribute('data-category');
                const s1 = document.getElementById('wizard-step-1');
                const s2 = document.getElementById('wizard-step-2');
                if (s1) { s1.classList.remove('active'); s1.classList.add('hidden'); }
                if (s2) { s2.classList.remove('hidden'); s2.classList.add('active'); }
            } 
            // Step 2: Duration Selection
            else if (optionBtn.hasAttribute('data-duration')) {
                wizardData.duration = optionBtn.getAttribute('data-duration');
                const s2 = document.getElementById('wizard-step-2');
                const s3 = document.getElementById('wizard-step-3');
                if (s2) { s2.classList.remove('active'); s2.classList.add('hidden'); }
                if (s3) { s3.classList.remove('hidden'); s3.classList.add('active'); }
            } 
            // Step 3: Severity Selection
            else if (optionBtn.hasAttribute('data-severity')) {
                document.querySelectorAll('#wizard-step-3 .wizard-option-btn').forEach(b => b.classList.remove('selected'));
                optionBtn.classList.add('selected');
                wizardData.severity = optionBtn.getAttribute('data-severity');
            }
        });
    }

    function closeWizardModal() {
        if (symptomWizardModal) {
            symptomWizardModal.classList.remove('open');
            symptomWizardModal.setAttribute('aria-hidden', 'true');
        }
    }

    function resetWizard() {
        wizardData = { category: '', duration: '', severity: '' };
        const s1 = document.getElementById('wizard-step-1');
        const s2 = document.getElementById('wizard-step-2');
        const s3 = document.getElementById('wizard-step-3');
        if (s1) { s1.classList.remove('hidden'); s1.classList.add('active'); }
        if (s2) { s2.classList.remove('active'); s2.classList.add('hidden'); }
        if (s3) { s3.classList.remove('active'); s3.classList.add('hidden'); }
        document.querySelectorAll('.wizard-option-btn').forEach(btn => btn.classList.remove('selected'));
        if (wizardNotesInput) wizardNotesInput.value = '';
    }

    if (wizardSubmitBtn) {
        wizardSubmitBtn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();

            const notes = wizardNotesInput ? wizardNotesInput.value.trim() : '';
            const category = wizardData.category || 'General';
            const duration = wizardData.duration || 'recently';
            const severity = wizardData.severity || 'Moderate';

            let query = `I am experiencing ${severity.toLowerCase()} ${category} symptoms for ${duration}.`;
            if (notes) query += ` Specific details: ${notes}.`;
            query += ` What medical information and guidance is available for this?`;

            closeWizardModal();
            switchView('chat');
            if (userInput) {
                userInput.value = query;
                userInput.dispatchEvent(new Event('input'));
                userInput.focus();
            }
        });
    }

    // 5. NEW CHAT BUTTONS
    headerNewChatBtn.addEventListener('click', () => startNewChatSession());
    sidebarNewChatBtn.addEventListener('click', () => startNewChatSession());

    function startNewChatSession() {
        switchView('chat');
        appState.startNewChat();
        renderDynamicChatQuestions();
        closeMobileDrawer();
        userInput.focus();
    }

    // 6. DRAWER TOGGLE (MOBILE & DESKTOP HISTORY)
    const historyToggleBtn = document.getElementById('history-toggle-btn');
    if (historyToggleBtn) {
        historyToggleBtn.addEventListener('click', () => {
            const isOpen = sidebarDrawer.classList.contains('open');
            if (isOpen) {
                closeMobileDrawer();
            } else {
                openMobileDrawer();
            }
        });
    }

    drawerToggleBtn.addEventListener('click', () => {
        const isOpen = sidebarDrawer.classList.contains('open');
        if (isOpen) {
            closeMobileDrawer();
        } else {
            openMobileDrawer();
        }
    });

    drawerOverlay.addEventListener('click', () => closeMobileDrawer());

    function openMobileDrawer() {
        sidebarDrawer.classList.add('open');
        drawerOverlay.classList.add('open');
        drawerToggleBtn.setAttribute('aria-expanded', 'true');
    }

    function closeMobileDrawer() {
        sidebarDrawer.classList.remove('open');
        drawerOverlay.classList.remove('open');
        drawerToggleBtn.setAttribute('aria-expanded', 'false');
    }

    // 7. MODALS (SAFETY & ARTICLE DETAIL)
    disclaimerModalBtn.addEventListener('click', () => {
        safetyModal.classList.add('open');
        safetyModal.setAttribute('aria-hidden', 'false');
    });

    modalCloseBtn.addEventListener('click', () => closeSafetyModal());
    articleModalCloseBtn.addEventListener('click', () => closeArticleModal());

    safetyModal.addEventListener('click', (e) => {
        if (e.target === safetyModal) closeSafetyModal();
    });

    articleDetailModal.addEventListener('click', (e) => {
        if (e.target === articleDetailModal) closeArticleModal();
    });

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeSafetyModal();
            closeArticleModal();
            closeMobileDrawer();
        }
    });

    function closeSafetyModal() {
        safetyModal.classList.remove('open');
        safetyModal.setAttribute('aria-hidden', 'true');
    }

    function closeArticleModal() {
        articleDetailModal.classList.remove('open');
        articleDetailModal.setAttribute('aria-hidden', 'true');
    }

    function openArticleModal(sourceObj) {
        articleModalTitle.textContent = `${sourceObj.article_title || 'Article Detail'}`;
        articleModalBody.innerHTML = `
            <div class="source-meta-grid" style="margin-bottom: 16px;">
                <div><strong>Document:</strong> ${sourceObj.document_name || sourceObj.source || 'Encyclopedia PDF'}</div>
                <div><strong>Page Number:</strong> ${sourceObj.page}</div>
                <div><strong>Article Title:</strong> ${sourceObj.article_title}</div>
                <div><strong>Section Heading:</strong> ${sourceObj.section}</div>
                <div><strong>Chunk ID:</strong> <code>${sourceObj.chunk_id || 'N/A'}</code></div>
                <div><strong>Relevance Score:</strong> ${(sourceObj.score || 0).toFixed(4)}</div>
            </div>
            <hr style="border: none; border-top: 1px solid var(--border-subtle); margin: 16px 0;" />
            <h4 style="color: var(--accent-teal); margin-bottom: 8px;">Excerpt Content:</h4>
            <div style="background-color: var(--bg-code); padding: 14px; border-radius: var(--radius-sm); font-size: 0.9rem; line-height: 1.6; max-height: 300px; overflow-y: auto;">
                ${renderMarkdown(sourceObj.snippet || sourceObj.text || 'No text snippet available.')}
            </div>
        `;
        articleDetailModal.classList.add('open');
        articleDetailModal.setAttribute('aria-hidden', 'false');
    }

    // 8. KNOWLEDGE EXPLORER MODE SWITCH EXPLANATIONS
    const modeExplanationBadge = document.getElementById('mode-explanation-badge');

    const MODE_EXPLANATIONS = {
        hybrid: {
            title: "🎯 Hybrid RRF (Recommended)",
            desc: "<strong>Best Input:</strong> Full questions or mixed symptoms (e.g. <em>\"What causes high blood pressure and dizziness?\"</em>).<br><strong>Output:</strong> Merges deep conceptual meaning with exact keyword matching for peak search accuracy."
        },
        dense: {
            title: "🧠 Semantic Search (Dense Embeddings)",
            desc: "<strong>Best Input:</strong> Natural language phrases or conceptual descriptions (e.g. <em>\"feeling lightheaded and tired in the morning\"</em>).<br><strong>Output:</strong> Retrieves passages with matching medical meanings and concepts, even if exact keywords differ."
        },
        lexical: {
            title: "🔤 Lexical Search (BM25 Keyword Matching)",
            desc: "<strong>Best Input:</strong> Specific drug names, medical codes, or exact technical terms (e.g. <em>\"Metformin\"</em>, <em>\"Campylobacteriosis\"</em>, <em>\"Caffeine Overdose\"</em>).<br><strong>Output:</strong> Performs exact string and keyword matching directly against indexed encyclopedia text."
        }
    };

    if (explorerModeSelect && modeExplanationBadge) {
        explorerModeSelect.addEventListener('change', () => {
            const mode = explorerModeSelect.value || 'hybrid';
            const info = MODE_EXPLANATIONS[mode] || MODE_EXPLANATIONS.hybrid;
            modeExplanationBadge.innerHTML = `
                <div class="mode-badge-title">${info.title}</div>
                <div class="mode-badge-desc">${info.desc}</div>
            `;
        });
    }

    // KNOWLEDGE EXPLORER SEARCH FORM SUBMIT
    explorerSearchForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const query = explorerSearchInput.value.trim();
        if (!query) return;

        const mode = explorerModeSelect.value || 'hybrid';
        explorerEmptyNotice.style.display = 'none';
        explorerResultsFeed.innerHTML = '<div class="explorer-empty-notice">Searching indexed medical knowledge...</div>';

        try {
            const data = await chatApi.searchKnowledge(query, 12, mode);
            renderExplorerResults(data);
        } catch (err) {
            explorerResultsFeed.innerHTML = `
                <div class="explorer-empty-notice" style="color: var(--match-none-text);">
                    Search execution failed: ${err.message || 'Server error'}
                </div>
            `;
        }
    });

    function renderExplorerResults(data) {
        explorerResultsFeed.innerHTML = '';
        if (!data.results || data.results.length === 0) {
            explorerResultsFeed.innerHTML = `
                <div class="explorer-empty-notice">
                    No matching medical chunks found for query "${data.query}".
                </div>
            `;
            return;
        }

        const summaryHeader = document.createElement('div');
        summaryHeader.style.fontSize = '0.85rem';
        summaryHeader.style.color = 'var(--text-muted)';
        summaryHeader.style.marginBottom = '12px';
        summaryHeader.textContent = `Found ${data.result_count} relevant chunks in ${data.search_latency_ms} ms (Mode: ${data.search_mode.toUpperCase()})`;
        explorerResultsFeed.appendChild(summaryHeader);

        data.results.forEach((item, idx) => {
            const card = document.createElement('div');
            card.className = 'explorer-result-card';

            card.innerHTML = `
                <div class="card-top">
                    <div class="card-title-group">
                        <span class="card-article-title">${item.article_title}</span>
                        <span class="card-section-tag">${item.section}</span>
                    </div>
                    <span style="font-size: 0.78rem; font-weight: 600; color: var(--accent-teal);">Score: ${item.score.toFixed(4)}</span>
                </div>
                <div class="card-snippet">${item.snippet.substring(0, 300)}${item.snippet.length > 300 ? '...' : ''}</div>
                <div class="card-footer">
                    <span>Page ${item.page} | ${item.source}</span>
                    <button class="action-btn view-detail-btn">
                        <span>View Detail</span> &rarr;
                    </button>
                </div>
            `;

            card.querySelector('.view-detail-btn').addEventListener('click', () => {
                openArticleModal(item);
            });

            explorerResultsFeed.appendChild(card);
        });
    }

    // UI CHAT RENDER FUNCTIONS & STATE SUBSCRIPTIONS
    appState.subscribe(updateUiState);
    appState.subscribe(renderConversationsNav);

    function updateUiState() {
        if (appState.messages.length === 0 && !appState.isLoading && !appState.error) {
            emptyState.style.display = 'block';
            messagesThread.style.display = 'none';
            messagesThread.innerHTML = '';
        } else {
            emptyState.style.display = 'none';
            messagesThread.style.display = 'flex';
            renderMessagesThread();
        }
    }

    function renderMessagesThread() {
        messagesThread.innerHTML = '';

        appState.messages.forEach(msg => {
            const wrapper = document.createElement('div');
            wrapper.className = `message-wrapper ${msg.role}`;

            if (msg.role === 'user') {
                const bubble = document.createElement('div');
                bubble.className = 'message-bubble';
                bubble.textContent = msg.content;
                wrapper.appendChild(bubble);
            } else {
                const bubble = document.createElement('div');
                bubble.className = 'message-bubble';

                if (msg.match_quality) {
                    const qualityLower = msg.match_quality.toLowerCase();
                    const badgeClass = qualityLower.includes('strong') ? 'strong' : (qualityLower.includes('limited') ? 'limited' : 'none');
                    const badge = document.createElement('div');
                    badge.className = `match-quality-bar ${badgeClass}`;
                    badge.textContent = `Retrieval Match: ${msg.match_quality}`;
                    bubble.appendChild(badge);
                }

                const contentDiv = document.createElement('div');
                contentDiv.className = 'markdown-body';
                contentDiv.innerHTML = renderMarkdown(msg.content);
                bubble.appendChild(contentDiv);

                if (msg.sources && msg.sources.length > 0) {
                    const sourcesContainer = createSourcesContainer(msg.sources);
                    bubble.appendChild(sourcesContainer);
                }

                const actionsBar = document.createElement('div');
                actionsBar.className = 'message-actions';

                const copyBtn = document.createElement('button');
                copyBtn.className = 'action-btn';
                copyBtn.innerHTML = `
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                    </svg>
                    <span>Copy Answer</span>
                `;
                copyBtn.addEventListener('click', () => {
                    navigator.clipboard.writeText(msg.content).then(() => {
                        const span = copyBtn.querySelector('span');
                        span.textContent = 'Copied!';
                        setTimeout(() => { span.textContent = 'Copy Answer'; }, 2000);
                    });
                });

                const speakBtn = document.createElement('button');
                speakBtn.className = 'action-btn';
                speakBtn.innerHTML = `
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon>
                        <path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"></path>
                    </svg>
                    <span>Read Aloud</span>
                `;

                speakBtn.addEventListener('click', () => {
                    if ('speechSynthesis' in window) {
                        window.speechSynthesis.cancel();
                        const textToRead = msg.content.replace(/[#*`_]/g, '');
                        const utterance = new SpeechSynthesisUtterance(textToRead);
                        const lang = getSelectedLanguage();
                        utterance.lang = lang === 'Hindi' ? 'hi-IN' : (lang === 'Spanish' ? 'es-ES' : 'en-US');
                        window.speechSynthesis.speak(utterance);
                    } else {
                        alert('Text-to-speech is not supported in this browser.');
                    }
                });

                actionsBar.appendChild(copyBtn);
                actionsBar.appendChild(speakBtn);
                bubble.appendChild(actionsBar);
                wrapper.appendChild(bubble);
            }

            messagesThread.appendChild(wrapper);
        });

        if (appState.isLoading) {
            const loadingWrapper = document.createElement('div');
            loadingWrapper.className = 'message-wrapper assistant';
            loadingWrapper.innerHTML = `
                <div class="message-bubble">
                    <div class="loading-dots">
                        <span></span><span></span><span></span>
                    </div>
                </div>
            `;
            messagesThread.appendChild(loadingWrapper);
        }

        if (appState.error) {
            const errorWrapper = document.createElement('div');
            errorWrapper.className = 'message-wrapper assistant';

            const errBubble = document.createElement('div');
            errBubble.className = 'message-bubble';
            errBubble.style.borderColor = 'var(--match-none-border)';
            errBubble.style.backgroundColor = 'var(--match-none-bg)';

            errBubble.innerHTML = `
                <div style="color: var(--match-none-text); font-weight: 600; margin-bottom: 4px;">System Notice</div>
                <p style="color: var(--text-main); font-size: 0.9rem;">${appState.error.message}</p>
            `;

            const retryBtn = document.createElement('button');
            retryBtn.className = 'btn btn-secondary';
            retryBtn.style.marginTop = '10px';
            retryBtn.innerHTML = `
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="23 4 23 10 17 10"></polyline>
                    <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path>
                </svg>
                <span>Retry Question</span>
            `;

            retryBtn.addEventListener('click', () => {
                if (appState.error.failedText) {
                    const text = appState.error.failedText;
                    appState.clearError();
                    userInput.value = text;
                    composerForm.dispatchEvent(new Event('submit'));
                }
            });

            errBubble.appendChild(retryBtn);
            errorWrapper.appendChild(errBubble);
            messagesThread.appendChild(errorWrapper);
        }

        const chatContainer = document.getElementById('chat-container');
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    function createSourcesContainer(sources) {
        const container = document.createElement('div');
        container.className = 'sources-container';

        const title = document.createElement('div');
        title.className = 'sources-title';
        title.textContent = `Sources & Citations (${sources.length})`;
        container.appendChild(title);

        const list = document.createElement('div');
        list.className = 'sources-list';

        sources.forEach((src, idx) => {
            const card = document.createElement('div');
            card.className = 'source-card';

            const headerBtn = document.createElement('button');
            headerBtn.className = 'source-header';
            headerBtn.innerHTML = `
                <span>[${idx + 1}] ${src.article_title} (Page ${src.page})</span>
                <span style="font-size: 0.75rem; color: var(--accent-teal);">Inspect &rarr;</span>
            `;

            headerBtn.addEventListener('click', () => {
                openArticleModal(src);
            });

            card.appendChild(headerBtn);
            list.appendChild(card);
        });

        container.appendChild(list);
        return container;
    }

    function renderConversationsNav() {
        conversationsList.innerHTML = '';
        if (appState.conversations.length === 0) {
            const emptyNav = document.createElement('div');
            emptyNav.style.fontSize = '0.8rem';
            emptyNav.style.color = '#94a3b8';
            emptyNav.style.padding = '8px 12px';
            emptyNav.textContent = 'No recent conversations';
            conversationsList.appendChild(emptyNav);
            return;
        }

        appState.conversations.forEach(conv => {
            const item = document.createElement('div');
            item.className = `conversation-item ${conv.id === appState.conversationId ? 'active' : ''}`;

            const titleSpan = document.createElement('span');
            titleSpan.className = 'conversation-title';
            titleSpan.textContent = conv.title;
            item.appendChild(titleSpan);

            const delBtn = document.createElement('button');
            delBtn.className = 'delete-conv-btn';
            delBtn.setAttribute('aria-label', 'Delete conversation');
            delBtn.innerHTML = `
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="3 6 5 6 21 6"></polyline>
                    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                </svg>
            `;

            delBtn.addEventListener('click', async (e) => {
                e.stopPropagation();
                await chatApi.deleteConversation(conv.id);
                appState.removeConversation(conv.id);
            });

            item.addEventListener('click', async () => {
                switchView('chat');
                appState.selectConversation(conv.id);
                closeMobileDrawer();

                // If messages are empty for older records, fetch history from server API
                if (appState.messages.length === 0) {
                    try {
                        const historyMsgs = await chatApi.getHistory(conv.id);
                        if (historyMsgs && historyMsgs.length > 0) {
                            appState.messages = historyMsgs;
                            appState.updateCurrentConversationRecord();
                            appState.notify();
                        }
                    } catch (err) {
                        console.warn('Failed to load server history:', err);
                    }
                }
            });

            item.appendChild(delBtn);
            conversationsList.appendChild(item);
        });
    }

    // INITIAL UI RENDERS ON LOAD
    updateUiState();
    renderConversationsNav();
    renderDynamicChatQuestions();
    renderExplorerSuggestions();
});
