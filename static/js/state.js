/**
 * Frontend State Management module with localStorage session tracking.
 */

const LOCAL_STORAGE_KEY = 'med_assistant_recent_chats_v1';

class AppState {
    constructor() {
        this.conversationId = null;
        this.messages = [];
        this.conversations = this._loadConversationsFromStorage();
        this.isLoading = false;
        this.error = null;
        this.listeners = [];
    }

    subscribe(listener) {
        this.listeners.push(listener);
        return () => {
            this.listeners = this.listeners.filter(l => l !== listener);
        };
    }

    notify() {
        this.listeners.forEach(listener => listener(this));
    }

    startNewChat() {
        this.conversationId = null;
        this.messages = [];
        this.isLoading = false;
        this.error = null;
        this.notify();
    }

    selectConversation(id) {
        this.conversationId = id;
        const conv = this.conversations.find(c => c.id === id);
        this.messages = (conv && conv.messages) ? [...conv.messages] : [];
        this.isLoading = false;
        this.error = null;
        this.notify();
    }

    addMessage(msgObj) {
        this.messages.push(msgObj);
        if (this.conversationId) {
            this.updateCurrentConversationRecord();
        }
        this.notify();
    }

    updateCurrentConversationRecord() {
        if (!this.conversationId) return;
        const existingIdx = this.conversations.findIndex(c => c.id === this.conversationId);
        if (existingIdx >= 0) {
            this.conversations[existingIdx].messages = [...this.messages];
            this.conversations[existingIdx].updatedAt = Date.now();
            this._saveConversationsToStorage();
        }
    }

    setLoading(loadingState) {
        this.isLoading = loadingState;
        this.notify();
    }

    setError(errObj) {
        this.error = errObj;
        this.notify();
    }

    clearError() {
        this.error = null;
        this.notify();
    }

    saveCurrentConversationTitle(firstUserMessage) {
        if (!this.conversationId) return;

        const title = firstUserMessage.length > 32 
            ? firstUserMessage.substring(0, 32) + '...' 
            : firstUserMessage;

        const existingIdx = this.conversations.findIndex(c => c.id === this.conversationId);
        const record = {
            id: this.conversationId,
            title: title,
            messages: [...this.messages],
            updatedAt: Date.now()
        };

        if (existingIdx >= 0) {
            this.conversations[existingIdx] = record;
        } else {
            this.conversations.unshift(record);
        }

        // Keep maximum 15 recent conversations in local browser storage
        this.conversations = this.conversations.slice(0, 15);
        this._saveConversationsToStorage();
        this.notify();
    }

    removeConversation(id) {
        this.conversations = this.conversations.filter(c => c.id !== id);
        this._saveConversationsToStorage();
        if (this.conversationId === id) {
            this.startNewChat();
        } else {
            this.notify();
        }
    }

    _loadConversationsFromStorage() {
        try {
            const raw = localStorage.getItem(LOCAL_STORAGE_KEY);
            return raw ? JSON.parse(raw) : [];
        } catch (e) {
            return [];
        }
    }

    _saveConversationsToStorage() {
        try {
            localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(this.conversations));
        } catch (e) {
            console.warn('LocalStorage quota exceeded or disabled.');
        }
    }
}

export const appState = new AppState();
