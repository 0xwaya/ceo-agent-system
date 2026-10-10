// Apply CSRF protection to the existing same-origin dashboard request paths.
const originalFetch = window.fetch.bind(window);
window.fetch = async (resource, options = {}) => {
    const url = new URL(resource instanceof Request ? resource.url : resource, location.href);
    const method = (options.method || (resource instanceof Request ? resource.method : 'GET')).toUpperCase();
    if (url.origin === location.origin && !['GET', 'HEAD', 'OPTIONS'].includes(method)) {
        const headers = new Headers(options.headers || (resource instanceof Request ? resource.headers : {}));
        headers.set('X-CSRF-Token', document.querySelector('meta[name="csrf-token"]').content);
        options = { ...options, headers };
    }
    const response = await originalFetch(resource, options);
    if (url.origin === location.origin && response.status === 401) location.assign('/login');
    return response;
};
