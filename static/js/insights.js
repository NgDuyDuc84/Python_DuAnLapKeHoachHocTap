(() => {
    // A dialog belongs to the adjacent trigger, including evidence repeated on several cards.
    document.addEventListener("click", (event) => {
        const opener = event.target.closest("[data-dialog-open]");
        if (opener) {
            const dialog = opener.parentElement.querySelector("dialog");
            opener.focus();
            dialog.addEventListener("close", () => opener.focus(), { once: true });
            dialog.showModal();
        }
        if (event.target.closest("[data-dialog-close]")) event.target.closest("dialog").close();
    });

    for (const panel of document.querySelectorAll(".ai-request")) {
        const form = panel.querySelector("[data-ai-form]");
        const consent = form.elements.consent;
        const token = form.elements.preview;
        const submit = form.querySelector("[data-ai-submit]");
        const quota = form.querySelector("[data-remaining]");
        const previewBody = panel.querySelector("[data-preview-body]");
        let loading = false;

        function syncButton() {
            submit.disabled = !consent.checked || consent.matches(":disabled") || !token.value || Number(quota.dataset.remaining) < 1;
        }

        async function preparePreview() {
            if (!panel.dataset.previewUrl || loading) return;
            loading = true;
            try {
                const response = await fetch(panel.dataset.previewUrl, { cache: "no-store" });
                if (!response.ok) throw new Error("preview");
                const page = new DOMParser().parseFromString(await response.text(), "text/html");
                const controls = page.querySelector("[data-ai-form]");
                if (!controls?.elements.preview.value) throw new Error("preview");
                const freshQuota = controls.querySelector("[data-remaining]");
                token.value = controls.elements.preview.value;
                quota.dataset.remaining = freshQuota.dataset.remaining;
                quota.textContent = freshQuota.textContent;
                consent.disabled = controls.elements.consent.matches(":disabled");
                previewBody.replaceChildren(...page.querySelector("[data-preview-body]").childNodes);
                delete panel.dataset.previewUrl;
                panel.querySelector("[data-preview-error]").hidden = true;
            } catch {
                consent.checked = false;
                previewBody.textContent = "Không tải được bản xem trước. Hãy đóng rồi mở lại.";
                panel.querySelector("[data-preview-error]").hidden = false;
            } finally {
                loading = false;
                syncButton();
            }
        }
        panel.querySelector("[data-dialog-open]").addEventListener("click", preparePreview);
        consent.addEventListener("change", () => {
            if (consent.checked) preparePreview();
            syncButton();
        });
        window.addEventListener("pageshow", syncButton);
        syncButton();
    }
})();
