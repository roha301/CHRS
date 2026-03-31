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
        const isToday = (day === today.getDate() && month === today.getMonth() && year === today.getFullYear());

        // Build a plain-text tooltip list
        const tooltipLines = isBooked
            ? dayBookings.map(b => `${b.eventName || 'Event'}${b.club && b.club !== 'None' ? ' (' + b.club + ')' : ''} @ ${b.hallName || b.hall?.name || 'Hall'} [${b.startTime || ''}]`).join('\n')
            : '';

        html += `
            <div
                style="padding: 6px 2px; min-height: 44px; border-radius: 6px; position: relative;
                    background: ${isBooked ? 'rgba(29,78,216,0.10)' : isToday ? 'rgba(29,78,216,0.05)' : 'transparent'};
                    border: 1.5px solid ${isBooked ? 'var(--primary)' : isToday ? 'rgba(29,78,216,0.3)' : 'transparent'};
                    cursor: ${isBooked ? 'pointer' : 'default'};"
                ${isBooked ? `title="${tooltipLines.replace(/"/g, '&quot;')}"` : ''}
            >
                <span style="font-size: 0.85rem; font-weight: ${isToday ? '700' : '400'}; color: ${isToday ? 'var(--primary)' : 'var(--text-main)'};">${day}</span>
                ${isBooked ? `<div style="width: 5px; height: 5px; background: var(--primary); border-radius: 50%; margin: 3px auto 0;"></div>` : ''}
                ${isBooked ? `<div style="font-size: 0.6rem; color: var(--primary); line-height: 1.2; margin-top: 2px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${dayBookings[0].eventName || 'Booked'}</div>` : ''}
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
