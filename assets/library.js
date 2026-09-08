(function () {
  const state = { guides: [], query: '', course: 'ALL' };

  const listEl = document.getElementById('lib-list');
  const searchEl = document.getElementById('lib-search');
  const filtersEl = document.getElementById('lib-filters');
  const offlineBadge = document.getElementById('lib-offline-badge');

  function render() {
    const q = state.query.trim().toLowerCase();
    const filtered = state.guides.filter((g) => {
      const matchesCourse = state.course === 'ALL' || g.course === state.course;
      const matchesQuery =
        !q ||
        g.title.toLowerCase().includes(q) ||
        g.course.toLowerCase().includes(q) ||
        (g.courseName || '').toLowerCase().includes(q);
      return matchesCourse && matchesQuery;
    });

    listEl.innerHTML = '';

    if (filtered.length === 0) {
      const empty = document.createElement('div');
      empty.className = 'lib-empty';
      empty.textContent = 'No guides match your search.';
      listEl.appendChild(empty);
      return;
    }

    const groups = new Map();
    filtered.forEach((g) => {
      if (!groups.has(g.course)) groups.set(g.course, []);
      groups.get(g.course).push(g);
    });

    for (const [course, guides] of groups) {
      const groupEl = document.createElement('div');
      groupEl.className = 'lib-group';

      const title = document.createElement('div');
      title.className = 'lib-group-title';
      title.textContent = guides[0].courseName ? `${course} — ${guides[0].courseName}` : course;
      groupEl.appendChild(title);

      guides
        .slice()
        .sort((a, b) => (a.title > b.title ? 1 : -1))
        .forEach((g) => {
          const card = document.createElement('a');
          card.className = 'lib-card';
          card.href = g.path;

          const t = document.createElement('div');
          t.className = 'lib-card-title';
          t.textContent = g.title;

          const meta = document.createElement('div');
          meta.className = 'lib-card-meta';
          meta.textContent = g.dateAdded ? `Added ${g.dateAdded}` : '';

          card.appendChild(t);
          card.appendChild(meta);
          groupEl.appendChild(card);
        });

      listEl.appendChild(groupEl);
    }
  }

  function renderFilters() {
    const courses = ['ALL', ...new Set(state.guides.map((g) => g.course))];
    filtersEl.innerHTML = '';
    courses.forEach((c) => {
      const chip = document.createElement('div');
      chip.className = 'lib-filter-chip' + (c === state.course ? ' active' : '');
      chip.textContent = c;
      chip.addEventListener('click', () => {
        state.course = c;
        renderFilters();
        render();
      });
      filtersEl.appendChild(chip);
    });
  }

  searchEl.addEventListener('input', (e) => {
    state.query = e.target.value;
    render();
  });

  fetch('guides.json')
    .then((r) => r.json())
    .then((data) => {
      state.guides = data;
      renderFilters();
      render();
    })
    .catch(() => {
      listEl.innerHTML = '<div class="lib-empty">Could not load the guide index.</div>';
    });

  function updateOfflineBadge() {
    if (!navigator.onLine) {
      offlineBadge.classList.add('show');
      offlineBadge.textContent = 'Offline — showing cached guides';
    } else {
      offlineBadge.classList.remove('show');
    }
  }
  window.addEventListener('online', updateOfflineBadge);
  window.addEventListener('offline', updateOfflineBadge);
  updateOfflineBadge();

  if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
      navigator.serviceWorker.register('sw.js').catch((err) => {
        console.error('SW registration failed', err);
      });
    });
  }
})();
