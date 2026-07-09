function getCookie(name) {
    return document.cookie
        .split("; ")
        .find(row => row.startsWith(name + "="))
        ?.split("=")[1];
}

function getCsrfHeaders(method) {
    const normalizedMethod = (method || "GET").toUpperCase();
    const token = decodeURIComponent(getCookie("XSRF-TOKEN") || "");

    if (isSafeMethod(normalizedMethod) || !token) {
        return {};
    }

    return { "X-XSRF-TOKEN": token };
}

const nativeFetch = window.fetch.bind(window);

function isSameOriginRequest(input) {
    const url = typeof input === "string" ? input : input.url;
    return new URL(url, window.location.origin).origin === window.location.origin;
}

function isAuthEndpoint(input, endpoint) {
    const url = typeof input === "string" ? input : input.url;
    return new URL(url, window.location.origin).pathname === endpoint;
}

function isSafeMethod(method) {
    return ["GET", "HEAD", "OPTIONS", "TRACE"].includes((method || "GET").toUpperCase());
}

async function ensureCsrfToken(method) {
    if (isSafeMethod(method) || getCookie("XSRF-TOKEN")) {
        return;
    }

    await nativeFetch("/api/auth/csrf", {
        method: "GET",
        credentials: "same-origin"
    });
}

window.fetch = async function securedFetch(input, options = {}) {
    const method = (options.method || "GET").toUpperCase();
    const sameOrigin = isSameOriginRequest(input);
    if (sameOrigin) {
        await ensureCsrfToken(method);
    }

    const requestOptions = sameOrigin
        ? {
            ...options,
            method,
            credentials: options.credentials || "same-origin",
            headers: {
                ...(options.headers || {}),
                ...getCsrfHeaders(method)
            }
        }
        : options;

    let res = await nativeFetch(input, requestOptions);
    if (sameOrigin && !isSafeMethod(method) && res.status === 403) {
        await nativeFetch("/api/auth/csrf", {
            method: "GET",
            credentials: "same-origin"
        });
        res = await nativeFetch(input, {
            ...requestOptions,
            headers: {
                ...(options.headers || {}),
                ...getCsrfHeaders(method)
            }
        });
    }

    const canRefresh = sameOrigin
        && res.status === 401
        && !isAuthEndpoint(input, "/api/auth/login")
        && !isAuthEndpoint(input, "/api/auth/refresh")
        && !isAuthEndpoint(input, "/api/auth/logout");

    if (canRefresh && await refreshAuthSession()) {
        res = await nativeFetch(input, {
            ...requestOptions,
            headers: {
                ...(options.headers || {}),
                ...getCsrfHeaders(method)
            }
        });
    }

    return res;
};

function logoutClient() {
    localStorage.removeItem("accessToken");
    localStorage.removeItem("refreshToken");
    localStorage.removeItem("userRole");
    localStorage.removeItem("userId");
    window.location.href = "/login";
}

async function refreshAuthSession() {
    await ensureCsrfToken("POST");
    const res = await nativeFetch("/api/auth/refresh", {
        method: "POST",
        credentials: "same-origin",
        headers: getCsrfHeaders("POST")
    });
    return res.ok;
}

async function authFetch(url, options = {}) {
    const method = (options.method || "GET").toUpperCase();
    const headers = {
        ...(options.headers || {}),
        ...getCsrfHeaders(method)
    };

    const requestOptions = {
        ...options,
        method,
        credentials: "same-origin",
        headers
    };

    try {
        const res = await fetch(url, requestOptions);
        if (res.status === 401 || res.status === 403) {
            logoutClient();
        }
        return res;
    } catch (err) {
        console.error("Request failed:", err);
        logoutClient();
    }
}

async function logout() {
    try {
        await ensureCsrfToken("POST");
        await nativeFetch("/api/auth/logout", {
            method: "POST",
            credentials: "same-origin",
            headers: getCsrfHeaders("POST")
        });
    } catch (err) {
        console.error("Logout error:", err);
    } finally {
        logoutClient();
    }
}




