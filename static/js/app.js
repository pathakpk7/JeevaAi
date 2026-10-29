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
    const navInteractionsBtn = document.getElementById('nav-interactions-btn');
    const chatView = document.getElementById('chat-view');
    const explorerView = document.getElementById('explorer-view');
    const interactionsView = document.getElementById('interactions-view');

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

    // DOM ELEMENTS — CLINICAL & ADVANCED TOOLS
    let wizardData = { age: '', gender: '', category: '', duration: '', severity: '', conditions: [] };
    const themeToggleBtn = document.getElementById('theme-toggle-btn');
    const themeIcon = document.getElementById('theme-icon');
    const languageSelect = document.getElementById('language-select');
    const symptomWizardBtn = document.getElementById('symptom-wizard-btn');
    const firstAidBtn = document.getElementById('first-aid-btn');
    const firstAidModal = document.getElementById('first-aid-modal');
    const firstAidCloseBtn = document.getElementById('first-aid-close-btn');
    const firstAidTabContent = document.getElementById('first-aid-tab-content');
    const doctorPrepBtn = document.getElementById('doctor-prep-btn');
    const doctorPrepModal = document.getElementById('doctor-prep-modal');
    const doctorPrepCloseBtn = document.getElementById('doctor-prep-close-btn');
    const doctorPrepBody = document.getElementById('doctor-prep-body');
    const printDoctorSummaryBtn = document.getElementById('print-doctor-summary-btn');
    const copyDoctorSummaryBtn = document.getElementById('copy-doctor-summary-btn');
    const emergencyModal = document.getElementById('emergency-modal');
    const emergencyCloseBtn = document.getElementById('emergency-close-btn');
    const emergencyDismissBtn = document.getElementById('emergency-dismiss-btn');
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
    const medInput = document.getElementById('med-input');
    const addMedBtn = document.getElementById('add-med-btn');
    const selectedMedsChips = document.getElementById('selected-meds-chips');
    const checkInteractionsBtn = document.getElementById('check-interactions-btn');
    const clearMedsBtn = document.getElementById('clear-meds-btn');
    const interactionsResultsFeed = document.getElementById('interactions-results-feed');
    const interactionsEmptyNotice = document.getElementById('interactions-empty-state');

    // 1. VIEW TAB SWITCHING
    if (navChatBtn) {
        navChatBtn.addEventListener('click', () => switchView('chat'));
    }
    if (navExplorerBtn) {
        navExplorerBtn.addEventListener('click', () => switchView('explorer'));
    }
    if (navInteractionsBtn) {
        navInteractionsBtn.addEventListener('click', () => switchView('interactions'));
    }

    function switchView(viewName) {
        [navChatBtn, navExplorerBtn, navInteractionsBtn].forEach(b => {
            if (b) { b.classList.remove('active'); b.setAttribute('aria-selected', 'false'); }
        });
        [chatView, explorerView, interactionsView].forEach(v => {
            if (v) v.classList.remove('active');
        });

        if (viewName === 'chat') {
            if (navChatBtn) { navChatBtn.classList.add('active'); navChatBtn.setAttribute('aria-selected', 'true'); }
            if (chatView) chatView.classList.add('active');
        } else if (viewName === 'explorer') {
            if (navExplorerBtn) { navExplorerBtn.classList.add('active'); navExplorerBtn.setAttribute('aria-selected', 'true'); }
            if (explorerView) explorerView.classList.add('active');
            if (explorerSearchInput) explorerSearchInput.focus();
        } else if (viewName === 'interactions') {
            if (navInteractionsBtn) { navInteractionsBtn.classList.add('active'); navInteractionsBtn.setAttribute('aria-selected', 'true'); }
            if (interactionsView) interactionsView.classList.add('active');
            if (medInput) medInput.focus();
            renderMedChips();
        }
        closeMobileDrawer();
    }

    // 1B. THEME TOGGLE (DARK / LIGHT)
    let currentTheme = localStorage.getItem('jeeva_theme') || 'light';
    applyTheme(currentTheme);

    if (themeToggleBtn) {
        themeToggleBtn.addEventListener('click', () => {
            currentTheme = currentTheme === 'light' ? 'dark' : 'light';
            localStorage.setItem('jeeva_theme', currentTheme);
            applyTheme(currentTheme);
        });
    }

    function applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        if (themeIcon) {
            themeIcon.textContent = theme === 'dark' ? '☀️' : '🌙';
        }
    }

    // 1C. EMERGENCY RED-FLAG REAL-TIME DETECTION
    const EMERGENCY_KEYWORDS = [
        'chest pain', 'heart attack', 'shortness of breath', 'cant breathe', "can't breathe",
        'slurred speech', 'stroke', 'unconscious', 'passed out', 'anaphylaxis', 'choking',
        'coughing blood', 'severe bleeding', 'overdose', 'poison', 'sudden numbness', 'loss of vision'
    ];

    function checkEmergencySymptoms(text) {
        if (!text) return false;
        const lower = text.toLowerCase();
        return EMERGENCY_KEYWORDS.some(kw => lower.includes(kw));
    }

    function openEmergencyModal() {
        if (emergencyModal) {
            emergencyModal.classList.add('open', 'active');
            emergencyModal.setAttribute('aria-hidden', 'false');
        }
    }

    function closeEmergencyModal() {
        if (emergencyModal) {
            emergencyModal.classList.remove('open', 'active');
            emergencyModal.setAttribute('aria-hidden', 'true');
        }
    }

    if (emergencyCloseBtn) emergencyCloseBtn.addEventListener('click', closeEmergencyModal);
    if (emergencyDismissBtn) emergencyDismissBtn.addEventListener('click', closeEmergencyModal);
    if (emergencyModal) {
        emergencyModal.addEventListener('click', (e) => {
            if (e.target === emergencyModal) closeEmergencyModal();
        });
    }

    // 1D. FIRST AID INTERACTIVE GUIDES
    const firstAidData = {
        cpr: {
            title: "🫀 CPR Steps (Cardiopulmonary Resuscitation)",
            steps: [
                { num: 1, title: "Check Safety & Responsiveness", desc: "Ensure scene safety. Tap shoulders firmly and shout: 'Are you OK?'. Check for breathing or chest rise." },
                { num: 2, title: "Call Emergency & Retrieve AED", desc: "Shout for someone to call 911 / 112 / 108 immediately and get an Automated External Defibrillator (AED)." },
                { num: 3, title: "Chest Compressions (100–120 bpm)", desc: "Place heel of hand on center of chest, interlock fingers. Push hard and fast (2–2.4 inches deep) to the beat of 'Stayin Alive'." },
                { num: 4, title: "Give 2 Rescue Breaths (If Trained)", desc: "After 30 compressions, tilt head back, lift chin, pinch nose and deliver 2 gentle breaths (1 sec each). Watch chest rise." },
                { num: 5, title: "Continue 30:2 Cycle", desc: "Continue uninterrupted cycles of 30 compressions and 2 breaths until emergency medical personnel arrive or AED is ready." }
            ]
        },
        choking: {
            title: "🗣️ Choking (Heimlich Maneuver / Back Blows)",
            steps: [
                { num: 1, title: "Assess Choking Severity", desc: "Ask 'Are you choking?'. If they can cough loudly or speak, encourage coughing. If silent or turning blue, act immediately." },
                { num: 2, title: "Give 5 Back Blows", desc: "Stand behind the victim, lean them forward, and strike firmly between the shoulder blades 5 times with heel of hand." },
                { num: 3, title: "Give 5 Abdominal Thrusts (Heimlich)", desc: "Wrap arms around waist. Place fist thumb-side just above navel. Grasp fist with other hand and thrust quickly inward and upward." },
                { num: 4, title: "Repeat 5 and 5 Cycle", desc: "Alternate between 5 back blows and 5 abdominal thrusts until the airway blockage clears." },
                { num: 5, title: "If Person Becomes Unresponsive", desc: "Lower them carefully to the ground, call emergency services immediately, and initiate CPR. Check mouth before breaths." }
            ]
        },
        burns: {
            title: "🔥 Burns & Scalds Immediate Care",
            steps: [
                { num: 1, title: "Cool with Running Water", desc: "Hold burned skin under cool running water for 15–20 minutes immediately. Never apply ice, butter, or oil." },
                { num: 2, title: "Remove Constrictive Items", desc: "Gently remove tight rings, watches, or clothing before swelling occurs. Do not peel clothing stuck directly to burned flesh." },
                { num: 3, title: "Cover Loosely with Clean Dressing", desc: "Cover with clean, non-stick sterile dressing or plastic wrap. Do not pop blisters as they prevent infection." },
                { num: 4, title: "Identify Severity", desc: "1st degree: red/painful. 2nd degree: blisters/swelling. 3rd degree: charred, white, or leathery (requires immediate ER)." },
                { num: 5, title: "Seek Emergency Care", desc: "Go to ER if burn is on face, hands, genitals, larger than patient's palm, or caused by chemicals or electricity." }
            ]
        },
        bleeding: {
            title: "🩸 Severe Bleeding & Hemorrhage Control",
            steps: [
                { num: 1, title: "Direct Continuous Pressure", desc: "Place a sterile gauze or clean cloth directly over the wound. Press firmly with both hands without letting up for 5–10 mins." },
                { num: 2, title: "Add Layers, Do Not Remove", desc: "If blood soaks through, do not lift off the cloth—place another layer directly on top and press harder to protect blood clotting." },
                { num: 3, title: "Elevate Limb Above Heart", desc: "If the injured limb has no broken bones, raise it above heart level to decrease blood flow." },
                { num: 4, title: "Use Tourniquet if Uncontrolled", desc: "For life-threatening limb bleeding, apply a commercial tourniquet 2–3 inches above wound (never over a joint) and tighten until bleeding halts." },
                { num: 5, title: "Prevent Shock", desc: "Keep patient lying flat, cover with a warm blanket, comfort them, and monitor breathing until paramedics arrive." }
            ]
        },
        fractures: {
            title: "🦴 Fractures & Musculoskeletal Injuries",
            steps: [
                { num: 1, title: "Keep Still & Immobilize", desc: "Do not attempt to straighten, push in, or move the injured bone or joint. Support in the exact position found." },
                { num: 2, title: "Apply R.I.C.E. for Sprains", desc: "Rest the joint, apply Ice wrapped in cloth (15 mins on/off), Compress gently with elastic wrap, and Elevate above heart level." },
                { num: 3, title: "Apply a Splint if Transporting", desc: "Pad a rigid object (board, folded newspaper) and tie securely above and below the injured area without cutting blood flow." },
                { num: 4, title: "Check Circulation & Sensation", desc: "Ensure fingers/toes are warm and pink. If pale, blue, or numb, loosen splint bindings immediately." },
                { num: 5, title: "Emergency Evaluation", desc: "Call for immediate help if bone penetrates skin (open fracture), severe deformity exists, or victim cannot feel digits." }
            ]
        },
        bites: {
            title: "🐍 Bites, Stings & Poisoning",
            steps: [
                { num: 1, title: "Snake Bites: Keep Calm & Still", desc: "Keep victim calm and still to slow venom spread. Keep bitten limb below heart level. Remove rings or constricting items." },
                { num: 2, title: "Snake Bite Don'ts", desc: "NEVER cut the wound, NEVER suck venom, NEVER apply ice or electric shock, and DO NOT apply a tight tourniquet." },
                { num: 3, title: "Bee/Wasp Stings", desc: "Scrape off visible stinger using a credit card edge (avoid squeezing venom sac with tweezers). Wash with soap and apply cold pack." },
                { num: 4, title: "Anaphylaxis & EpiPen", desc: "If patient has difficulty breathing, swollen tongue, or hives, administer prescribed EpiPen into outer thigh and dial emergency services." },
                { num: 5, title: "Animal Bites", desc: "Wash vigorously under warm soapy water for 5 minutes. Cover with clean bandage and visit emergency care for rabies/tetanus shots." }
            ]
        }
    };

    function renderFirstAidTab(tabKey) {
        const data = firstAidData[tabKey] || firstAidData['cpr'];
        if (!firstAidTabContent) return;

        let html = `<h4 style="margin-bottom: 16px; color: var(--accent-teal);">${data.title}</h4>`;
        data.steps.forEach(st => {
            html += `
                <div class="first-aid-step-item">
                    <div class="first-aid-step-num">${st.num}</div>
                    <div class="first-aid-step-content">
                        <h5>${st.title}</h5>
                        <p>${st.desc}</p>
                    </div>
                </div>
            `;
        });
        html += `
            <div style="margin-top: 18px; padding: 12px; background: rgba(239, 68, 68, 0.08); border-radius: 8px; font-size: 0.85rem; color: #ef4444;">
                ⚠️ <strong>Emergency Note:</strong> First aid is temporary stabilizing care. Always contact emergency services (911 / 112 / 108) immediately for life-threatening conditions.
            </div>
        `;
        firstAidTabContent.innerHTML = html;
    }

    if (firstAidBtn) {
        firstAidBtn.addEventListener('click', () => {
            if (firstAidModal) {
                firstAidModal.classList.add('open', 'active');
                firstAidModal.setAttribute('aria-hidden', 'false');
                renderFirstAidTab('cpr');
            }
        });
    }

    if (firstAidCloseBtn) {
        firstAidCloseBtn.addEventListener('click', () => {
            if (firstAidModal) {
                firstAidModal.classList.remove('open', 'active');
                firstAidModal.setAttribute('aria-hidden', 'true');
            }
        });
    }

    if (firstAidModal) {
        firstAidModal.addEventListener('click', (e) => {
            if (e.target === firstAidModal) {
                firstAidModal.classList.remove('open', 'active');
                firstAidModal.setAttribute('aria-hidden', 'true');
            }
        });
    }

    document.querySelectorAll('.fa-tab-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.querySelectorAll('.fa-tab-btn').forEach(b => b.classList.remove('active'));
            e.currentTarget.classList.add('active');
            renderFirstAidTab(e.currentTarget.dataset.tab);
        });
    });

    // 1E. DOCTOR VISIT PREPARATION SUMMARY
    if (doctorPrepBtn) {
        doctorPrepBtn.addEventListener('click', async () => {
            if (doctorPrepModal) {
                doctorPrepModal.classList.add('open', 'active');
                doctorPrepModal.setAttribute('aria-hidden', 'false');
            }
            if (doctorPrepBody) {
                doctorPrepBody.innerHTML = `
                    <div class="loading-dots" style="text-align: center; padding: 40px;">
                        <span></span><span></span><span></span>
                        <p style="margin-top: 14px; font-size: 0.9rem; color: var(--text-muted);">
                            Synthesizing medical consultation into a clinical doctor's intake summary...
                        </p>
                    </div>
                `;
            }

            try {
                const data = await chatApi.generateDoctorSummary(appState.conversationId, wizardData || {}, getSelectedLanguage());
                if (doctorPrepBody) {
                    doctorPrepBody.innerHTML = renderMarkdown(data.summary);
                }
            } catch (err) {
                if (doctorPrepBody) {
                    doctorPrepBody.innerHTML = `
                        <div style="color: var(--match-none-text); padding: 20px;">
                            <strong>Failed to generate summary:</strong> ${err.message}
                        </div>
                    `;
                }
            }
        });
    }

    if (doctorPrepCloseBtn) {
        doctorPrepCloseBtn.addEventListener('click', () => {
            if (doctorPrepModal) {
                doctorPrepModal.classList.remove('open', 'active');
                doctorPrepModal.setAttribute('aria-hidden', 'true');
            }
        });
    }

    if (doctorPrepModal) {
        doctorPrepModal.addEventListener('click', (e) => {
            if (e.target === doctorPrepModal) {
                doctorPrepModal.classList.remove('open', 'active');
                doctorPrepModal.setAttribute('aria-hidden', 'true');
            }
        });
    }

    if (printDoctorSummaryBtn) {
        printDoctorSummaryBtn.addEventListener('click', () => {
            window.print();
        });
    }

    if (copyDoctorSummaryBtn) {
        copyDoctorSummaryBtn.addEventListener('click', () => {
            if (doctorPrepBody) {
                navigator.clipboard.writeText(doctorPrepBody.innerText).then(() => {
                    copyDoctorSummaryBtn.textContent = '✅ Copied!';
                    setTimeout(() => { copyDoctorSummaryBtn.textContent = '📋 Copy Summary'; }, 2000);
                });
            }
        });
    }

    // 1F. DRUG-TO-DRUG INTERACTION CHECKER
    let selectedMedications = ['Aspirin', 'Ibuprofen'];

    function renderMedChips() {
        if (!selectedMedsChips) return;
        selectedMedsChips.innerHTML = '';
        selectedMedications.forEach((med, idx) => {
            const chip = document.createElement('div');
            chip.className = 'med-chip';
            chip.innerHTML = `
                <span>💊 ${med}</span>
                <button type="button" class="med-chip-remove" aria-label="Remove ${med}">&times;</button>
            `;
            chip.querySelector('.med-chip-remove').addEventListener('click', () => {
                selectedMedications.splice(idx, 1);
                renderMedChips();
            });
            selectedMedsChips.appendChild(chip);
        });
    }

    if (addMedBtn && medInput) {
        const handleAddMed = () => {
            const val = medInput.value.trim();
            if (val && !selectedMedications.includes(val)) {
                selectedMedications.push(val);
                medInput.value = '';
                renderMedChips();
            }
        };
        addMedBtn.addEventListener('click', handleAddMed);
        medInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                handleAddMed();
            }
        });
    }

    if (clearMedsBtn) {
        clearMedsBtn.addEventListener('click', () => {
            selectedMedications = [];
            renderMedChips();
            if (interactionsResultsFeed) {
                interactionsResultsFeed.innerHTML = '';
                interactionsResultsFeed.classList.add('hidden');
            }
            if (interactionsEmptyNotice) {
                interactionsEmptyNotice.classList.remove('hidden');
            }
        });
    }

    if (checkInteractionsBtn) {
        checkInteractionsBtn.addEventListener('click', async () => {
            if (selectedMedications.length < 2) {
                alert('Please add at least 2 medications to evaluate interactions.');
                return;
            }

            if (interactionsEmptyNotice) interactionsEmptyNotice.classList.add('hidden');
            if (interactionsResultsFeed) {
                interactionsResultsFeed.classList.remove('hidden');
                interactionsResultsFeed.innerHTML = `
                    <div class="loading-dots" style="text-align: center; padding: 40px;">
                        <span></span><span></span><span></span>
                        <p style="margin-top: 12px; font-size: 0.9rem; color: var(--text-muted);">
                            Cross-referencing pharmacology encyclopedia for interactions...
                        </p>
                    </div>
                `;
            }

            try {
                const data = await chatApi.checkDrugInteractions(selectedMedications, getSelectedLanguage());
                const riskClass = data.risk_level.toLowerCase().includes('high') ? 'risk-high' : 
                                  (data.risk_level.toLowerCase().includes('low') ? 'risk-low' : 'risk-moderate');

                let html = `
                    <div class="explorer-result-card" style="padding: 24px;">
                        <div class="interaction-risk-badge ${riskClass}">
                            ⚠️ Interaction Level: ${data.risk_level}
                        </div>
                        <div class="markdown-body">
                            ${renderMarkdown(data.analysis)}
                        </div>
                `;

                if (data.citations && data.citations.length > 0) {
                    html += `
                        <div style="margin-top: 16px; padding-top: 12px; border-top: 1px solid var(--border-subtle); font-size: 0.85rem; color: var(--text-muted);">
                            <strong>Encyclopedia Citations:</strong>
                            <ul style="margin-left: 20px; margin-top: 6px;">
                    `;
                    data.citations.forEach(c => {
                        html += `<li>${c.article_title} (Page ${c.page})</li>`;
                    });
                    html += `</ul></div>`;
                }

                html += `</div>`;
                if (interactionsResultsFeed) interactionsResultsFeed.innerHTML = html;
            } catch (err) {
                if (interactionsResultsFeed) {
                    interactionsResultsFeed.innerHTML = `
                        <div style="color: var(--match-none-text); padding: 20px;">
                            <strong>Interaction check failed:</strong> ${err.message}
                        </div>
                    `;
                }
            }
        });
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

        userInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                if (!appState.isLoading && (userInput.value.trim().length > 0 || currentAttachedFile)) {
                    if (composerForm.requestSubmit) {
                        composerForm.requestSubmit();
                    } else {
                        composerForm.dispatchEvent(new Event('submit', { cancelable: true }));
                    }
                }
            }
        });
    }

    // CHAT FORM SUBMIT (TEXT OR FILE REPORT)
    composerForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const text = userInput.value.trim();
        const lang = getSelectedLanguage();

        if (!text && !currentAttachedFile) return;
        if (appState.isLoading) return;

        // Check for Emergency Red-Flag Symptoms
        if (checkEmergencySymptoms(text)) {
            openEmergencyModal();
        }

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
    if (symptomWizardBtn) {
        symptomWizardBtn.addEventListener('click', () => {
            resetWizard();
            if (symptomWizardModal) {
                symptomWizardModal.classList.add('open', 'active');
                symptomWizardModal.setAttribute('aria-hidden', 'false');
            }
        });
    }

    if (wizardCloseBtn) {
        wizardCloseBtn.addEventListener('click', () => closeWizardModal());
    }

    const wizardNext1Btn = document.getElementById('wizard-next-1-btn');
    const wizardNext4Btn = document.getElementById('wizard-next-4-btn');

    if (wizardNext1Btn) {
        wizardNext1Btn.addEventListener('click', () => {
            goToWizardStep(2);
        });
    }

    if (wizardNext4Btn) {
        wizardNext4Btn.addEventListener('click', () => {
            goToWizardStep(5);
        });
    }

    if (symptomWizardModal) {
        symptomWizardModal.addEventListener('click', (e) => {
            if (e.target === symptomWizardModal) {
                closeWizardModal();
                return;
            }

            const optionBtn = e.target.closest('.wizard-option-btn');
            if (!optionBtn) return;

            // Step 1: Age Selection
            if (optionBtn.hasAttribute('data-age')) {
                document.querySelectorAll('#wizard-step-1 .wizard-option-btn[data-age]').forEach(b => b.classList.remove('selected'));
                optionBtn.classList.add('selected');
                wizardData.age = optionBtn.getAttribute('data-age');
            }
            // Step 1: Gender Selection
            else if (optionBtn.hasAttribute('data-gender')) {
                document.querySelectorAll('#wizard-step-1 .wizard-option-btn[data-gender]').forEach(b => b.classList.remove('selected'));
                optionBtn.classList.add('selected');
                wizardData.gender = optionBtn.getAttribute('data-gender');
            }
            // Step 2: Category Selection
            else if (optionBtn.hasAttribute('data-category')) {
                wizardData.category = optionBtn.getAttribute('data-category');
                goToWizardStep(3);
            } 
            // Step 3: Duration Selection
            else if (optionBtn.hasAttribute('data-duration')) {
                wizardData.duration = optionBtn.getAttribute('data-duration');
                goToWizardStep(4);
            } 
            // Step 4: Severity Selection
            else if (optionBtn.hasAttribute('data-severity')) {
                document.querySelectorAll('#wizard-step-4 .wizard-option-btn[data-severity]').forEach(b => b.classList.remove('selected'));
                optionBtn.classList.add('selected');
                wizardData.severity = optionBtn.getAttribute('data-severity');
            }
            // Step 4: Condition Selection (Multiple Checkboxes)
            else if (optionBtn.hasAttribute('data-condition')) {
                const cond = optionBtn.getAttribute('data-condition');
                if (cond === 'None') {
                    document.querySelectorAll('#wizard-step-4 .wizard-condition-btn').forEach(b => b.classList.remove('selected'));
                    optionBtn.classList.add('selected');
                    wizardData.conditions = ['None'];
                } else {
                    document.querySelectorAll('#wizard-step-4 .wizard-condition-btn[data-condition="None"]').forEach(b => b.classList.remove('selected'));
                    wizardData.conditions = wizardData.conditions.filter(c => c !== 'None');
                    
                    if (optionBtn.classList.contains('selected')) {
                        optionBtn.classList.remove('selected');
                        wizardData.conditions = wizardData.conditions.filter(c => c !== cond);
                    } else {
                        optionBtn.classList.add('selected');
                        if (!wizardData.conditions.includes(cond)) {
                            wizardData.conditions.push(cond);
                        }
                    }
                }
            }
        });
    }

    function goToWizardStep(stepNum) {
        for (let i = 1; i <= 5; i++) {
            const stepEl = document.getElementById(`wizard-step-${i}`);
            if (stepEl) {
                if (i === stepNum) {
                    stepEl.classList.remove('hidden');
                    stepEl.classList.add('active');
                } else {
                    stepEl.classList.remove('active');
                    stepEl.classList.add('hidden');
                }
            }
        }
    }

    function closeWizardModal() {
        if (symptomWizardModal) {
            symptomWizardModal.classList.remove('open', 'active');
            symptomWizardModal.setAttribute('aria-hidden', 'true');
        }
    }

    function resetWizard() {
        wizardData = { age: '', gender: '', category: '', duration: '', severity: '', conditions: [] };
        goToWizardStep(1);
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

            let profileParts = [];
            if (wizardData.age) profileParts.push(`age ${wizardData.age}`);
            if (wizardData.gender && wizardData.gender !== 'Unspecified') profileParts.push(wizardData.gender);
            const profileStr = profileParts.length > 0 ? `Patient Profile: ${profileParts.join(', ')}. ` : '';

            let conditionStr = '';
            if (wizardData.conditions.length > 0 && !wizardData.conditions.includes('None')) {
                conditionStr = ` Pre-existing health context: ${wizardData.conditions.join(', ')}.`;
            }

            let query = `${profileStr}Experiencing ${severity.toLowerCase()} ${category} symptoms for ${duration}.${conditionStr}`;
            if (notes) query += ` Specific details: ${notes}.`;
            query += ` What medical information, potential causes, and evidence-grounded guidance are available for this condition?`;

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
    if (headerNewChatBtn) headerNewChatBtn.addEventListener('click', () => startNewChatSession());
    if (sidebarNewChatBtn) sidebarNewChatBtn.addEventListener('click', () => startNewChatSession());

    function startNewChatSession() {
        switchView('chat');
        appState.startNewChat();
        if (userInput) {
            userInput.value = '';
            userInput.style.height = '44px';
            userInput.focus();
        }
        if (charCounter) charCounter.textContent = '0 / 2000';
        if (sendBtn) sendBtn.disabled = true;
        renderDynamicChatQuestions();
        closeMobileDrawer();
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
    if (disclaimerModalBtn) {
        disclaimerModalBtn.addEventListener('click', () => {
            if (safetyModal) {
                safetyModal.classList.add('open', 'active');
                safetyModal.setAttribute('aria-hidden', 'false');
            }
        });
    }

    if (modalCloseBtn) modalCloseBtn.addEventListener('click', () => closeSafetyModal());
    if (articleModalCloseBtn) articleModalCloseBtn.addEventListener('click', () => closeArticleModal());

    if (safetyModal) {
        safetyModal.addEventListener('click', (e) => {
            if (e.target === safetyModal) closeSafetyModal();
        });
    }

    if (articleDetailModal) {
        articleDetailModal.addEventListener('click', (e) => {
            if (e.target === articleDetailModal) closeArticleModal();
        });
    }

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeSafetyModal();
            closeArticleModal();
            closeWizardModal();
            closeEmergencyModal();
            if (firstAidModal) {
                firstAidModal.classList.remove('open', 'active');
                firstAidModal.setAttribute('aria-hidden', 'true');
            }
            if (doctorPrepModal) {
                doctorPrepModal.classList.remove('open', 'active');
                doctorPrepModal.setAttribute('aria-hidden', 'true');
            }
            closeMobileDrawer();
        }
    });

    function closeSafetyModal() {
        if (safetyModal) {
            safetyModal.classList.remove('open', 'active');
            safetyModal.setAttribute('aria-hidden', 'true');
        }
    }

    function closeArticleModal() {
        if (articleDetailModal) {
            articleDetailModal.classList.remove('open', 'active');
            articleDetailModal.setAttribute('aria-hidden', 'true');
        }
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
        articleDetailModal.classList.add('open', 'active');
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

                let isSpeaking = false;
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
                        if (isSpeaking) {
                            window.speechSynthesis.cancel();
                            isSpeaking = false;
                            speakBtn.querySelector('span').textContent = 'Read Aloud';
                            return;
                        }
                        window.speechSynthesis.cancel();
                        const textToRead = msg.content.replace(/[#*`_\[\]()]/g, '');
                        const utterance = new SpeechSynthesisUtterance(textToRead);
                        const lang = getSelectedLanguage();
                        utterance.lang = lang === 'Hindi' ? 'hi-IN' : (lang === 'Spanish' ? 'es-ES' : 'en-US');
                        utterance.onstart = () => {
                            isSpeaking = true;
                            speakBtn.querySelector('span').textContent = '⏹️ Stop';
                        };
                        utterance.onend = () => {
                            isSpeaking = false;
                            speakBtn.querySelector('span').textContent = 'Read Aloud';
                        };
                        utterance.onerror = () => {
                            isSpeaking = false;
                            speakBtn.querySelector('span').textContent = 'Read Aloud';
                        };
                        window.speechSynthesis.speak(utterance);
                    } else {
                        alert('Text-to-speech is not supported in this browser.');
                    }
                });

                // Helpful / Unhelpful Feedback Buttons
                const thumbsUp = document.createElement('button');
                thumbsUp.className = 'feedback-btn';
                thumbsUp.innerHTML = '👍 Helpful';
                thumbsUp.title = 'Rate answer as helpful';
                thumbsUp.addEventListener('click', () => {
                    thumbsUp.classList.toggle('active');
                    thumbsDown.classList.remove('active');
                    chatApi.sendFeedback({ conversation_id: appState.conversationId, rating: 1 });
                });

                const thumbsDown = document.createElement('button');
                thumbsDown.className = 'feedback-btn';
                thumbsDown.innerHTML = '👎 Needs Work';
                thumbsDown.title = 'Rate answer as unhelpful';
                thumbsDown.addEventListener('click', () => {
                    thumbsDown.classList.toggle('active');
                    thumbsUp.classList.remove('active');
                    chatApi.sendFeedback({ conversation_id: appState.conversationId, rating: -1 });
                });

                actionsBar.appendChild(copyBtn);
                actionsBar.appendChild(speakBtn);
                actionsBar.appendChild(thumbsUp);
                actionsBar.appendChild(thumbsDown);
                bubble.appendChild(actionsBar);

                // Smart contextual follow-up questions
                const followupsContainer = document.createElement('div');
                followupsContainer.className = 'smart-followups-container';
                followupsContainer.innerHTML = `<div class="smart-followup-title">💡 Suggested Follow-up Inquiries:</div>`;
                const followupsFlex = document.createElement('div');
                followupsFlex.className = 'smart-followups-flex';

                const suggestions = [
                    'What complications can occur with this?',
                    'What dietary or lifestyle changes help?',
                    'When should I see an in-person doctor?'
                ];

                suggestions.forEach(sug => {
                    const chip = document.createElement('button');
                    chip.type = 'button';
                    chip.className = 'followup-chip';
                    chip.textContent = sug;
                    chip.addEventListener('click', () => {
                        userInput.value = sug;
                        userInput.dispatchEvent(new Event('input'));
                        if (composerForm.requestSubmit) {
                            composerForm.requestSubmit();
                        } else {
                            composerForm.dispatchEvent(new Event('submit', { cancelable: true }));
                        }
                    });
                    followupsFlex.appendChild(chip);
                });
                followupsContainer.appendChild(followupsFlex);
                bubble.appendChild(followupsContainer);
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
                    userInput.dispatchEvent(new Event('input'));
                    if (composerForm.requestSubmit) {
                        composerForm.requestSubmit();
                    } else {
                        composerForm.dispatchEvent(new Event('submit', { cancelable: true }));
                    }
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

    function renderDynamicChatQuestions() {
        const grid = document.getElementById('example-prompts-grid');
        if (!grid) return;
        const questions = [
            { icon: '🩺', title: 'Hypertension Risks', text: 'What are the main causes and symptoms of high blood pressure?' },
            { icon: '🩸', title: 'Diabetes Management', text: 'Explain the key differences between Type 1 and Type 2 diabetes.' },
            { icon: '💊', title: 'Antibiotic Safety', text: 'What precautions should be taken when taking prescribed antibiotics?' },
            { icon: '🧠', title: 'Migraine vs Headache', text: 'How can you distinguish a common tension headache from a migraine?' }
        ];

        grid.innerHTML = '';
        questions.forEach(q => {
            const card = document.createElement('button');
            card.type = 'button';
            card.className = 'example-prompt-card';
            card.innerHTML = `
                <div class="prompt-icon">${q.icon}</div>
                <div class="prompt-content">
                    <div class="prompt-title">${q.title}</div>
                    <div class="prompt-desc">${q.text}</div>
                </div>
            `;
            card.addEventListener('click', () => {
                userInput.value = q.text;
                userInput.style.height = 'auto';
                userInput.dispatchEvent(new Event('input'));
                if (composerForm.requestSubmit) {
                    composerForm.requestSubmit();
                } else {
                    composerForm.dispatchEvent(new Event('submit', { cancelable: true }));
                }
            });
            grid.appendChild(card);
        });
    }

    function renderExplorerSuggestions() {
        const container = document.getElementById('scientific-pills-container');
        if (!container) return;
        const topics = [
            'Hypertension', 'Diabetes mellitus', 'Asthma', 'Pneumonia',
            'Migraine', 'Antibiotics', 'Cholesterol', 'Anemia', 'Ulcerative colitis', 'Caffeine'
        ];

        container.innerHTML = '';
        topics.forEach(topic => {
            const pill = document.createElement('button');
            pill.type = 'button';
            pill.className = 'citation-pill';
            pill.textContent = topic;
            pill.addEventListener('click', () => {
                if (explorerSearchInput) {
                    explorerSearchInput.value = topic;
                    explorerSearchForm.dispatchEvent(new Event('submit'));
                }
            });
            container.appendChild(pill);
        });
    }

    // INITIAL UI RENDERS ON LOAD
    updateUiState();
    renderConversationsNav();
    renderDynamicChatQuestions();
    renderExplorerSuggestions();
});
