/**
 * Application Configuration
 * Reads from environment variables with sensible defaults
 */

const config = {
    // API Base URL - defaults to localhost for development
    apiBaseUrl: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',

    // API Endpoints
    api: {
        analyzeText: '/api/analyze/text',
        analyzeFile: '/api/analyze/file',
        analyzeStream: '/api/analyze/stream',
        history: '/api/history',
    },

    // Request timeouts (in milliseconds)
    timeouts: {
        default: 300000, // 5 minutes for analysis
        stream: 600000,  // 10 minutes for streaming
    },

    // Development mode
    isDevelopment: import.meta.env.DEV,
    isProduction: import.meta.env.PROD,
};

export default config;
