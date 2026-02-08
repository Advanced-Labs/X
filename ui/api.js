const API_BASE = "/api";

async function fetchJSON(path) {
    const res = await fetch(`${API_BASE}${path}`);
    if (!res.ok) throw new Error(`API error: ${res.status}`);
    return res.json();
}

const API = {
    getHealth: () => fetchJSON("/health"),
    getUsers: () => fetchJSON("/users"),
    getUser: (id) => fetchJSON(`/users/${id}`),
    getItems: () => fetchJSON("/items"),
    getItemsByOwner: (ownerId) => fetchJSON(`/items/by-owner/${ownerId}`),
};
