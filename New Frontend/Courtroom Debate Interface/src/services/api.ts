/**
 * API Client for Project AETHER Backend
 * Handles all communication with the backend API
 */

import config from '../config/config';

export interface AnalyzeTextRequest {
    text: string;
    show_updates?: boolean;
}

export interface AnalyzeFileRequest {
    file: File;
    show_updates?: boolean;
}

export interface BackendResponse {
    success: boolean;
    factors?: any[];
    validation_results?: any;
    debates?: any;
    synthesis?: any;
    final_report?: any;
    assumptions?: any[];
    resolutions?: {
        accepted: string[];
        partially_accepted: string[];
        rejected: string[];
    };
    integrity_check?: any;
    integrity_report?: any;
    all_messages?: any[];
    registry?: any;
    error?: string;
    analysis_id?: number;
}

export interface ProgressUpdate {
    stage: string;
    message: string;
    data?: any;
}

export type ProgressCallback = (update: ProgressUpdate) => void;

class APIClient {
    private baseUrl: string;

    constructor() {
        this.baseUrl = config.apiBaseUrl;
    }

    /**
     * Analyze text input
     */
    async analyzeText(request: AnalyzeTextRequest): Promise<BackendResponse> {
        try {
            const response = await fetch(`${this.baseUrl}${config.api.analyzeText}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(request),
                signal: AbortSignal.timeout(config.timeouts.default),
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            if (error instanceof Error) {
                if (error.name === 'TimeoutError') {
                    throw new Error('Analysis request timed out. Please try with a shorter text.');
                }
                throw error;
            }
            throw new Error('An unexpected error occurred during analysis');
        }
    }

    /**
     * Analyze uploaded file
     */
    async analyzeFile(request: AnalyzeFileRequest): Promise<BackendResponse> {
        try {
            const formData = new FormData();
            formData.append('file', request.file);
            formData.append('show_updates', String(request.show_updates ?? true));

            const response = await fetch(`${this.baseUrl}${config.api.analyzeFile}`, {
                method: 'POST',
                body: formData,
                signal: AbortSignal.timeout(config.timeouts.default),
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            if (error instanceof Error) {
                if (error.name === 'TimeoutError') {
                    throw new Error('File analysis request timed out. Please try with a smaller file.');
                }
                throw error;
            }
            throw new Error('An unexpected error occurred during file analysis');
        }
    }

    /**
     * Stream analysis with real-time updates via Server-Sent Events (SSE)
     */
    async analyzeStream(
        text: string,
        onProgress: ProgressCallback,
        onComplete: (result: BackendResponse) => void,
        onError: (error: Error) => void
    ): Promise<() => void> {
        const sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        const url = `${this.baseUrl}${config.api.analyzeStream}/${sessionId}?text=${encodeURIComponent(text)}&show_updates=true`;

        let eventSource: EventSource | null = null;

        try {
            eventSource = new EventSource(url);

            eventSource.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);

                    switch (data.event) {
                        case 'connected':
                            onProgress({
                                stage: 'connection',
                                message: data.data.message || 'Connected to server',
                            });
                            break;

                        case 'progress':
                            onProgress(data.data);
                            break;

                        case 'complete':
                            onComplete(data.data);
                            eventSource?.close();
                            break;

                        case 'error':
                            onError(new Error(data.data.error || 'Unknown error occurred'));
                            eventSource?.close();
                            break;

                        default:
                            console.warn('Unknown SSE event type:', data.event);
                    }
                } catch (error) {
                    console.error('Error parsing SSE message:', error);
                }
            };

            eventSource.onerror = (error) => {
                console.error('SSE connection error:', error);
                onError(new Error('Connection to server lost. Please try again.'));
                eventSource?.close();
            };

            // Return cleanup function
            return () => {
                if (eventSource) {
                    eventSource.close();
                }
            };
        } catch (error) {
            if (error instanceof Error) {
                onError(error);
            } else {
                onError(new Error('Failed to establish streaming connection'));
            }

            // Return no-op cleanup function
            return () => { };
        }
    }

    /**
     * Get analysis history
     */
    async getHistory(limit: number = 50): Promise<any[]> {
        try {
            const response = await fetch(`${this.baseUrl}${config.api.history}?limit=${limit}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                },
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            return data.history || [];
        } catch (error) {
            console.error('Error fetching history:', error);
            return [];
        }
    }

    /**
     * Get specific analysis by ID
     */
    async getAnalysis(analysisId: number): Promise<BackendResponse | null> {
        try {
            const response = await fetch(`${this.baseUrl}${config.api.history}/${analysisId}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                },
            });

            if (!response.ok) {
                if (response.status === 404) {
                    return null;
                }
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error fetching analysis:', error);
            return null;
        }
    }

    /**
     * Check if backend is available
     */
    async healthCheck(): Promise<boolean> {
        try {
            const response = await fetch(`${this.baseUrl}/`, {
                method: 'GET',
                signal: AbortSignal.timeout(5000),
            });
            return response.ok;
        } catch (error) {
            return false;
        }
    }
}

// Export singleton instance
export const apiClient = new APIClient();
export default apiClient;
