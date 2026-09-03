// App State
let appState = {
    places: [],
    categories: ['all'],
    activeCategory: 'all',
    searchQuery: '',
    viewMode: 'grid' // 'grid' or 'table'
};

// DOM Elements
const collectionContainer = document.getElementById('collectionContainer');
const searchInput = document.getElementById('searchInput');
const categoryChips = document.getElementById('categoryChips');
const statTotalPlaces = document.getElementById('statTotalPlaces');
const statTotalCategories = document.getElementById('statTotalCategories');
const statPopularDishes = document.getElementById('statPopularDishes');

const linkTextArea = document.getElementById('linkTextArea');
const btnAddLinks = document.getElementById('btnAddLinks');
const btnBrowseFile = document.getElementById('btnBrowseFile');
const fileDropzone = document.getElementById('fileDropzone');
const btnExportExcel = document.getElementById('btnExportExcel');
const btnClearAll = document.getElementById('btnClearAll');
const loadingOverlay = document.getElementById('loadingOverlay');
const loadingText = document.getElementById('loadingText');

const btnRandomizer = document.getElementById('btnRandomizer');
const randomizerModal = document.getElementById('randomizerModal');
const btnCloseModal = document.getElementById('btnCloseModal');
const btnSpinRandom = document.getElementById('btnSpinRandom');
const randomResultBox = document.getElementById('randomResultBox');

const viewGridBtn = document.getElementById('viewGridBtn');
const viewTableBtn = document.getElementById('viewTableBtn');

// Callback nạp ngầm dữ liệu từ Python Backend (Async Push)
window.onBackendDataReady = function(places) {
    if (Array.isArray(places) && places.length > 0) {
        appState.places = places;
        try {
            localStorage.setItem('munch_cached_places', JSON.stringify(places));
        } catch (e) {}
        updateUI();
        showToast(`Đã đồng bộ ${places.length} quán ăn mới nhất!`, "info");
    }
};

window.onInitialDataLoaded = function(places) {
    window.onBackendDataReady(places);
};

// Runtime Environment helper
const isPyWebView = () => !!(window.pywebview && window.pywebview.api);

function updateRuntimeModeBadge(mode) {
    const badge = document.getElementById('appModeBadge');
    if (!badge) return;
    if (mode === 'desktop') {
        badge.textContent = 'DESKTOP APP';
        badge.style.background = 'linear-gradient(90deg, #10b981, #059669)';
        badge.title = 'Đang chạy qua PyWebView Desktop Backend';
    } else {
        badge.textContent = 'STATIC WEB';
        badge.style.background = 'linear-gradient(90deg, #3b82f6, #8b5cf6)';
        badge.title = 'Đang chạy chế độ Web Tĩnh (0 VNĐ Server - Pre-baked Data)';
    }
}

// Fetch & Load Places from Backend (Desktop Mode)
async function loadPlaces() {
    try {
        if (isPyWebView()) {
            const places = await window.pywebview.api.get_places();
            if (places && Array.isArray(places)) {
                appState.places = places;
                localStorage.setItem('munch_cached_places', JSON.stringify(places));
                updateUI();
            }
        }
    } catch (e) {
        console.error("Lỗi nạp dữ liệu từ Python API:", e);
    }
}

// Fetch & Load Places from Static JSON (Static Web Mode)
async function loadStaticPlaces() {
    try {
        const res = await fetch('./places.json');
        if (res.ok) {
            const data = await res.json();
            if (Array.isArray(data) && data.length > 0) {
                if (appState.places.length === 0 || appState.places.length !== data.length) {
                    appState.places = data;
                    localStorage.setItem('munch_cached_places', JSON.stringify(data));
                    updateUI();
                    showToast(`Đã nạp ${data.length} quán ăn từ dữ liệu Pre-gen tĩnh!`, "info");
                }
            }
        } else {
            console.warn("Không tìm thấy file ./places.json tĩnh");
        }
    } catch (err) {
        console.log("Static places fetch:", err);
    }
}

// Initialize App
document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    
    // 0ms INSTANT RENDER: Nạp ngay từ localStorage đệm nếu có
    try {
        const cached = localStorage.getItem('munch_cached_places');
        if (cached) {
            const parsed = JSON.parse(cached);
            if (Array.isArray(parsed) && parsed.length > 0) {
                appState.places = parsed;
                updateUI();
            }
        }
    } catch (e) {
        console.warn("Lỗi đọc cache local:", e);
    }

    // Nhận diện môi trường Runtime: Desktop hay Static Web
    if (isPyWebView()) {
        updateRuntimeModeBadge('desktop');
        loadPlaces();
    } else {
        let pywebviewLoaded = false;
        const handlePyWebView = () => {
            if (pywebviewLoaded) return;
            pywebviewLoaded = true;
            updateRuntimeModeBadge('desktop');
            loadPlaces();
        };
        window.addEventListener('pywebviewready', handlePyWebView);

        // Nếu sau 350ms không có pywebviewready -> Kích hoạt Static Web Mode
        setTimeout(() => {
            if (!pywebviewLoaded && !isPyWebView()) {
                updateRuntimeModeBadge('web');
                loadStaticPlaces();
            }
        }, 350);
    }
});

// Client-Side Excel Exporter (SheetJS)
function exportExcelClientSide() {
    if (typeof XLSX === 'undefined') {
        showToast("Thư viện SheetJS chưa được nạp, vui lòng kiểm tra kết nối mạng!", "error");
        return;
    }
    try {
        const exportData = appState.places.map((p, idx) => ({
            "STT": idx + 1,
            "Tên Quán": p.name || "",
            "Danh Mục": p.category || "",
            "Địa Chỉ": p.address || "",
            "Món Gợi Ý": Array.isArray(p.recommended_dishes) ? p.recommended_dishes.join(", ") : (p.recommended_dishes || ""),
            "Khoảng Giá": p.price_range || "",
            "Đánh Giá AI": p.rating_ai || "",
            "Không Gian & Vibe": p.vibe || "",
            "Tóm Tắt Đánh Giá": p.summary || "",
            "Điểm Nổi Bật": Array.isArray(p.highlights) ? p.highlights.join(", ") : (p.highlights || ""),
            "Link Google Maps": p.original_url || p.expanded_url || ""
        }));

        const ws = XLSX.utils.json_to_sheet(exportData);
        ws['!cols'] = [
            { wch: 6 },
            { wch: 30 },
            { wch: 18 },
            { wch: 45 },
            { wch: 35 },
            { wch: 20 },
            { wch: 12 },
            { wch: 35 },
            { wch: 50 },
            { wch: 25 },
            { wch: 40 }
        ];

        const wb = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(wb, ws, "Danh Sách Quán Ăn");
        const dateStr = new Date().toISOString().slice(0, 10);
        XLSX.writeFile(wb, `danh_sach_quan_an_${dateStr}.xlsx`);
        showToast("Đã xuất file Excel thành công trực tiếp từ trình duyệt!", "success");
    } catch (e) {
        console.error("Lỗi xuất Excel:", e);
        showToast(`Lỗi xuất Excel: ${e.message}`, "error");
    }
}

// Client-Side File Reader (Web Mode)
function handleWebUploadedFile(file) {
    if (!file) return;
    const ext = file.name.split('.').pop().toLowerCase();
    
    if (ext === 'json') {
        const reader = new FileReader();
        reader.onload = (e) => {
            try {
                const data = JSON.parse(e.target.result);
                if (Array.isArray(data) && data.length > 0) {
                    appState.places = data;
                    localStorage.setItem('munch_cached_places', JSON.stringify(data));
                    updateUI();
                    showToast(`Đã nhập thành công ${data.length} quán từ file JSON!`, "success");
                } else {
                    showToast("File JSON không hợp lệ!", "error");
                }
            } catch (err) {
                showToast(`Lỗi đọc JSON: ${err.message}`, "error");
            }
        };
        reader.readAsText(file);
    } else if (ext === 'xlsx' || ext === 'xls' || ext === 'csv') {
        if (typeof XLSX === 'undefined') {
            showToast("Thư viện SheetJS chưa sẵn sàng!", "error");
            return;
        }
        const reader = new FileReader();
        reader.onload = (e) => {
            try {
                const data = new Uint8Array(e.target.result);
                const workbook = XLSX.read(data, { type: 'array' });
                const firstSheet = workbook.Sheets[workbook.SheetNames[0]];
                const rows = XLSX.utils.sheet_to_json(firstSheet);
                showToast(`Đã đọc ${rows.length} dòng từ Excel! Để phân tích AI, hãy chạy script pregen_dataset.py.`, "info");
            } catch (err) {
                showToast(`Lỗi đọc Excel: ${err.message}`, "error");
            }
        };
        reader.readAsArrayBuffer(file);
    } else if (ext === 'txt') {
        const reader = new FileReader();
        reader.onload = (e) => {
            const text = e.target.result;
            const urls = text.match(/https?:\/\/[^\s]+/g) || [];
            showToast(`Đã tìm thấy ${urls.length} link Google Maps trong file TXT!`, "info");
        };
        reader.readAsText(file);
    } else {
        showToast("Định dạng file không được hỗ trợ!", "error");
    }
}

// Event Listeners
function setupEventListeners() {
    // Dán Link Manual
    btnAddLinks.addEventListener('click', async () => {
        const text = linkTextArea.value.trim();
        if (!text) {
            showToast("Vui lòng dán ít nhất 1 đường link Google Maps!", "error");
            return;
        }

        if (isPyWebView()) {
            showLoading("AI Gemini đang phân tích link quán ăn...");
            try {
                const res = await window.pywebview.api.process_text(text);
                if (res.success) {
                    appState.places = res.places || [];
                    linkTextArea.value = "";
                    showToast(`Đã thêm thành công ${res.count} quán ăn mới!`, "success");
                } else {
                    showToast(`Lỗi: ${res.error}`, "error");
                }
            } catch (e) {
                showToast("Có lỗi xảy ra khi phân tích link!", "error");
            } finally {
                hideLoading();
                updateUI();
            }
        } else {
            // Chế độ Web Tĩnh
            showToast("💡 Chế độ Web Tĩnh (0 VNĐ Server): Hãy chạy 'python pregen_dataset.py' trên máy để AI xử lý và cập nhật lên web!", "info");
        }
    });

    // Hidden Web File Input
    const fileInputWeb = document.getElementById('fileInputWeb');
    if (fileInputWeb) {
        fileInputWeb.addEventListener('change', (e) => {
            const files = e.target.files;
            if (files && files.length > 0) {
                handleWebUploadedFile(files[0]);
                fileInputWeb.value = "";
            }
        });
    }

    // File Browse Dialog
    btnBrowseFile.addEventListener('click', async () => {
        if (isPyWebView()) {
            showLoading("Đang đọc file và gọi AI Gemini...");
            try {
                const res = await window.pywebview.api.open_file_dialog();
                if (res.success) {
                    appState.places = res.places || [];
                    showToast(`Đã xử lý file thành công (${res.count} quán)!`, "success");
                } else if (res.error) {
                    showToast(`Lỗi đọc file: ${res.error}`, "error");
                }
            } catch (e) {
                showToast("Lỗi khi chọn file!", "error");
            } finally {
                hideLoading();
                updateUI();
            }
        } else {
            // Web Mode: Kích hoạt file picker của trình duyệt
            if (fileInputWeb) fileInputWeb.click();
        }
    });

    // Drag and Drop File
    fileDropzone.addEventListener('dragover', (e) => {
        e.preventDefault();
        fileDropzone.classList.add('drag-over');
    });

    fileDropzone.addEventListener('dragleave', () => {
        fileDropzone.classList.remove('drag-over');
    });

    fileDropzone.addEventListener('drop', async (e) => {
        e.preventDefault();
        fileDropzone.classList.remove('drag-over');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            const file = files[0];
            if (isPyWebView() && file.path) {
                showLoading("AI đang đọc dữ liệu từ file...");
                try {
                    const res = await window.pywebview.api.process_file(file.path);
                    if (res.success) {
                        appState.places = res.places || [];
                        updateUI();
                        showToast(`Nhập dữ liệu thành công (${res.count} quán mới)!`, "success");
                    }
                } catch (err) {
                    showToast("Lỗi xử lý file!", "error");
                } finally {
                    hideLoading();
                }
            } else {
                handleWebUploadedFile(file);
            }
        }
    });

    // Export Excel
    btnExportExcel.addEventListener('click', async () => {
        if (appState.places.length === 0) {
            showToast("Chưa có quán ăn nào để xuất Excel!", "error");
            return;
        }

        if (isPyWebView()) {
            const res = await window.pywebview.api.export_excel_dialog();
            if (res.success) {
                showToast("Xuất Excel thành công!", "success");
            } else if (res.error) {
                showToast(`Lỗi xuất file: ${res.error}`, "error");
            }
        } else {
            exportExcelClientSide();
        }
    });

    // Clear All
    btnClearAll.addEventListener('click', async () => {
        if (confirm("Bạn có chắc chắn muốn xóa danh sách quán ăn đang hiển thị không?")) {
            if (isPyWebView()) {
                const res = await window.pywebview.api.clear_all();
                if (res.success) {
                    appState.places = [];
                    updateUI();
                    showToast("Đã xóa sạch danh sách quán ăn!", "success");
                }
            } else {
                appState.places = [];
                localStorage.removeItem('munch_cached_places');
                updateUI();
                showToast("Đã xóa danh sách hiển thị! Bạn có thể tải lại trang để nạp lại dữ liệu gốc.", "info");
            }
        }
    });

    // Search Input
    searchInput.addEventListener('input', (e) => {
        appState.searchQuery = e.target.value.toLowerCase().trim();
        renderCollection();
    });

    // Grid Density Toggle Buttons
    const gridColsToggle = document.getElementById('gridColsToggle');
    if (gridColsToggle) {
        gridColsToggle.querySelectorAll('.density-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const cols = e.target.dataset.cols;
                gridColsToggle.querySelectorAll('.density-btn').forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
                
                collectionContainer.classList.remove('cols-1', 'cols-2', 'cols-3', 'cols-4');
                collectionContainer.classList.add(`cols-${cols}`);
                renderCollection();
            });
        });
    }

    // Debounced Window Resize Handler (Fix Bug 1 UI Resize Break)
    let resizeTimer;
    window.addEventListener('resize', () => {
        cancelAnimationFrame(resizeTimer);
        resizeTimer = requestAnimationFrame(() => {
            if (appState.viewMode === 'grid') {
                renderCollection();
            }
        });
    });

    // View Toggle Buttons
    viewGridBtn.addEventListener('click', () => {
        appState.viewMode = 'grid';
        viewGridBtn.classList.add('active');
        viewTableBtn.classList.remove('active');
        collectionContainer.classList.remove('table-mode');
        renderCollection();
    });

    viewTableBtn.addEventListener('click', () => {
        appState.viewMode = 'table';
        viewTableBtn.classList.add('active');
        viewGridBtn.classList.remove('active');
        collectionContainer.classList.add('table-mode');
        renderCollection();
    });

    const btnReanalyze = document.getElementById('btnReanalyze');
    if (btnReanalyze) {
        btnReanalyze.addEventListener('click', async () => {
            if (isPyWebView()) {
                showLoading("AI đang cập nhật lại thông tin các quán chưa rõ...");
                try {
                    const res = await window.pywebview.api.reanalyze_fallbacks();
                    if (res.success) {
                        appState.places = res.places || [];
                        updateUI();
                        showToast(`Đã phân tích lại thành công ${res.count} quán!`, "success");
                    }
                } catch (e) {
                    showToast("Lỗi khi phân tích lại!", "error");
                } finally {
                    hideLoading();
                }
            } else {
                showToast("💡 Chế độ Web Tĩnh: Hãy chạy 'python reprocess_fallback.py' hoặc 'python pregen_dataset.py' trên máy local để cập nhật dữ liệu!", "info");
            }
        });
    }

    // Randomizer Modal Controls
    btnRandomizer.addEventListener('click', () => {
        randomizerModal.classList.remove('hidden');
    });

    btnCloseModal.addEventListener('click', () => {
        randomizerModal.classList.add('hidden');
    });

    btnSpinRandom.addEventListener('click', spinRandomFood);
}

// UI Render & Update Logic
function updateUI() {
    updateStats();
    updateCategoryChips();
    renderCollection();
}

function updateStats() {
    const total = appState.places.length;
    statTotalPlaces.textContent = total;

    const categories = new Set(appState.places.map(p => p.category || 'Khác'));
    statTotalCategories.textContent = `${categories.size} Loại hình`;

    // Collect top dishes
    const allDishes = [];
    appState.places.forEach(p => {
        if (Array.isArray(p.recommended_dishes)) {
            allDishes.push(...p.recommended_dishes);
        }
    });
    const uniqueDishes = [...new Set(allDishes)];
    statPopularDishes.textContent = uniqueDishes.length > 0 ? uniqueDishes.slice(0, 2).join(', ') : 'Chưa có';
}

function updateCategoryChips() {
    const categories = ['all', ...new Set(appState.places.map(p => p.category).filter(Boolean))];
    appState.categories = categories;

    categoryChips.innerHTML = categories.map(cat => {
        const label = cat === 'all' ? 'Tất cả' : cat;
        const isActive = appState.activeCategory === cat ? 'active' : '';
        return `<button class="chip ${isActive}" data-category="${cat}">${label}</button>`;
    }).join('');

    // Chip click event
    categoryChips.querySelectorAll('.chip').forEach(btn => {
        btn.addEventListener('click', (e) => {
            appState.activeCategory = e.target.dataset.category;
            updateCategoryChips();
            renderCollection();
        });
    });
}

function renderCollection() {
    let filtered = appState.places;

    // Filter by Category
    if (appState.activeCategory !== 'all') {
        filtered = filtered.filter(p => p.category === appState.activeCategory);
    }

    // Filter by Search Query
    if (appState.searchQuery) {
        const q = appState.searchQuery;
        filtered = filtered.filter(p => {
            const name = (p.name || '').toLowerCase();
            const address = (p.address || '').toLowerCase();
            const dishes = Array.isArray(p.recommended_dishes) ? p.recommended_dishes.join(' ').toLowerCase() : '';
            return name.includes(q) || address.includes(q) || dishes.includes(q);
        });
    }

    if (filtered.length === 0) {
        collectionContainer.innerHTML = `
            <div style="grid-column: 1 / -1; text-align: center; padding: 60px 20px; color: var(--text-muted);">
                <i class="fa-solid fa-utensils-slash" style="font-size: 3rem; margin-bottom: 16px; opacity: 0.5;"></i>
                <h3>Chưa có quán ăn nào</h3>
                <p>Hãy dán đường link Google Maps hoặc kéo thả file TXT / Excel để bắt đầu!</p>
            </div>
        `;
        return;
    }

    if (appState.viewMode === 'grid') {
        renderGridView(filtered);
    } else {
        renderTableView(filtered);
    }
}

function renderGridView(places) {
    const defaultImg = "https://images.unsplash.com/photo-1504674900247-0877df9cc836?auto=format&fit=crop&w=800&q=80";
    const isCols1 = collectionContainer.classList.contains('cols-1');

    collectionContainer.innerHTML = places.map(p => {
        const dishes = Array.isArray(p.recommended_dishes) ? p.recommended_dishes : [];
        const dishesHtml = dishes.map(d => `<span class="dish-tag">${escapeHtml(d)}</span>`).join('');
        const mapUrl = p.original_url || p.expanded_url || '#';
        const ratingVal = p.rating_ai || p.rating || 4.5;
        const reviewCountStr = p.review_count ? ` (${escapeHtml(p.review_count)})` : '';
        const rating = `⭐ ${ratingVal}${reviewCountStr}`;
        const imgUrl = p.image_url || defaultImg;
        const vibe = p.vibe ? `<span class="price-tag" style="background-color: rgba(139, 92, 246, 0.15); color: var(--accent-purple);"><i class="fa-solid fa-sparkles"></i> ${escapeHtml(p.vibe)}</span>` : '';

        // Tạo danh sách ảnh thực tế từ Google Maps
        let photoGalleryHtml = '';
        const galleryList = Array.isArray(p.photo_gallery) && p.photo_gallery.length > 0 ? p.photo_gallery : [imgUrl];
        if (isCols1) {
            const itemsHtml = galleryList.map((src, i) => `
                <img src="${src}" alt="${escapeHtml(p.name)} Photo ${i+1}" class="card-photo-item" loading="lazy" decoding="async" onerror="this.src='${defaultImg}'" />
            `).join('');
            photoGalleryHtml = `<div class="card-photo-gallery">${itemsHtml}</div>`;
        }

        // Tạo khối hiển thị Đánh giá tiêu biểu (Top Comments)
        let topCommentsHtml = '';
        if (Array.isArray(p.top_comments) && p.top_comments.length > 0) {
            const firstComment = p.top_comments[0];
            topCommentsHtml = `
                <div class="top-comment-box" style="margin-top: 6px; padding: 8px 10px; background: rgba(255,255,255,0.03); border-radius: var(--radius-sm); border-left: 3px solid var(--accent-amber); font-size: 0.8rem; color: var(--text-secondary);">
                    <div style="display: flex; justify-content: space-between; font-weight: 600; color: var(--text-main); margin-bottom: 2px;">
                        <span><i class="fa-solid fa-circle-user" style="color: var(--accent-amber);"></i> ${escapeHtml(firstComment.author || 'Thực khách')}</span>
                        <span style="color: var(--accent-amber);">⭐ ${firstComment.rating || 5}/5</span>
                    </div>
                    <p style="margin: 0; font-style: italic;">"${escapeHtml(firstComment.comment)}"</p>
                </div>
            `;
        }

        return `
            <div class="food-card" data-id="${p.id}">
                ${isCols1 ? photoGalleryHtml : `
                <div class="card-banner">
                    <img src="${imgUrl}" alt="${escapeHtml(p.name)}" class="card-banner-img" loading="lazy" decoding="async" onerror="this.src='${defaultImg}'" />
                    <div class="card-overlay"></div>
                    <div class="card-banner-badges">
                        <span class="place-category">${escapeHtml(p.category || 'Ẩm thực')}</span>
                        <span class="rating-tag" style="background: rgba(0,0,0,0.7); backdrop-filter: blur(4px); padding: 4px 8px; border-radius: var(--radius-full); font-size: 0.78rem; color: var(--accent-amber); font-weight: 700;">${rating}</span>
                    </div>
                </div>`}

                <div class="card-body">
                    <div class="card-header">
                        <div style="flex: 1;">
                            <h4 class="place-name">${escapeHtml(p.name || 'Quán ăn')}</h4>
                            <span class="place-address"><i class="fa-solid fa-location-dot" style="color: var(--accent-emerald);"></i> ${escapeHtml(p.address || 'Đang cập nhật')}</span>
                        </div>
                        ${isCols1 ? `<div style="display: flex; gap: 8px; align-items: center;"><span class="place-category">${escapeHtml(p.category || 'Ẩm thực')}</span><span class="rating-tag" style="background: var(--bg-hover); padding: 4px 8px; border-radius: var(--radius-full); font-size: 0.85rem; color: var(--accent-amber); font-weight: 700;">${rating}</span></div>` : ''}
                    </div>

                    <div class="dishes-box">
                        <span class="dishes-title"><i class="fa-solid fa-utensils"></i> Món nên thử</span>
                        <div class="dishes-tags">${dishesHtml || '<span class="dish-tag">Món đặc sản</span>'}</div>
                    </div>

                    <div class="card-details">
                        <span class="price-tag"><i class="fa-solid fa-wallet"></i> ${escapeHtml(p.price_range || 'Bình dân')}</span>
                        ${vibe}
                    </div>

                    ${p.summary ? `<p class="summary-quote">"${escapeHtml(p.summary)}"</p>` : ''}
                    ${topCommentsHtml}

                    <div class="card-footer" style="margin-top: auto; padding-top: 10px; border-top: 1px solid rgba(255,255,255,0.05); display: flex; justify-content: space-between; align-items: center;">
                        <a href="${mapUrl}" target="_blank" class="map-link">
                            <i class="fa-solid fa-map-location-dot"></i> Google Maps
                        </a>
                        <div style="display: flex; gap: 8px;">
                            <button class="btn-icon-delete" onclick="reanalyzePlace('${p.id}')" title="Phân tích lại quán này với AI">
                                <i class="fa-solid fa-arrows-rotate" style="color: var(--accent-amber);"></i>
                            </button>
                            <button class="btn-icon-delete" onclick="deletePlace('${p.id}')" title="Xóa quán này">
                                <i class="fa-solid fa-trash"></i>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

function renderTableView(places) {
    let rowsHtml = places.map((p, idx) => {
        const dishes = Array.isArray(p.recommended_dishes) ? p.recommended_dishes.join(', ') : '';
        const mapUrl = p.original_url || p.expanded_url || '#';
        return `
            <tr style="border-bottom: 1px solid var(--border-color); color: var(--text-main);">
                <td style="padding: 12px;">${idx + 1}</td>
                <td style="padding: 12px; font-weight: 700;">${escapeHtml(p.name)}</td>
                <td style="padding: 12px;"><span class="place-category">${escapeHtml(p.category)}</span></td>
                <td style="padding: 12px; font-size: 0.8rem; color: var(--text-muted);">${escapeHtml(p.address)}</td>
                <td style="padding: 12px; color: var(--accent-amber); font-weight: 600;">${escapeHtml(dishes)}</td>
                <td style="padding: 12px; color: var(--accent-emerald);">${escapeHtml(p.price_range)}</td>
                <td style="padding: 12px;"><a href="${mapUrl}" target="_blank" class="map-link">Google Maps</a></td>
                <td style="padding: 12px; text-align: center;">
                    <button class="btn-icon-delete" onclick="deletePlace('${p.id}')"><i class="fa-solid fa-trash"></i></button>
                </td>
            </tr>
        `;
    }).join('');

    collectionContainer.innerHTML = `
        <table style="width: 100%; border-collapse: collapse; background-color: var(--bg-card); border-radius: var(--radius-md); overflow: hidden;">
            <thead>
                <tr style="background-color: var(--bg-hover); color: var(--text-muted); font-size: 0.8rem; text-transform: uppercase; text-align: left;">
                    <th style="padding: 12px;">#</th>
                    <th style="padding: 12px;">Tên Quán</th>
                    <th style="padding: 12px;">Loại Hình</th>
                    <th style="padding: 12px;">Địa Chỉ</th>
                    <th style="padding: 12px;">Món Nên Thử</th>
                    <th style="padding: 12px;">Khoảng Giá</th>
                    <th style="padding: 12px;">Link Maps</th>
                    <th style="padding: 12px; text-align: center;">Xóa</th>
                </tr>
            </thead>
            <tbody>${rowsHtml}</tbody>
        </table>
    `;
}

// Global Actions
async function reanalyzePlace(placeId) {
    if (window.pywebview && window.pywebview.api) {
        showLoading("AI đang phân tích lại quán này...");
        try {
            const res = await window.pywebview.api.reanalyze_place(placeId);
            if (res.success) {
                appState.places = res.places || [];
                updateUI();
                showToast("Đã cập nhật lại thông tin quán thành công!", "success");
            }
        } catch (e) {
            showToast("Lỗi khi cập nhật!", "error");
        } finally {
            hideLoading();
        }
    }
}

async function deletePlace(placeId) {
    if (window.pywebview && window.pywebview.api) {
        const res = await window.pywebview.api.delete_place(placeId);
        if (res.success) {
            appState.places = res.places || [];
            updateUI();
            showToast("Đã xóa quán ăn khỏi danh sách!", "success");
        }
    }
}

function spinRandomFood() {
    if (appState.places.length === 0) {
        randomResultBox.innerHTML = `
            <div class="result-placeholder">
                <i class="fa-solid fa-circle-exclamation" style="color: var(--accent-danger);"></i>
                <p>Danh sách của bạn chưa có quán ăn nào để chọn ngẫu nhiên!</p>
            </div>
        `;
        return;
    }

    const randomIndex = Math.floor(Math.random() * appState.places.length);
    const chosen = appState.places[randomIndex];
    const mapUrl = chosen.original_url || chosen.expanded_url || '#';

    randomResultBox.innerHTML = `
        <div style="text-align: center; animation: slideIn 0.3s ease;">
            <span class="place-category" style="margin-bottom: 8px; inline-block;">${escapeHtml(chosen.category || 'Ẩm thực')}</span>
            <h2 style="font-family: var(--font-heading); color: var(--accent-amber); font-size: 1.5rem; margin-bottom: 8px;">
                🔥 ${escapeHtml(chosen.name)}
            </h2>
            <p style="font-size: 0.85rem; color: var(--text-muted); margin-bottom: 10px;">
                <i class="fa-solid fa-location-dot"></i> ${escapeHtml(chosen.address)}
            </p>
            <div style="margin-bottom: 12px; font-weight: 600; color: var(--accent-emerald);">
                Món gợi ý: ${escapeHtml(Array.isArray(chosen.recommended_dishes) ? chosen.recommended_dishes.join(', ') : 'Đặc sản')}
            </div>
            <a href="${mapUrl}" target="_blank" class="btn btn-primary btn-sm" style="text-decoration: none;">
                <i class="fa-solid fa-map-location-dot"></i> Đi Đến Quán Ngay!
            </a>
        </div>
    `;
}

// Utility Functions
function showLoading(msg) {
    loadingText.textContent = msg || "Đang xử lý...";
    loadingOverlay.classList.remove('hidden');
}

function hideLoading() {
    loadingOverlay.classList.add('hidden');
}

function showToast(message, type = "success") {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    const icon = type === "success" ? "fa-circle-check" : "fa-circle-xmark";
    toast.innerHTML = `<i class="fa-solid ${icon}"></i> <span>${escapeHtml(message)}</span>`;
    
    document.getElementById('toastContainer').appendChild(toast);
    setTimeout(() => toast.remove(), 4000);
}

function escapeHtml(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}
