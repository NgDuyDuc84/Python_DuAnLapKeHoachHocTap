(() => {
    const menus = [...document.querySelectorAll(".header-menu")];
    const navigation = document.querySelector(".header-nav-menu");
    const desktop = window.matchMedia("(min-width: 800px)");
    const collapsible = (menu) => menu !== navigation || !desktop.matches;
    const close = (menu) => { if (collapsible(menu)) menu.open = false; };
    const backlog = document.querySelector(".week-backlog");
    if (backlog) {
        const wideCalendar = window.matchMedia("(min-width: 1100px)");
        const resizeBacklog = () => { backlog.open = wideCalendar.matches; };
        wideCalendar.addEventListener("change", resizeBacklog);
        resizeBacklog();
    }
    if (navigation) {
        const resize = () => { navigation.open = desktop.matches; };
        desktop.addEventListener("change", resize);
        resize();
        navigation.addEventListener("click", (event) => {
            if (event.target.closest("a")) close(navigation);
        });
    }
    for (const menu of menus) {
        menu.addEventListener("toggle", () => {
            if (menu === navigation) menu.querySelector("summary").setAttribute("aria-expanded", String(menu.open));
            if (menu.open) {
                for (const other of menus) {
                    if (other !== menu) close(other);
                }
            }
        });
    }
    document.addEventListener("click", (event) => {
        for (const menu of menus) {
            if (!menu.contains(event.target)) close(menu);
        }
    });
    document.addEventListener("keydown", (event) => {
        if (event.key !== "Escape") return;
        const opened = menus.find((menu) => menu.open && collapsible(menu));
        if (opened) {
            opened.open = false;
            opened.querySelector("summary").focus();
        }
    });
})();
