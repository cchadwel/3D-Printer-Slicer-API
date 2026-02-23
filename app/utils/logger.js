/**
 * Structured error logger (console-only).
 */

function logError(errorData) {
    const entry = {
        timestamp: new Date().toISOString(),
        error: errorData?.message || 'Unknown Error',
        details: errorData?.stderr || errorData?.stack || 'No details',
        path: errorData?.path || 'N/A'
    };

    console.error('[ERROR LOG]', JSON.stringify(entry));
}

module.exports = {
    logError
};