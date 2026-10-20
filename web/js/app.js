/**
 * web/js/app.js
 * Atharv Studio - Searchable n8n Workflow Library Client Controller
 */

let allWorkflows = [];
let filteredWorkflows = [];
let categoriesData = [];
let statsData = {};
let brandingData = {};
let favoritesSet = new Set(JSON.parse(localStorage.getItem('atharv_favorites') || localStorage.getItem('flowforge_favorites') || '[]'));

let currentTab = 'all';
let currentPage = 1;
const PAGE_SIZE = 18;
let activeModalWorkflow = null;
let visualizer = null;

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', async () => {
  visualizer = new WorkflowVisualizer('nodeGraphSvg');
  setupEventListeners();
  await loadApplicationData();
});

async function loadApplicationData() {
  try {
    const [indexRes, statsRes, catRes, brandRes] = await Promise.all([
      fetch('data/index.json'),
      fetch('data/stats.json'),
      fetch('data/categories.json'),
      fetch('data/branding.json')
    ]);

    allWorkflows = await indexRes.json();
    statsData = await statsRes.json();
    categoriesData = await catRes.json();
    brandingData = await brandRes.json();

    applyBranding();
    populateFilterDropdowns();
    updateTabCounts();
    applyFilters();
  } catch (err) {
    console.error('Failed to load workflow data:', err);
    showToast('Notice: Running in preview mode or data loading error.');
  }
}

function applyBranding() {
  if (!brandingData.brand) return;
  const brand = brandingData.brand;
  document.getElementById('brandName').textContent = brand.name;
  document.getElementById('brandTagline').textContent = brand.tagline;
  document.getElementById('footerBrandName').textContent = brand.name;
  if (brand.github_repo_url) {
    document.getElementById('githubRepoLink').href = brand.github_repo_url;
  }
}

function updateTabCounts() {
  const origCount = allWorkflows.filter(w => w.origin_type === 'original').length;
  const modCount = allWorkflows.filter(w => w.origin_type === 'modified').length;

  document.getElementById('headerTotalCount').textContent = allWorkflows.length.toLocaleString();
  document.getElementById('metricTotal').textContent = allWorkflows.length.toLocaleString();
  document.getElementById('metricOriginals').textContent = origCount;
  document.getElementById('countAll').textContent = allWorkflows.length;
  document.getElementById('countOriginals').textContent = origCount;
  document.getElementById('countModified').textContent = modCount;
  document.getElementById('countFavorites').textContent = favoritesSet.size;
}

function populateFilterDropdowns() {
  // Category dropdown
  const catSelect = document.getElementById('categoryFilter');
  catSelect.innerHTML = '<option value="">All 30 Categories</option>';
  categoriesData.forEach(c => {
    const opt = document.createElement('option');
    opt.value = c.id;
    opt.textContent = c.name;
    catSelect.appendChild(opt);
  });

  // Integrations dropdown
  const intSelect = document.getElementById('integrationFilter');
  intSelect.innerHTML = '<option value="">All Integrations</option>';
  if (statsData.integrations) {
    statsData.integrations.forEach(i => {
      const opt = document.createElement('option');
      opt.value = i.name;
      opt.textContent = `${i.name} (${i.count})`;
      intSelect.appendChild(opt);
    });
  }

  // Triggers dropdown
  const trigSelect = document.getElementById('triggerFilter');
  trigSelect.innerHTML = '<option value="">All Triggers</option>';
  if (statsData.triggers) {
    statsData.triggers.forEach(t => {
      const opt = document.createElement('option');
      opt.value = t.name;
      opt.textContent = `${t.name} (${t.count})`;
      trigSelect.appendChild(opt);
    });
  }
}

function setupEventListeners() {
  // Search input with instant filter
  const searchInput = document.getElementById('searchInput');
  const clearBtn = document.getElementById('clearSearchBtn');

  searchInput.addEventListener('input', () => {
    clearBtn.style.display = searchInput.value ? 'block' : 'none';
    currentPage = 1;
    applyFilters();
  });

  clearBtn.addEventListener('click', () => {
    searchInput.value = '';
    clearBtn.style.display = 'none';
    currentPage = 1;
    applyFilters();
    searchInput.focus();
  });

  // Keyboard shortcut '/'
  window.addEventListener('keydown', (e) => {
    if (e.key === '/' && document.activeElement !== searchInput) {
      e.preventDefault();
      searchInput.focus();
    }
    if (e.key === 'Escape') {
      closeModal();
    }
  });

  // Filter dropdowns
  ['categoryFilter', 'integrationFilter', 'triggerFilter', 'complexityFilter', 'credentialsFilter', 'sortBy'].forEach(id => {
    document.getElementById(id).addEventListener('change', () => {
      currentPage = 1;
      applyFilters();
    });
  });

  document.getElementById('resetFiltersBtn').addEventListener('click', resetFilters);
  document.getElementById('emptyResetBtn').addEventListener('click', resetFilters);

  // Tabs navigation
  document.querySelectorAll('.nav-tab').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.nav-tab').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      switchMainTab(btn.dataset.tab);
    });
  });

  // Pagination buttons
  document.getElementById('prevPageBtn').addEventListener('click', () => {
    if (currentPage > 1) {
      currentPage--;
      renderWorkflows();
      window.scrollTo({ top: 380, behavior: 'smooth' });
    }
  });

  document.getElementById('nextPageBtn').addEventListener('click', () => {
    const totalPages = Math.ceil(filteredWorkflows.length / PAGE_SIZE);
    if (currentPage < totalPages) {
      currentPage++;
      renderWorkflows();
      window.scrollTo({ top: 380, behavior: 'smooth' });
    }
  });

  // Modal close & controls
  document.getElementById('modalCloseBtn').addEventListener('click', closeModal);
  document.getElementById('workflowModal').addEventListener('click', (e) => {
    if (e.target.id === 'workflowModal') closeModal();
  });

  document.getElementById('modalCopyBtn').addEventListener('click', () => copyActiveWorkflowJson());
  document.getElementById('modalDownloadBtn').addEventListener('click', () => downloadActiveWorkflowJson());

  // Modal tabs
  document.querySelectorAll('.modal-tab').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.modal-tab').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.modal-tab-content').forEach(c => c.classList.remove('active'));
      btn.classList.add('active');
      const targetId = 'content' + btn.dataset.mTab.charAt(0).toUpperCase() + btn.dataset.mTab.slice(1);
      const contentEl = document.getElementById(targetId);
      if (contentEl) contentEl.classList.add('active');
    });
  });

  // Visualizer Zoom
  document.getElementById('vizZoomInBtn').addEventListener('click', () => visualizer.zoom(1.2));
  document.getElementById('vizZoomOutBtn').addEventListener('click', () => visualizer.zoom(0.8));
  document.getElementById('vizResetBtn').addEventListener('click', () => visualizer.reset());
}

function switchMainTab(tabName) {
  currentTab = tabName;
  const catalogView = document.getElementById('catalogView');
  const filtersSection = document.getElementById('filtersSection');
  const securityView = document.getElementById('securityAuditView');

  // Hide all views first
  catalogView.style.display = 'none';
  filtersSection.style.display = 'none';
  securityView.style.display = 'none';

  if (tabName === 'security-audit') {
    securityView.style.display = 'block';
  } else {
    catalogView.style.display = 'block';
    filtersSection.style.display = 'block';
    currentPage = 1;
    applyFilters();
  }
}

function resetFilters() {
  document.getElementById('searchInput').value = '';
  document.getElementById('clearSearchBtn').style.display = 'none';
  document.getElementById('categoryFilter').value = '';
  document.getElementById('integrationFilter').value = '';
  document.getElementById('triggerFilter').value = '';
  document.getElementById('complexityFilter').value = '';
  document.getElementById('credentialsFilter').value = '';
  document.getElementById('sortBy').value = 'featured';
  currentPage = 1;
  applyFilters();
}

function applyFilters() {
  const searchTerm = document.getElementById('searchInput').value.trim().toLowerCase();
  const selectedCat = document.getElementById('categoryFilter').value;
  const selectedInt = document.getElementById('integrationFilter').value;
  const selectedTrig = document.getElementById('triggerFilter').value;
  const selectedComp = document.getElementById('complexityFilter').value;
  const selectedCreds = document.getElementById('credentialsFilter').value;
  const sortBy = document.getElementById('sortBy').value;

  filteredWorkflows = allWorkflows.filter(wf => {
    // Tab filter
    if (currentTab === 'originals' && wf.origin_type !== 'original') return false;
    if (currentTab === 'modified' && wf.origin_type !== 'modified') return false;
    if (currentTab === 'favorites' && !favoritesSet.has(wf.id)) return false;

    // Search query match
    if (searchTerm) {
      const matchTitle = wf.title.toLowerCase().includes(searchTerm);
      const matchDesc = (wf.description || '').toLowerCase().includes(searchTerm);
      const matchCat = (wf.category_name || '').toLowerCase().includes(searchTerm);
      const matchInt = (wf.integrations || []).some(i => i.toLowerCase().includes(searchTerm));
      const matchTrig = (wf.triggers || []).some(t => t.toLowerCase().includes(searchTerm));
      if (!matchTitle && !matchDesc && !matchCat && !matchInt && !matchTrig) {
        return false;
      }
    }

    // Dropdown filters
    if (selectedCat && wf.category_id !== selectedCat) return false;
    if (selectedInt && !(wf.integrations || []).includes(selectedInt)) return false;
    if (selectedTrig && !(wf.triggers || []).includes(selectedTrig)) return false;
    if (selectedComp && wf.complexity !== selectedComp) return false;
    if (selectedCreds === 'no-creds' && wf.has_credentials) return false;
    if (selectedCreds === 'has-creds' && !wf.has_credentials) return false;

    return true;
  });

  // Sorting
  if (sortBy === 'name-asc') {
    filteredWorkflows.sort((a, b) => a.title.localeCompare(b.title));
  } else if (sortBy === 'name-desc') {
    filteredWorkflows.sort((a, b) => b.title.localeCompare(a.title));
  } else if (sortBy === 'nodes-desc') {
    filteredWorkflows.sort((a, b) => b.node_count - a.node_count);
  } else if (sortBy === 'nodes-asc') {
    filteredWorkflows.sort((a, b) => a.node_count - b.node_count);
  } else {
    // Featured / Originals First
    const rank = { 'original': 0, 'modified': 1, 'community': 2 };
    filteredWorkflows.sort((a, b) => (rank[a.origin_type] || 2) - (rank[b.origin_type] || 2));
  }

  renderWorkflows();
}

function renderWorkflows() {
  const grid = document.getElementById('workflowsGrid');
  const emptyState = document.getElementById('emptyState');
  const paginationBar = document.getElementById('paginationBar');
  const resultsBadge = document.getElementById('resultsCount');

  resultsBadge.textContent = `${filteredWorkflows.length} Workflows`;

  if (filteredWorkflows.length === 0) {
    grid.innerHTML = '';
    emptyState.style.display = 'block';
    paginationBar.style.display = 'none';
    document.getElementById('paginationSummary').textContent = 'Showing 0 of 0';
    return;
  }

  emptyState.style.display = 'none';
  paginationBar.style.display = 'flex';

  const totalPages = Math.ceil(filteredWorkflows.length / PAGE_SIZE);
  if (currentPage > totalPages) currentPage = totalPages;

  const startIndex = (currentPage - 1) * PAGE_SIZE;
  const endIndex = Math.min(startIndex + PAGE_SIZE, filteredWorkflows.length);
  const currentBatch = filteredWorkflows.slice(startIndex, endIndex);

  document.getElementById('paginationSummary').textContent = `Showing ${startIndex + 1}-${endIndex} of ${filteredWorkflows.length}`;

  grid.innerHTML = currentBatch.map(wf => createWorkflowCardHtml(wf)).join('');

  // Attach card event listeners
  currentBatch.forEach(wf => {
    const cardEl = document.getElementById(`wf-card-${wf.id}`);
    if (!cardEl) return;

    cardEl.querySelector('.card-title').addEventListener('click', () => openWorkflowModal(wf));
    cardEl.querySelector('.btn-inspect').addEventListener('click', () => openWorkflowModal(wf));
    cardEl.querySelector('.btn-copy-card').addEventListener('click', (e) => {
      e.stopPropagation();
      copyWorkflowJsonByPath(wf.catalog_rel_path, wf.title);
    });

    const favBtn = cardEl.querySelector('.fav-btn');
    favBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      toggleFavorite(wf.id, favBtn);
    });
  });

  renderPaginationControls(totalPages);
}

function createWorkflowCardHtml(wf) {
  const isFav = favoritesSet.has(wf.id);
  const integChips = (wf.integrations || []).slice(0, 3).map(i => `<span class="integ-chip">${i}</span>`).join('');
  
  let originBadge = '';
  if (wf.origin_type === 'original') {
    originBadge = `<span class="badge-original">★ Atharv Original</span>`;
  } else if (wf.origin_type === 'modified') {
    originBadge = `<span class="badge-modified">⚡ Enhanced</span>`;
  }

  return `
    <div class="workflow-card" id="wf-card-${wf.id}">
      <div>
        <div class="card-top">
          <span class="card-category-pill">${wf.category_name}</span>
          <div class="card-badges">
            ${originBadge}
            <button class="fav-btn ${isFav ? 'is-fav' : ''}" title="Save to Favorites">♥</button>
          </div>
        </div>
        <h4 class="card-title" title="${wf.title}">${wf.title}</h4>
        <p class="card-description">${wf.description || 'Production automation template.'}</p>
        <div class="card-integrations">${integChips}</div>
      </div>

      <div class="card-footer">
        <div class="card-meta-left">
          <span class="node-count-badge">⚙ ${wf.node_count} nodes</span>
          <span>•</span>
          <span>${wf.complexity}</span>
        </div>
        <div class="card-actions">
          <button class="btn btn-sm btn-outline btn-copy-card" title="Copy workflow to paste onto canvas">Copy</button>
          <button class="btn btn-sm btn-primary btn-inspect">Inspect</button>
        </div>
      </div>
    </div>
  `;
}

function renderPaginationControls(totalPages) {
  const prevBtn = document.getElementById('prevPageBtn');
  const nextBtn = document.getElementById('nextPageBtn');
  const pageNumbers = document.getElementById('pageNumbers');

  prevBtn.disabled = (currentPage === 1);
  nextBtn.disabled = (currentPage === totalPages);

  pageNumbers.innerHTML = '';

  let start = Math.max(1, currentPage - 2);
  let end = Math.min(totalPages, start + 4);
  if (end - start < 4) start = Math.max(1, end - 4);

  for (let i = start; i <= end; i++) {
    const pBtn = document.createElement('button');
    pBtn.className = `page-num ${i === currentPage ? 'active' : ''}`;
    pBtn.textContent = i;
    pBtn.addEventListener('click', () => {
      currentPage = i;
      renderWorkflows();
      window.scrollTo({ top: 380, behavior: 'smooth' });
    });
    pageNumbers.appendChild(pBtn);
  }
}

function toggleFavorite(id, btn) {
  if (favoritesSet.has(id)) {
    favoritesSet.delete(id);
    btn.classList.remove('is-fav');
    showToast('Removed from favorites');
  } else {
    favoritesSet.add(id);
    btn.classList.add('is-fav');
    showToast('Added to favorites ♥');
  }
  localStorage.setItem('atharv_favorites', JSON.stringify(Array.from(favoritesSet)));
  document.getElementById('countFavorites').textContent = favoritesSet.size;
  if (currentTab === 'favorites') {
    applyFilters();
  }
}

async function openWorkflowModal(wf) {
  activeModalWorkflow = wf;
  const modal = document.getElementById('workflowModal');
  modal.style.display = 'flex';

  document.getElementById('modalTitle').textContent = wf.title;
  document.getElementById('modalCategory').textContent = wf.category_name;
  document.getElementById('modalOrigin').textContent = wf.origin_type === 'original' ? 'Atharv Original' : (wf.origin_type === 'modified' ? 'Atharv Enhanced' : 'Curated Community');
  document.getElementById('modalNodesCount').textContent = `${wf.node_count} nodes (${wf.complexity})`;
  document.getElementById('modalLicense').textContent = wf.license;
  document.getElementById('modalAuthor').textContent = wf.original_author;
  document.getElementById('modalDescription').textContent = wf.description;

  // Integrations list
  document.getElementById('modalIntegrationsList').innerHTML = (wf.integrations || []).map(i => `<span class="integ-chip">${i}</span>`).join('') || '<span class="text-dim">Standard n8n nodes</span>';
  
  // Triggers list
  document.getElementById('modalTriggersList').innerHTML = (wf.triggers || []).map(t => `<span class="integ-chip">${t}</span>`).join('');
  
  // Credentials list
  document.getElementById('modalCredentialsList').innerHTML = (wf.credentials_required || []).map(c => `<span class="integ-chip">${c}</span>`).join('') || '<span class="text-dim">No credentials needed</span>';

  // Fetch full JSON for visualizer & code view
  document.getElementById('modalJsonCode').textContent = 'Loading workflow JSON definition...';
  try {
    const res = await fetch(`../${wf.catalog_rel_path}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    activeModalWorkflow.fullData = data;

    document.getElementById('modalJsonCode').textContent = JSON.stringify(data, null, 2);

    // Nodes sequence table
    const wfObj = data.workflow && data.workflow.nodes ? data.workflow : data;
    const nodes = wfObj.nodes || [];
    document.getElementById('modalNodesTable').innerHTML = nodes.map((n, i) => `
      <div class="node-row">
        <span><strong>${i + 1}.</strong> ${n.name}</span>
        <span class="node-row-type">${n.type}</span>
      </div>
    `).join('');

    // Render interactive visualizer
    visualizer.render(data);

    // Similar workflows
    populateSimilarWorkflows(wf);

  } catch (err) {
    document.getElementById('modalJsonCode').textContent = 'Could not load raw JSON: ' + err.message;
  }
}

function populateSimilarWorkflows(currentWf) {
  const container = document.getElementById('similarWorkflowsGrid');
  const similar = allWorkflows.filter(w => w.id !== currentWf.id && (w.category_id === currentWf.category_id || (w.integrations && currentWf.integrations && w.integrations.some(i => currentWf.integrations.includes(i))))).slice(0, 4);

  if (similar.length === 0) {
    container.innerHTML = '<p class="text-dim">No similar workflows found in this category.</p>';
    return;
  }

  container.innerHTML = similar.map(s => `
    <div class="workflow-card" style="margin-bottom: 12px; cursor: pointer;" onclick="openWorkflowModalById('${s.id}')">
      <div class="card-top">
        <span class="card-category-pill">${s.category_name}</span>
        <span class="node-count-badge">⚙ ${s.node_count} nodes</span>
      </div>
      <h5 style="color: #fff; margin: 6px 0;">${s.title}</h5>
      <p style="font-size: 0.8rem; color: #94a3b8;">${(s.description || '').substring(0, 90)}...</p>
    </div>
  `).join('');
}

window.openWorkflowModalById = function(id) {
  const found = allWorkflows.find(w => w.id === id);
  if (found) openWorkflowModal(found);
};

function closeModal() {
  document.getElementById('workflowModal').style.display = 'none';
  activeModalWorkflow = null;
}

async function copyActiveWorkflowJson() {
  if (!activeModalWorkflow || !activeModalWorkflow.fullData) {
    showToast('Workflow JSON is still loading...');
    return;
  }
  const jsonStr = JSON.stringify(activeModalWorkflow.fullData, null, 2);
  await navigator.clipboard.writeText(jsonStr);
  showToast('✓ Copied to clipboard! Ready to paste into n8n canvas (Ctrl+V)');
}

async function copyWorkflowJsonByPath(relPath, title) {
  try {
    const res = await fetch(`../${relPath}`);
    const data = await res.json();
    await navigator.clipboard.writeText(JSON.stringify(data, null, 2));
    showToast(`✓ Copied "${title}" (Ctrl+V into n8n)`);
  } catch (e) {
    showToast('Failed to copy workflow JSON.');
  }
}

function downloadActiveWorkflowJson() {
  if (!activeModalWorkflow || !activeModalWorkflow.fullData) return;
  const jsonStr = JSON.stringify(activeModalWorkflow.fullData, null, 2);
  const blob = new Blob([jsonStr], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `${activeModalWorkflow.slug || 'workflow'}.json`;
  a.click();
  URL.revokeObjectURL(url);
  showToast(`Downloaded ${a.download}`);
}


function showToast(msg) {
  const container = document.getElementById('toastContainer');
  const toast = document.createElement('div');
  toast.className = 'toast';
  toast.innerHTML = `<span>${msg}</span>`;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}
