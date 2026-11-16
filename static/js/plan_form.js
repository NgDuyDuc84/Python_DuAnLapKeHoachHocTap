(() => {
    const mode = document.getElementById("id_mode");
    const help = document.getElementById("plan-mode-help");
    if (!mode || !help) return;
    const update = () => {
        const explanation = document.getElementById(`plan-mode-${mode.value || "add"}`);
        if (explanation) help.textContent = explanation.textContent.trim();
    };
    mode.setAttribute("aria-describedby", help.id);
    mode.addEventListener("change", update);
    update();
})();
