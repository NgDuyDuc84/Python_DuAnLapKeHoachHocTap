(() => {
    const clock = document.getElementById("focus-timer");
    const initial = document.getElementById("timer-state");
    if (!clock || !initial) return;
    let state = JSON.parse(initial.textContent);
    let anchoredAt = performance.now();
    const initialStatus = state.status;
    const message = document.getElementById("timer-message");
    const syncMessage = document.getElementById("timer-sync");
    const draw = () => {
        const passed = state.status === "running" ? Math.floor((performance.now() - anchoredAt) / 1000) : 0;
        const remaining = Math.max(0, state.remaining - passed);
        clock.textContent = `${String(Math.floor(remaining / 60)).padStart(2, "0")}:${String(remaining % 60).padStart(2, "0")}`;
        document.getElementById("timer-status").textContent = state.status_label;
        if (!remaining && (state.status === "running" || state.status === "paused")) {
            const expiredMessage = "Đã hết giờ. Bấm lưu/kết thúc để xác nhận phiên.";
            if (message.textContent !== expiredMessage) message.textContent = expiredMessage;
        }
    };
    const sync = async () => {
        try {
            const response = await fetch(clock.dataset.stateUrl, {cache: "no-store", headers: {Accept: "application/json"}});
            if (!response.ok || !response.headers.get("content-type")?.includes("application/json")) throw new Error();
            state = await response.json();
            anchoredAt = performance.now();
            syncMessage.textContent = state.status !== initialStatus ? "Phiên đã được cập nhật. Tải lại trang để xem các thao tác mới." : "";
            draw();
        } catch {
            syncMessage.textContent = "Chưa đồng bộ được trạng thái. Kết nối lại hoặc tải lại trang trước khi lưu.";
        }
    };
    draw();
    if (state.status === "running" || state.status === "paused") {
        setInterval(draw, 1000);
        setInterval(sync, 15000);
        document.addEventListener("visibilitychange", () => { if (!document.hidden) sync(); });
    }
})();
