(() => {
    for (const select of document.querySelectorAll('.page:not(.calendar-container) select')) {
        const empty = select.querySelector('option[value=""]');
        if (!empty || !/^-+$/.test(empty.textContent.trim())) continue;
        const label = select.labels[0]?.textContent.replace(/[:*]/g, '').trim().toLocaleLowerCase('vi');
        empty.textContent = label ? `Chọn ${label}…` : 'Chọn…';
    }
})();
