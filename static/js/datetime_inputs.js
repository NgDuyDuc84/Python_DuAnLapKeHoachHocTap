(() => {
    const picker = window.flatpickr;
    if (typeof picker !== "function" || !picker.l10ns.vn) return;
    picker.l10ns.vi = {
        ...picker.l10ns.vn,
        yearAriaLabel: "Năm", monthAriaLabel: "Tháng",
        hourAriaLabel: "Giờ", minuteAriaLabel: "Phút",
        scrollTitle: "Cuộn để thay đổi", toggleTitle: "Nhấn để đổi",
    };
    const formats = {
        date: ["Y-m-d", "d/m/Y", "dd/mm/yyyy"],
        time: ["H:i", "H:i", "HH:mm"],
        "datetime-local": ["Y-m-d\\TH:i", "d/m/Y H:i", "dd/mm/yyyy HH:mm"],
    };

    // Construct wall-clock values, without converting ISO input to/from UTC.
    function parse(value, format) {
        const clockOnly = format === "H:i";
        const iso = format.startsWith("Y");
        const match = (clockOnly ? /^(\d{2}):(\d{2})$/ : iso
            ? /^(\d{4})-(\d{2})-(\d{2})(?:T(\d{2}):(\d{2}))?$/
            : /^(\d{2})\/(\d{2})\/(\d{4})(?: (\d{2}):(\d{2}))?$/).exec(value.trim());
        if (!match || (!clockOnly && Boolean(match[4]) !== format.includes("H"))) return;
        const year = clockOnly ? 2000 : Number(match[iso ? 1 : 3]);
        const month = clockOnly ? 1 : Number(match[2]);
        const day = clockOnly ? 1 : Number(match[iso ? 3 : 1]);
        const hour = Number(match[clockOnly ? 1 : 4] || 0);
        const minute = Number(match[clockOnly ? 2 : 5] || 0);
        const date = new Date(0);
        date.setFullYear(year, month - 1, day);
        date.setHours(hour, minute, 0, 0);
        if (year > 0 && date.getFullYear() === year && date.getMonth() === month - 1 &&
            date.getDate() === day && date.getHours() === hour && date.getMinutes() === minute) return date;
    }

    const restoreInputs = [];
    for (const input of document.querySelectorAll('input[type="date"], input[type="time"], input[type="datetime-local"]')) {
        const type = input.type;
        const [iso, display, placeholder] = formats[type];
        const initialValue = input.value;
        if (initialValue && !parse(initialValue, iso)) continue;
        const attributes = Object.fromEntries(["type", "class", "readonly"].map(name => [name, input.getAttribute(name)]));
        const labels = [...input.labels];
        let instance;
        let invalidText = null;
        const message = `Vui lòng nhập đúng định dạng ${placeholder} và ngày, giờ hợp lệ.`;

        function restore(value = input.value) {
            const alternate = instance && instance.altInput;
            const calendar = instance && instance.calendarContainer;
            try { if (instance) instance.destroy(); } catch (_) { /* Restore native input even after a picker error. */ }
            if (alternate) alternate.remove();
            if (calendar) calendar.remove();
            for (const [name, original] of Object.entries(attributes)) {
                if (original === null) input.removeAttribute(name);
                else input.setAttribute(name, original);
            }
            input.value = value;
            for (const label of labels) label.htmlFor = input.id;
            delete input._flatpickr;
        }

        function updateValidity() {
            const field = instance.altInput;
            if (invalidText !== null && instance.selectedDates.length === 0) field.value = invalidText;
            else invalidText = null;
            field.setCustomValidity(invalidText !== null || (field.required && !field.value) ? message : "");
        }

        try {
            const result = picker(input, {
                locale: "vi", altInput: true, allowInput: true,
                dateFormat: iso, altFormat: display, ariaDateFormat: "d/m/Y",
                enableTime: type !== "date", noCalendar: type === "time",
                time_24hr: true, minuteIncrement: 1, disableMobile: true,
                parseDate: parse,
                errorHandler: error => { if (invalidText === null) throw error; },
                onParseConfig: (_dates, _value, ready) => { instance = ready; },
                onValueUpdate: updateValidity,
                onChange: updateValidity,
                onClose: updateValidity,
            });
            if (!result.altInput || getComputedStyle(result.calendarContainer).position !== "absolute") {
                throw new Error("Date picker is unavailable");
            }
            instance = result;
            const field = instance.altInput;
            field.id = `${input.id}_display`;
            field.dataset.datetimeDisplay = type;
            field.placeholder = placeholder;
            field.readOnly = input.readOnly;
            for (const name of ["aria-describedby", "aria-invalid", "aria-labelledby", "aria-label"]) {
                if (input.hasAttribute(name)) field.setAttribute(name, input.getAttribute(name));
            }
            for (const label of labels) label.htmlFor = field.id;
            field.addEventListener("input", () => {
                try {
                    const value = field.value.trim();
                    const date = value ? parse(value, display) : null;
                    invalidText = value && !date ? field.value : null;
                    if (invalidText !== null) field.setCustomValidity(message);
                    else if (date) instance.setDate(date, true);
                    else instance.clear(true);
                } catch (_) { restore(); }
            });
            updateValidity();
            restoreInputs.push(restore);
        } catch (_) {
            restore(initialValue);
        }
    }
    window.addEventListener("error", event => {
        if (/(flatpickr(?:\.min)?|datetime_inputs)\.js(?:\?|$)/.test(event.filename || "")) {
            for (const restore of restoreInputs) restore();
        }
    });
})();
