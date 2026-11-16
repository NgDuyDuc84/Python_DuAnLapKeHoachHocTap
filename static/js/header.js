(() => {
    const menus = [...document.querySelectorAll(".header-menu")];
    for (const menu of menus) {
        menu.addEventListener("toggle", () => {
            if (menu.open) {
                for (const other of menus) {
                    if (other !== menu) other.open = false;
                }
            }
        });
    }
    document.addEventListener("click", (event) => {
        for (const menu of menus) {
            if (!menu.contains(event.target)) menu.open = false;
        }
    });
    document.addEventListener("keydown", (event) => {
        if (event.key !== "Escape") return;
        const opened = menus.find((menu) => menu.open);
        if (opened) {
            opened.open = false;
            opened.querySelector("summary").focus();
        }
    });
})();
