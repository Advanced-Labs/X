document.addEventListener("DOMContentLoaded", async () => {
    try {
        const health = await API.getHealth();
        document.getElementById("version").textContent = `v${health.version}`;
    } catch (e) {
        document.getElementById("version").textContent = "offline";
    }

    try {
        const users = await API.getUsers();
        const usersList = document.getElementById("users-list");
        users.forEach(user => {
            const li = document.createElement("li");
            li.innerHTML = `<span>${user.name}</span><span class="email">${user.email}</span>`;
            usersList.appendChild(li);
        });
    } catch (e) {
        console.error("Failed to load users:", e);
    }

    try {
        const CATEGORIES = {1: "Electronics", 2: "Tools", 3: "Toys"};
        const items = await API.getItems();
        const itemsList = document.getElementById("items-list");
        items.forEach(item => {
            const li = document.createElement("li");
            const categoryName = CATEGORIES[item.category_id] || "Unknown";
            li.innerHTML = `<span>${item.name}</span><span class="category">${categoryName}</span><span class="price">$${item.price.toFixed(2)}</span>`;
            itemsList.appendChild(li);
        });
    } catch (e) {
        console.error("Failed to load items:", e);
    }
});
