/* ──────────────────────────────────────────────────────
   Shared interactive calendar with month navigation.
   
   Usage:
     renderCalendar(bookingsArray, 'element-id');
   
   Each booking object should have:
     date        – 'YYYY-MM-DD'
     eventName   – string (optional)
     club        – string (optional)
     hallName    – string (optional)
     hall.name   – string (fallback)
     startTime   – string (optional)
     status      – ignored (only approved ones should be passed)
────────────────────────────────────────────────────── */

const _calState = {};  // keyed by targetId: { year, month, bookings }

function renderCalendar(bookings, targetId = 'calendar-view') {
    const calendarEl = document.getElementById(targetId);
    if (!calendarEl) return;

    // Initialise state if first render
    if (!_calState[targetId]) {
        const now = new Date();
        _calState[targetId] = { year: now.getFullYear(), month: now.getMonth(), bookings };
    } else {
        // Always refresh bookings data
        _calState[targetId].bookings = bookings;
    }

    _drawCalendar(targetId);
}

function _drawCalendar(targetId) {
    const calendarEl = document.getElementById(targetId);
    if (!calendarEl) return;

    const { year, month, bookings } = _calState[targetId];

    const today = new Date();
    const firstDay = new Date(year, month, 1).getDay();
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    const monthName = new Date(year, month, 1).toLocaleString('default', { month: 'long' });

    let html = `
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
            <button onclick="_calPrev('${targetId}')" style="border: none; background: var(--bg-main); border-radius: 50%; width: 32px; height: 32px; cursor: pointer; font-size: 1rem; color: var(--primary); display: flex; align-items: center; justify-content: center;">&#8249;</button>
            <h3 style="margin: 0; font-family: Poppins, sans-serif; font-size: 1.1rem;">${monthName} ${year}</h3>
            <button onclick="_calNext('${targetId}')" style="border: none; background: var(--bg-main); border-radius: 50%; width: 32px; height: 32px; cursor: pointer; font-size: 1rem; color: var(--primary); display: flex; align-items: center; justify-content: center;">&#8250;</button>
        </div>
        <div style="display: grid; grid-template-columns: repeat(7, 1fr); gap: 4px; text-align: center;">
            ${['Sun','Mon','Tue','Wed','Thu','Fri','Sat'].map(d => `<div style="font-weight: 600; font-size: 0.72rem; color: var(--primary); padding: 0.2rem 0; letter-spacing: 0.04em;">${d}</div>`).join('')}
    `;

    // Empty cells for first row padding
    for (let i = 0; i < firstDay; i++) {
        html += `<div></div>`;
    }

    for (let day = 1; day <= daysInMonth; day++) {
        const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
        const dayBookings = bookings.filter(b => b.date === dateStr);
        const isBooked = dayBookings.length > 0;
        const hasOnlyMaintenance = isBooked && dayBookings.every((entry) => entry.entryType === 'maintenance');
        const isToday = (day === today.getDate() && month === today.getMonth() && year === today.getFullYear());

        // Build a plain-text tooltip list
        const tooltipLines = isBooked
            ? dayBookings.map(b => {
                const label = b.entryType === 'maintenance'
                    ? (b.title || b.eventName || 'Maintenance')
                    : (b.eventName || 'Event');
                const scope = b.entryType === 'maintenance'
                    ? 'Maintenance'
                    : (b.club && b.club !== 'None' ? `(${b.club})` : '');
                return `${label}${scope ? ' ' + scope : ''} @ ${b.hallName || b.hall?.name || 'Hall'} [${b.startTime || ''}]`;
            }).join('\n')
            : '';

        // Build event name labels (show up to 2 event names + overflow indicator)
        let eventLabelsHtml = '';
        if (isBooked) {
            const maxShow = 2;
            const shown = dayBookings.slice(0, maxShow);
            eventLabelsHtml = shown.map(b => {
                const isMaintenance = b.entryType === 'maintenance';
                const label = isMaintenance ? (b.title || b.eventName || 'Maintenance') : (b.eventName || 'Booked');
                const background = isMaintenance ? '#d97706' : 'var(--primary)';
                return `<div style="font-size: 0.65rem; font-weight: 600; color: white; background: ${background}; border-radius: 3px; padding: 1px 4px; margin-top: 2px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; line-height: 1.3;">${label}</div>`;
            }).join('');
            if (dayBookings.length > maxShow) {
                eventLabelsHtml += `<div style="font-size: 0.58rem; color: var(--primary); font-weight: 600; margin-top: 1px;">+${dayBookings.length - maxShow} more</div>`;
            }
        }

        html += `
            <div
                style="padding: 4px 3px; min-height: 52px; border-radius: 6px; position: relative;
                    background: ${isBooked ? (hasOnlyMaintenance ? 'rgba(217,119,6,0.08)' : 'rgba(29,78,216,0.06)') : isToday ? 'rgba(29,78,216,0.04)' : 'transparent'};
                    border: 1.5px solid ${isBooked ? (hasOnlyMaintenance ? 'rgba(217,119,6,0.7)' : 'var(--primary)') : isToday ? 'rgba(29,78,216,0.3)' : 'transparent'};
                    cursor: ${isBooked ? 'pointer' : 'default'};"
                ${isBooked ? `title="${tooltipLines.replace(/"/g, '&quot;')}"` : ''}
            >
                <span style="font-size: 0.82rem; font-weight: ${isToday ? '700' : '400'}; color: ${isToday ? 'var(--primary)' : 'var(--text-main)'};">${day}</span>
                ${eventLabelsHtml}
            </div>
        `;
    }

    html += `</div>`;
    calendarEl.innerHTML = html;
}

function _calPrev(targetId) {
    const s = _calState[targetId];
    if (!s) return;
    s.month -= 1;
    if (s.month < 0) { s.month = 11; s.year -= 1; }
    _drawCalendar(targetId);
}

function _calNext(targetId) {
    const s = _calState[targetId];
    if (!s) return;
    s.month += 1;
    if (s.month > 11) { s.month = 0; s.year += 1; }
    _drawCalendar(targetId);
}
