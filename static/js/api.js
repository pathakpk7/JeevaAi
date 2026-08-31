/**
 * Dedicated API Client for Medical Knowledge Assistant REST Endpoints.
 */

export const chatApi = {
    /**
     * Sends a chat message turn to POST /api/chat.
     * @param {string} message - User question string.
     * @param {string|null} conversationId - Active conversation session ID.
     * @param {string|null} language - Target response language.
     * @returns {Promise<Object>} Response object containing answer, sources, metrics.
     */
    async sendMessage(message, conversationId = null, language = 'English') {
        const payload = { message: message.trim(), language: language || 'English' };
        if (conversationId) {
            payload.conversation_id = conversationId;
        }

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(payload),
            });

            let data;
            try {
                data = await response.json();
            } catch (jsonErr) {
                const err = new Error(`Server returned error status ${response.status} (${response.statusText}).`);
                err.code = 'SERVER_ERROR';
                err.status = response.status;
                throw err;
            }

            if (!response.ok) {
                const errorCode = data.error?.code || 'API_ERROR';
                const errorMsg = data.error?.message || 'Failed to complete generation request.';
                const err = new Error(errorMsg);
                err.code = errorCode;
                err.status = response.status;
                throw err;
            }

            return data;
        } catch (error) {
            if (!error.status) {
                error.code = 'NETWORK_ERROR';
                error.message = 'Unable to connect to the medical knowledge server. Please verify that the Flask server (app.py) is running on http://127.0.0.1:5000.';
            }
            throw error;
        }
    },

    /**
     * Uploads custom medical report / lab PDF via POST /api/upload-report.
     * @param {File} file - PDF or TXT file object.
     * @param {string} language - Target language.
     * @returns {Promise<Object>} Extracted insights and analysis.
     */
    async uploadReport(file, language = 'English') {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('language', language || 'English');

        try {
            const response = await fetch('/api/upload-report', {
                method: 'POST',
                body: formData,
            });

            const data = await response.json();
            if (!response.ok) {
                const err = new Error(data.error?.message || 'Report processing failed.');
                err.code = data.error?.code || 'UPLOAD_ERROR';
                throw err;
            }
            return data;
        } catch (error) {
            console.error('Report upload error:', error);
            throw error;
        }
    },

    /**
     * Retrieves session message history via GET /api/chat/<conversation_id>.
     * @param {string} conversationId - Session ID.
     * @returns {Promise<Array>} Array of message objects.
     */
    async getHistory(conversationId) {
        if (!conversationId) return [];
        try {
            const response = await fetch(`/api/chat/${encodeURIComponent(conversationId)}`);
            if (!response.ok) return [];
            const data = await response.json();
            return data.messages || [];
        } catch (error) {
            console.warn('Failed to fetch session history from server:', error);
            return [];
        }
    },

    /**
     * Deletes a conversation session from backend memory via DELETE /api/chat/<conversation_id>.
     * @param {string} conversationId - Session ID to clear.
     * @returns {Promise<boolean>} Success boolean.
     */
    async deleteConversation(conversationId) {
        if (!conversationId) return false;
        try {
            const response = await fetch(`/api/chat/${encodeURIComponent(conversationId)}`, {
                method: 'DELETE',
            });
            return response.ok;
        } catch (error) {
            console.warn('Failed to delete session memory on server:', error);
            return false;
        }
    },

    /**
     * Executes Knowledge Explorer search query via GET /api/search?q=query&limit=10&mode=hybrid.
     * Performs fast knowledge base search without invoking LLM generation.
     * @param {string} query - Search query term.
     * @param {number} limit - Result count limit (default 10).
     * @param {string} mode - Search mode: 'hybrid', 'dense', or 'lexical'.
     * @returns {Promise<Object>} SearchResponse object containing results and latency.
     */
    async searchKnowledge(query, limit = 10, mode = 'hybrid') {
        const url = `/api/search?q=${encodeURIComponent(query.trim())}&limit=${limit}&mode=${encodeURIComponent(mode)}`;
        try {
            const response = await fetch(url);
            const data = await response.json();
            if (!response.ok) {
                const err = new Error(data.error?.message || 'Search request failed.');
                err.code = data.error?.code || 'SEARCH_ERROR';
                throw err;
            }
            return data;
        } catch (error) {
            console.error('Knowledge search error:', error);
            throw error;
        }
    },

    /**
     * Fast health check GET /api/health.
     */
    async checkHealth() {
        try {
            const response = await fetch('/api/health');
            return await response.json();
        } catch (error) {
            return { status: 'unreachable' };
        }
    }
};
