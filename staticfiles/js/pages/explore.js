let studyPage = 1, bmPage = 1;
let studyDone = false, bmDone = false;
let q = '';

async function fetchItems(kind, page, search) {
  const params = new URLSearchParams({ page, limit: 12 });
  if (search) params.append('search', search);
  const base = kind === 'studies' ? '/api/v1/study/' : '/api/v1/study/biomarkers/';
  const res = await fetch(`${base}?${params.toString()}`);
  return res.json();
}

function studyCard(item) {
  return `
    <div class="col-md-6 col-xl-4">
      <div class="card h-100">
        <div class="card-body">
          <h5 class="card-title">${item.name ?? 'Study'}</h5>
          <p class="card-text text-muted">${item.description ?? ''}</p>
        </div>
      </div>
    </div>`;
}

function biomarkerCard(item) {
  return `
    <div class="col-md-6 col-xl-4">
      <div class="card h-100">
        <div class="card-body">
          <h5 class="card-title">${item.name ?? 'Biomarker'}</h5>
          <p class="card-text text-muted">${item.category ?? ''}</p>
        </div>
      </div>
    </div>`;
}

async function loadStudies(append=true) {
  if (studyDone) return;
  const loading = document.getElementById('studiesLoading');
  const end = document.getElementById('studiesEnd');
  const container = document.getElementById('studiesContainer');
  loading?.classList.remove('d-none');
  const data = await fetchItems('studies', studyPage, q);
  const items = data.results ?? data.items ?? [];
  if (!append) container.innerHTML = '';
  container.insertAdjacentHTML('beforeend', items.map(studyCard).join(''));
  const hasNext = (data.pagination && data.pagination.has_next) || (data.page < data.total_pages);
  if (!hasNext || items.length === 0) { studyDone = true; end?.classList.remove('d-none'); }
  else { studyPage += 1; }
  loading?.classList.add('d-none');
}

async function loadBiomarkers(append=true) {
  if (bmDone) return;
  const loading = document.getElementById('biomarkersLoading');
  const end = document.getElementById('biomarkersEnd');
  const container = document.getElementById('biomarkersContainer');
  loading?.classList.remove('d-none');
  const data = await fetchItems('biomarkers', bmPage, q);
  const items = data.results ?? data.items ?? [];
  if (!append) container.innerHTML = '';
  container.insertAdjacentHTML('beforeend', items.map(biomarkerCard).join(''));
  const hasNext = (data.pagination && data.pagination.has_next) || (data.page < data.total_pages);
  if (!hasNext || items.length === 0) { bmDone = true; end?.classList.remove('d-none'); }
  else { bmPage += 1; }
  loading?.classList.add('d-none');
}

function onScroll() {
  const activeId = document.querySelector('#exploreTabs .nav-link.active')?.id;
  const container = activeId === 'studies-tab' ? 'studies' : 'biomarkers';
  if ((window.innerHeight + window.scrollY) >= (document.body.offsetHeight - 300)) {
    if (container === 'studies') loadStudies(true); else loadBiomarkers(true);
  }
}

document.addEventListener('DOMContentLoaded', () => {
  if (!document.getElementById('exploreTabs')) return;
  loadStudies(true);
  const btn = document.getElementById('searchBtn');
  const input = document.getElementById('searchInput');
  btn?.addEventListener('click', () => {
    q = input?.value || '';
    studyPage = 1; bmPage = 1; studyDone = false; bmDone = false;
    document.getElementById('studiesEnd')?.classList.add('d-none');
    document.getElementById('biomarkersEnd')?.classList.add('d-none');
    loadStudies(false);
    loadBiomarkers(false);
  });
  window.addEventListener('scroll', onScroll);
});


