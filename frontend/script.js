/**
 * Lumina AI Background Remover — Frontend Application Logic
 * Full-featured interactive studio, comparison sliders, background replacement,
 * and high-fidelity multi-format export (PNG, JPG, Vector SVG).
 */

(function () {
  'use strict';

  // =========================================================================
  // State Management
  // =========================================================================
  const state = {
    currentImageId: null,
    originalFilename: 'image.png',
    originalImageSrc: null,
    processedImageSrc: null,
    customBgImageSrc: null,
    imageWidth: 0,
    imageHeight: 0,
    processingTimeMs: 0,

    // Viewer states
    viewMode: 'slider', // 'slider' | 'cutout' | 'side'
    zoomLevel: 1.0,
    splitPercent: 50,

    // Background customization
    bgType: 'transparent', // 'transparent' | 'color' | 'gradient' | 'image'
    solidColor: '#ffffff',
    gradientStart: '#3b82f6',
    gradientEnd: '#9333ea',
    gradientDirection: 'vertical',

    // Export format
    exportFormat: 'png', // 'png' | 'jpg' | 'svg'

    // Library & Pagination State
    libraryPage: 1,
    libraryLimit: 12,
    libraryFilter: 'all',
    librarySort: 'newest',
    librarySearch: '',
    currentDetailImage: null,

    // Identity State
    guestSessionId: null,
    currentUser: null,

    // Flags
    isProcessing: false
  };

  // =========================================================================
  // DOM Elements
  // =========================================================================
  const elements = {
    // Nav & Status
    aiStatusPill: document.getElementById('aiStatusPill'),
    navLibraryLink: document.getElementById('navLibraryLink'),
    libraryCountBadge: document.getElementById('libraryCountBadge'),
    accountBtn: document.getElementById('accountBtn'),
    accountLabel: document.getElementById('accountLabel'),

    // Hero & Demo Slider
    heroSlider: document.getElementById('heroSlider'),
    heroDemoCutoutWrapper: document.getElementById('heroDemoCutoutWrapper'),
    heroSliderBar: document.getElementById('heroSliderBar'),

    // Upload
    uploadSection: document.getElementById('uploadSection'),
    dropZone: document.getElementById('dropZone'),
    fileInput: document.getElementById('fileInput'),
    browseBtn: document.getElementById('browseBtn'),
    sampleChips: document.querySelectorAll('.sample-chip'),

    // Processing Overlay
    processingCard: document.getElementById('processingCard'),
    processingPreviewImg: document.getElementById('processingPreviewImg'),
    processingStatusTitle: document.getElementById('processingStatusTitle'),
    processingStatusStep: document.getElementById('processingStatusStep'),
    progressBarFill: document.getElementById('progressBarFill'),
    steps: [
      document.getElementById('step1'),
      document.getElementById('step2'),
      document.getElementById('step3'),
      document.getElementById('step4')
    ],

    // Editor & Studio
    editorSection: document.getElementById('editorSection') || document.getElementById('editor-section'),
    metaFilename: document.getElementById('metaFilename'),
    metaStats: document.getElementById('metaStats'),
    viewTabs: document.querySelectorAll('.view-tab'),

    // Canvas & Viewports
    canvasViewport: document.getElementById('canvasViewport'),
    splitSliderContainer: document.getElementById('splitSliderContainer'),
    cutoutOnlyContainer: document.getElementById('cutoutOnlyContainer'),
    sideBySideContainer: document.getElementById('sideBySideContainer'),

    // Images
    sliderOrigImg: document.getElementById('sliderOrigImg'),
    sliderProcImg: document.getElementById('sliderProcImg'),
    cutoutOnlyImg: document.getElementById('cutoutOnlyImg'),
    sideOrigImg: document.getElementById('sideOrigImg'),
    sideProcImg: document.getElementById('sideProcImg'),

    // Backdrop wrappers for live background preview
    sliderBackdropWrapper: document.getElementById('sliderBackdropWrapper'),
    cutoutBackdropWrapper: document.getElementById('cutoutBackdropWrapper'),
    sideBackdropWrapper: document.getElementById('sideBackdropWrapper'),

    // Slider handles
    sliderProcLayer: document.getElementById('sliderProcLayer'),
    sliderHandleBar: document.getElementById('sliderHandleBar'),

    // Canvas tools
    zoomInBtn: document.getElementById('zoomInBtn'),
    zoomOutBtn: document.getElementById('zoomOutBtn'),
    fitScreenBtn: document.getElementById('fitScreenBtn'),
    zoomLevelLabel: document.getElementById('zoomLevelLabel'),
    uploadAnotherBtn: document.getElementById('uploadAnotherBtn'),
    resetStudioBtn: document.getElementById('resetStudioBtn'),

    // Background Controls
    bgTabs: document.querySelectorAll('.bg-tab'),
    bgPanels: {
      transparent: document.getElementById('bgSettingsTransparent'),
      color: document.getElementById('bgSettingsColor'),
      gradient: document.getElementById('bgSettingsGradient'),
      image: document.getElementById('bgSettingsImage')
    },
    colorSwatches: document.querySelectorAll('.color-swatch-btn'),
    customColorPicker: document.getElementById('customColorPicker'),
    customColorHex: document.getElementById('customColorHex'),
    gradientSwatches: document.querySelectorAll('.gradient-swatch-btn'),
    gradientStartPicker: document.getElementById('gradientStartPicker'),
    gradientEndPicker: document.getElementById('gradientEndPicker'),
    gradientDirectionSelect: document.getElementById('gradientDirectionSelect'),
    customBgDropzone: document.getElementById('customBgDropzone'),
    customBgInput: document.getElementById('customBgInput'),
    customBgFileName: document.getElementById('customBgFileName'),

    // Export Controls
    formatCards: document.querySelectorAll('.format-card'),
    svgNoticeBox: document.getElementById('svgNoticeBox'),
    downloadBtn: document.getElementById('downloadBtn'),
    downloadBtnText: document.getElementById('downloadBtnText'),

    // Library Elements
    refreshLibraryBtn: document.getElementById('refreshLibraryBtn'),
    clearAllHistoryBtn: document.getElementById('clearAllHistoryBtn'),
    librarySearchInput: document.getElementById('librarySearchInput'),
    filterChips: document.querySelectorAll('.filter-chip'),
    librarySortSelect: document.getElementById('librarySortSelect'),
    libraryGrid: document.getElementById('libraryGrid'),
    libraryEmpty: document.getElementById('libraryEmpty'),
    emptyUploadBtn: document.getElementById('emptyUploadBtn'),
    libraryPagination: document.getElementById('libraryPagination'),
    prevPageBtn: document.getElementById('prevPageBtn'),
    nextPageBtn: document.getElementById('nextPageBtn'),
    pageIndicator: document.getElementById('pageIndicator'),

    // Library Detail Modal
    libraryDetailModal: document.getElementById('libraryDetailModal'),
    closeDetailModalBtn: document.getElementById('closeDetailModalBtn'),
    modalImageTitle: document.getElementById('modalImageTitle'),
    modalImageBadge: document.getElementById('modalImageBadge'),
    modalOrigImg: document.getElementById('modalOrigImg'),
    modalProcImg: document.getElementById('modalProcImg'),
    modalMetaRes: document.getElementById('modalMetaRes'),
    modalMetaSize: document.getElementById('modalMetaSize'),
    modalMetaDate: document.getElementById('modalMetaDate'),
    modalMetaStatus: document.getElementById('modalMetaStatus'),
    modalDeleteBtn: document.getElementById('modalDeleteBtn'),
    modalOpenStudioBtn: document.getElementById('modalOpenStudioBtn'),
    modalDownloadBtn: document.getElementById('modalDownloadBtn'),

    // Account & Session Modal
    accountModal: document.getElementById('accountModal'),
    closeAccountModalBtn: document.getElementById('closeAccountModalBtn'),
    sessionTypeDisplay: document.getElementById('sessionTypeDisplay'),
    sessionIdDisplay: document.getElementById('sessionIdDisplay'),
    copySessionBtn: document.getElementById('copySessionBtn'),
    accountTabs: document.querySelectorAll('.account-tab'),
    authForm: document.getElementById('authForm'),
    authUsername: document.getElementById('authUsername'),
    authEmail: document.getElementById('authEmail'),
    emailGroup: document.getElementById('emailGroup'),
    authSubmitBtn: document.getElementById('authSubmitBtn'),

    // Privacy Modal & Banner
    privacyModal: document.getElementById('privacyModal'),
    closePrivacyModalBtn: document.getElementById('closePrivacyModalBtn'),
    ackPrivacyBtn: document.getElementById('ackPrivacyBtn'),
    privacyBanner: document.getElementById('privacyBanner'),
    openPrivacyModalBtn: document.getElementById('openPrivacyModalBtn'),
    dismissPrivacyBannerBtn: document.getElementById('dismissPrivacyBannerBtn'),

    // Toasts
    toastContainer: document.getElementById('toastContainer')
  };

  // Base API URL
  const API_BASE = window.location.origin;

  // =========================================================================
  // Initialize Application
  // =========================================================================
  function init() {
    initIdentity();
    setupHeroDemoSlider();
    setupDropzone();
    setupSampleChips();
    setupViewModeTabs();
    setupCanvasZoom();
    setupSplitSlider();
    setupBackgroundControls();
    setupExportControls();
    setupLibrary();
    setupAccountAndSession();
    setupPrivacyBanner();
    checkBackendHealth();
    fetchLibrary();
  }

  // =========================================================================
  // Toast Notifications
  // =========================================================================
  function showToast(message, type = 'info', duration = 3500) {
    if (!elements.toastContainer) return;
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    elements.toastContainer.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(100%)';
      toast.style.transition = 'all 0.3s ease';
      setTimeout(() => toast.remove(), 300);
    }, duration);
  }

  // =========================================================================
  // Backend Health Check
  // =========================================================================
  async function checkBackendHealth() {
    try {
      const res = await fetch(`${API_BASE}/api/health`);
      if (res.ok) {
        const data = await res.json();
        if (elements.aiStatusPill) {
          elements.aiStatusPill.innerHTML = `
            <span class="status-dot"></span>
            <span class="status-label">U2-Net AI Online</span>
          `;
        }
      }
    } catch (e) {
      if (elements.aiStatusPill) {
        elements.aiStatusPill.innerHTML = `
          <span class="status-dot" style="background:#eab308;box-shadow:0 0 10px #eab308;"></span>
          <span class="status-label" style="color:#eab308;">Local Backend Standby</span>
        `;
      }
    }
  }

  // =========================================================================
  // Hero Demo Slider (Interactive Before/After on Landing)
  // =========================================================================
  function setupHeroDemoSlider() {
    if (!elements.heroSlider) return;

    let isDragging = false;

    function updateHeroSlider(xPos) {
      const rect = elements.heroSlider.getBoundingClientRect();
      let percent = ((xPos - rect.left) / rect.width) * 100;
      percent = Math.max(0, Math.min(100, percent));

      elements.heroDemoCutoutWrapper.style.clipPath = `inset(0 0 0 ${percent}%)`;
      elements.heroSliderBar.style.left = `${percent}%`;
    }

    elements.heroSlider.addEventListener('mousedown', (e) => {
      isDragging = true;
      updateHeroSlider(e.clientX);
    });

    window.addEventListener('mousemove', (e) => {
      if (!isDragging) return;
      updateHeroSlider(e.clientX);
    });

    window.addEventListener('mouseup', () => {
      isDragging = false;
    });

    // Touch support for mobile/tablets
    elements.heroSlider.addEventListener('touchstart', (e) => {
      isDragging = true;
      updateHeroSlider(e.touches[0].clientX);
    }, { passive: true });

    window.addEventListener('touchmove', (e) => {
      if (!isDragging) return;
      updateHeroSlider(e.touches[0].clientX);
    }, { passive: true });

    window.addEventListener('touchend', () => {
      isDragging = false;
    });
  }

  // =========================================================================
  // Drag & Drop / File Upload Handlers
  // =========================================================================
  function setupDropzone() {
    const { dropZone, fileInput, browseBtn } = elements;
    if (!dropZone || !fileInput) return;

    // Trigger file chooser
    browseBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      fileInput.click();
    });

    dropZone.addEventListener('click', () => {
      fileInput.click();
    });

    fileInput.addEventListener('change', (e) => {
      if (e.target.files && e.target.files[0]) {
        handleFileSelection(e.target.files[0]);
      }
    });

    // Drag events
    ['dragenter', 'dragover'].forEach(eventName => {
      dropZone.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropZone.classList.add('drag-over');
      });
    });

    ['dragleave', 'drop'].forEach(eventName => {
      dropZone.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropZone.classList.remove('drag-over');
      });
    });

    dropZone.addEventListener('drop', (e) => {
      const dt = e.dataTransfer;
      if (dt && dt.files && dt.files.length > 0) {
        handleFileSelection(dt.files[0]);
      }
    });

    // Reset buttons
    if (elements.uploadAnotherBtn) {
      elements.uploadAnotherBtn.addEventListener('click', resetToUpload);
    }
    if (elements.resetStudioBtn) {
      elements.resetStudioBtn.addEventListener('click', resetToUpload);
    }
  }

  function handleFileSelection(file) {
    if (state.isProcessing) return;

    // 1. Validate file type
    const validExtensions = ['image/jpeg', 'image/png', 'image/webp'];
    const ext = file.name.split('.').pop().toLowerCase();
    const allowedExts = ['jpg', 'jpeg', 'png', 'webp'];

    if (!validExtensions.includes(file.type) && !allowedExts.includes(ext)) {
      showToast('Unsupported format. Please upload JPG, PNG, or WebP.', 'error');
      return;
    }

    // 2. Validate file size (25 MB)
    const maxSize = 25 * 1024 * 1024;
    if (file.size > maxSize) {
      showToast('File too large. Maximum upload size is 25 MB.', 'error');
      return;
    }

    state.originalFilename = file.name;

    // Show processing indicator with local preview
    const reader = new FileReader();
    reader.onload = (e) => {
      state.originalImageSrc = e.target.result;
      if (elements.processingPreviewImg) {
        elements.processingPreviewImg.src = state.originalImageSrc;
      }
      startProcessing(file);
    };
    reader.readAsDataURL(file);
  }

  // =========================================================================
  // Sample Images Shelf (Click to test instantly)
  // =========================================================================
  function setupSampleChips() {
    const samples = {
      portrait: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=800&q=80',
      pet: 'https://images.unsplash.com/photo-1543466835-00a7907e9de1?auto=format&fit=crop&w=800&q=80',
      car: 'https://images.unsplash.com/photo-1503376780353-7e6692767b70?auto=format&fit=crop&w=800&q=80',
      product: 'https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=800&q=80'
    };

    elements.sampleChips.forEach(chip => {
      chip.addEventListener('click', async () => {
        if (state.isProcessing) return;
        const key = chip.getAttribute('data-sample');
        const url = samples[key];
        if (!url) return;

        showToast(`Loading ${key} sample image...`, 'info', 2000);

        try {
          // Fetch image as blob
          const res = await fetch(url);
          const blob = await res.blob();
          const file = new File([blob], `sample_${key}.jpg`, { type: 'image/jpeg' });
          handleFileSelection(file);
        } catch (e) {
          showToast('Could not load sample image. Please upload your own image.', 'error');
        }
      });
    });
  }

  // =========================================================================
  // Process Image with Local AI Backend
  // =========================================================================
  async function startProcessing(file) {
    state.isProcessing = true;

    // UI transitions
    elements.uploadSection.style.display = 'none';
    elements.processingCard.style.display = 'block';
    if (elements.editorSection) elements.editorSection.style.display = 'none';

    // Step 1: Validation
    setProcessingStep(1, 'Validating file integrity and dimensions...', 25);

    // Prepare multipart payload
    const formData = new FormData();
    formData.append('image', file);
    formData.append('alpha_matting', 'false');

    // Step 2: Inference simulation progress
    setTimeout(() => {
      setProcessingStep(2, 'Running U2-Net deep neural network inference...', 55);
    }, 450);

    setTimeout(() => {
      setProcessingStep(3, 'Refining edge segmentation and hair matting...', 80);
    }, 1100);

    try {
      const response = await fetch(`${API_BASE}/api/remove-background`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: formData
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || `Server returned error (${response.status})`);
      }

      setProcessingStep(4, 'Finalizing lossless transparent cutout...', 95);

      const result = await response.json();
      if (!result.success) {
        throw new Error(result.error || 'AI background removal failed.');
      }

      // Success
      setTimeout(() => {
        onProcessingComplete(result);
      }, 350);

    } catch (err) {
      console.error('Processing error:', err);
      showToast(`Error: ${err.message}`, 'error', 5000);
      resetToUpload();
    }
  }

  function setProcessingStep(stepNum, statusText, progressPercent) {
    if (elements.processingStatusTitle) {
      elements.processingStatusTitle.textContent = statusText;
    }
    if (elements.progressBarFill) {
      elements.progressBarFill.style.width = `${progressPercent}%`;
    }
    elements.steps.forEach((step, idx) => {
      if (step) {
        if (idx < stepNum) {
          step.classList.add('active');
        } else {
          step.classList.remove('active');
        }
      }
    });
  }

  function onProcessingComplete(result) {
    state.isProcessing = false;
    state.currentImageId = result.image_id;
    state.originalFilename = result.filename || state.originalFilename;
    state.originalImageSrc = result.original_image || state.originalImageSrc;
    state.processedImageSrc = result.processed_image;
    state.imageWidth = result.width;
    state.imageHeight = result.height;
    state.processingTimeMs = result.processing_time_ms;

    // Update metadata tags
    if (elements.metaFilename) {
      elements.metaFilename.textContent = state.originalFilename;
    }
    if (elements.metaStats) {
      elements.metaStats.textContent = `${state.imageWidth} × ${state.imageHeight} px • ${state.processingTimeMs}ms processing`;
    }

    // Populate Images
    elements.sliderOrigImg.src = state.originalImageSrc;
    elements.sliderProcImg.src = state.processedImageSrc;
    elements.cutoutOnlyImg.src = state.processedImageSrc;
    elements.sideOrigImg.src = state.originalImageSrc;
    elements.sideProcImg.src = state.processedImageSrc;

    // Transition view
    elements.processingCard.style.display = 'none';
    elements.editorSection.style.display = 'block';

    // Apply default background state
    updateBackgroundPreview();

    // Reset zoom and split
    setZoom(1.0);
    setSplit(50);

    showToast('Background removed successfully!', 'success', 3000);

    // Refresh persistent library to display new cut
    fetchLibrary(1);

    // Scroll smoothly to editor
    elements.editorSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  function resetToUpload() {
    state.isProcessing = false;
    state.currentImageId = null;
    elements.processingCard.style.display = 'none';
    elements.editorSection.style.display = 'none';
    elements.uploadSection.style.display = 'block';
    if (elements.fileInput) elements.fileInput.value = '';

    // Scroll to upload
    elements.uploadSection.scrollIntoView({ behavior: 'smooth' });
  }

  // =========================================================================
  // Studio Split Slider (Comparison)
  // =========================================================================
  function setupSplitSlider() {
    const { splitSliderContainer, sliderProcLayer, sliderHandleBar } = elements;
    if (!splitSliderContainer) return;

    let isDragging = false;

    function handleSplitMove(xPos) {
      const rect = splitSliderContainer.getBoundingClientRect();
      let percent = ((xPos - rect.left) / rect.width) * 100;
      percent = Math.max(0, Math.min(100, percent));
      setSplit(percent);
    }

    splitSliderContainer.addEventListener('mousedown', (e) => {
      isDragging = true;
      handleSplitMove(e.clientX);
    });

    window.addEventListener('mousemove', (e) => {
      if (!isDragging) return;
      handleSplitMove(e.clientX);
    });

    window.addEventListener('mouseup', () => {
      isDragging = false;
    });

    // Touch
    splitSliderContainer.addEventListener('touchstart', (e) => {
      isDragging = true;
      handleSplitMove(e.touches[0].clientX);
    }, { passive: true });

    window.addEventListener('touchmove', (e) => {
      if (!isDragging) return;
      handleSplitMove(e.touches[0].clientX);
    }, { passive: true });

    window.addEventListener('touchend', () => {
      isDragging = false;
    });
  }

  function setSplit(percent) {
    state.splitPercent = percent;
    if (elements.sliderProcLayer) {
      elements.sliderProcLayer.style.clipPath = `inset(0 0 0 ${percent}%)`;
    }
    if (elements.sliderHandleBar) {
      elements.sliderHandleBar.style.left = `${percent}%`;
    }
  }

  // =========================================================================
  // View Modes (Slider / Cutout / Side-by-Side)
  // =========================================================================
  function setupViewModeTabs() {
    elements.viewTabs.forEach(tab => {
      tab.addEventListener('click', () => {
        elements.viewTabs.forEach(t => t.classList.remove('active'));
        tab.classList.add('active');

        const mode = tab.getAttribute('data-mode');
        state.viewMode = mode;

        elements.splitSliderContainer.style.display = mode === 'slider' ? 'block' : 'none';
        elements.cutoutOnlyContainer.style.display = mode === 'cutout' ? 'flex' : 'none';
        elements.sideBySideContainer.style.display = mode === 'side' ? 'grid' : 'none';
      });
    });
  }

  // =========================================================================
  // Canvas Zoom & Fit-to-Screen Controls
  // =========================================================================
  function setupCanvasZoom() {
    if (elements.zoomInBtn) {
      elements.zoomInBtn.addEventListener('click', () => {
        setZoom(state.zoomLevel + 0.25);
      });
    }

    if (elements.zoomOutBtn) {
      elements.zoomOutBtn.addEventListener('click', () => {
        setZoom(state.zoomLevel - 0.25);
      });
    }

    if (elements.fitScreenBtn) {
      elements.fitScreenBtn.addEventListener('click', () => {
        setZoom(1.0);
      });
    }
  }

  function setZoom(val) {
    state.zoomLevel = Math.max(0.5, Math.min(3.0, val));
    if (elements.zoomLevelLabel) {
      elements.zoomLevelLabel.textContent = `${Math.round(state.zoomLevel * 100)}%`;
    }

    const scaleStyle = `scale(${state.zoomLevel})`;
    if (elements.sliderOrigImg) elements.sliderOrigImg.style.transform = scaleStyle;
    if (elements.sliderProcImg) elements.sliderProcImg.style.transform = scaleStyle;
    if (elements.cutoutOnlyImg) elements.cutoutOnlyImg.style.transform = scaleStyle;
    if (elements.sideOrigImg) elements.sideOrigImg.style.transform = scaleStyle;
    if (elements.sideProcImg) elements.sideProcImg.style.transform = scaleStyle;
  }

  // =========================================================================
  // Background Customization (Transparent, Solid Color, Gradient, Custom Photo)
  // =========================================================================
  function setupBackgroundControls() {
    // 1. BG Tabs switcher
    elements.bgTabs.forEach(tab => {
      tab.addEventListener('click', () => {
        elements.bgTabs.forEach(t => t.classList.remove('active'));
        tab.classList.add('active');

        const bgKey = tab.getAttribute('data-bg');
        state.bgType = bgKey;

        // Show matching settings panel
        Object.keys(elements.bgPanels).forEach(key => {
          if (elements.bgPanels[key]) {
            elements.bgPanels[key].style.display = key === bgKey ? 'flex' : 'none';
          }
        });

        updateBackgroundPreview();
      });
    });

    // 2. Preset Color Swatches
    elements.colorSwatches.forEach(swatch => {
      swatch.addEventListener('click', () => {
        elements.colorSwatches.forEach(s => s.classList.remove('active'));
        swatch.classList.add('active');

        const color = swatch.getAttribute('data-color');
        state.solidColor = color;
        if (elements.customColorPicker) elements.customColorPicker.value = color;
        if (elements.customColorHex) elements.customColorHex.value = color.toUpperCase();

        updateBackgroundPreview();
      });
    });

    // 3. Custom Color Pickers
    if (elements.customColorPicker) {
      elements.customColorPicker.addEventListener('input', (e) => {
        state.solidColor = e.target.value;
        if (elements.customColorHex) elements.customColorHex.value = e.target.value.toUpperCase();
        elements.colorSwatches.forEach(s => s.classList.remove('active'));
        updateBackgroundPreview();
      });
    }

    if (elements.customColorHex) {
      elements.customColorHex.addEventListener('input', (e) => {
        let val = e.target.value.trim();
        if (!val.startsWith('#')) val = '#' + val;
        if (/^#[0-9A-Fa-f]{6}$/.test(val)) {
          state.solidColor = val;
          if (elements.customColorPicker) elements.customColorPicker.value = val;
          updateBackgroundPreview();
        }
      });
    }

    // 4. Preset Gradients
    elements.gradientSwatches.forEach(swatch => {
      swatch.addEventListener('click', () => {
        elements.gradientSwatches.forEach(s => s.classList.remove('active'));
        swatch.classList.add('active');

        state.gradientStart = swatch.getAttribute('data-g1');
        state.gradientEnd = swatch.getAttribute('data-g2');
        state.gradientDirection = swatch.getAttribute('data-dir') || 'vertical';

        if (elements.gradientStartPicker) elements.gradientStartPicker.value = state.gradientStart;
        if (elements.gradientEndPicker) elements.gradientEndPicker.value = state.gradientEnd;
        if (elements.gradientDirectionSelect) elements.gradientDirectionSelect.value = state.gradientDirection;

        updateBackgroundPreview();
      });
    });

    // Custom gradient pickers
    if (elements.gradientStartPicker) {
      elements.gradientStartPicker.addEventListener('input', (e) => {
        state.gradientStart = e.target.value;
        elements.gradientSwatches.forEach(s => s.classList.remove('active'));
        updateBackgroundPreview();
      });
    }

    if (elements.gradientEndPicker) {
      elements.gradientEndPicker.addEventListener('input', (e) => {
        state.gradientEnd = e.target.value;
        elements.gradientSwatches.forEach(s => s.classList.remove('active'));
        updateBackgroundPreview();
      });
    }

    if (elements.gradientDirectionSelect) {
      elements.gradientDirectionSelect.addEventListener('change', (e) => {
        state.gradientDirection = e.target.value;
        updateBackgroundPreview();
      });
    }

    // 5. Custom Backdrop Image Upload
    if (elements.customBgDropzone && elements.customBgInput) {
      elements.customBgDropzone.addEventListener('click', () => {
        elements.customBgInput.click();
      });

      elements.customBgInput.addEventListener('change', (e) => {
        if (e.target.files && e.target.files[0]) {
          const file = e.target.files[0];
          const reader = new FileReader();
          reader.onload = (event) => {
            state.customBgImageSrc = event.target.result;
            if (elements.customBgFileName) {
              elements.customBgFileName.textContent = file.name;
            }
            updateBackgroundPreview();
            showToast('Backdrop photo applied!', 'info', 2000);
          };
          reader.readAsDataURL(file);
        }
      });
    }
  }

  function updateBackgroundPreview() {
    const wrappers = [
      elements.sliderBackdropWrapper,
      elements.cutoutBackdropWrapper,
      elements.sideBackdropWrapper
    ];

    wrappers.forEach(wrapper => {
      if (!wrapper) return;

      if (state.bgType === 'transparent') {
        // Reset to checkerboard pattern
        wrapper.style.backgroundColor = 'var(--checker-dark)';
        wrapper.style.backgroundImage = `
          linear-gradient(45deg, var(--checker-light) 25%, transparent 25%),
          linear-gradient(-45deg, var(--checker-light) 25%, transparent 25%),
          linear-gradient(45deg, transparent 75%, var(--checker-light) 75%),
          linear-gradient(-45deg, transparent 75%, var(--checker-light) 75%)
        `;
        wrapper.style.backgroundSize = 'var(--checker-size) var(--checker-size)';
      } else if (state.bgType === 'color') {
        wrapper.style.backgroundImage = 'none';
        wrapper.style.backgroundColor = state.solidColor;
      } else if (state.bgType === 'gradient') {
        const dir = state.gradientDirection === 'horizontal' ? 'to right' :
                    state.gradientDirection === 'diagonal' ? 'to bottom right' : 'to bottom';
        wrapper.style.backgroundColor = 'transparent';
        wrapper.style.backgroundImage = `linear-gradient(${dir}, ${state.gradientStart}, ${state.gradientEnd})`;
        wrapper.style.backgroundSize = 'cover';
      } else if (state.bgType === 'image' && state.customBgImageSrc) {
        wrapper.style.backgroundColor = 'transparent';
        wrapper.style.backgroundImage = `url("${state.customBgImageSrc}")`;
        wrapper.style.backgroundSize = 'cover';
        wrapper.style.backgroundPosition = 'center';
      }
    });
  }

  // =========================================================================
  // Export & Download Options
  // =========================================================================
  function setupExportControls() {
    elements.formatCards.forEach(card => {
      card.addEventListener('click', () => {
        elements.formatCards.forEach(c => c.classList.remove('selected'));
        card.classList.add('selected');

        const radio = card.querySelector('input[type="radio"]');
        if (radio) radio.checked = true;

        const format = card.getAttribute('data-format');
        state.exportFormat = format;

        // Toggle SVG explanation notice
        if (elements.svgNoticeBox) {
          elements.svgNoticeBox.style.display = format === 'svg' ? 'flex' : 'none';
        }

        // Update button text
        if (elements.downloadBtnText) {
          if (format === 'png') elements.downloadBtnText.textContent = 'Download PNG';
          else if (format === 'jpg') elements.downloadBtnText.textContent = 'Download JPG';
          else if (format === 'svg') elements.downloadBtnText.textContent = 'Download Vector SVG';
        }
      });
    });

    if (elements.downloadBtn) {
      elements.downloadBtn.addEventListener('click', handleDownload);
    }
  }

  async function handleDownload() {
    if (!state.currentImageId && !state.processedImageSrc) {
      showToast('No processed image to export.', 'error');
      return;
    }

    const origBtnText = elements.downloadBtnText ? elements.downloadBtnText.textContent : 'Download';
    if (elements.downloadBtnText) {
      elements.downloadBtnText.textContent = 'Generating Export...';
    }
    elements.downloadBtn.disabled = true;

    try {
      // Build export payload
      const payload = {
        image_id: state.currentImageId,
        format: state.exportFormat,
        bg_type: state.bgType,
        bg_color: state.solidColor,
        gradient_start: state.gradientStart,
        gradient_end: state.gradientEnd,
        gradient_direction: state.gradientDirection
      };

      if (state.bgType === 'image' && state.customBgImageSrc) {
        payload.bg_custom_image = state.customBgImageSrc;
      }

      // If no image_id (e.g. offline fallback), include base64
      if (!state.currentImageId && state.processedImageSrc) {
        payload.image = state.processedImageSrc;
      }

      const response = await fetch(`${API_BASE}/api/export`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders()
        },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        const errJson = await response.json().catch(() => ({}));
        throw new Error(errJson.error || `Export failed (${response.status})`);
      }

      // Extract filename from Content-Disposition header if available
      let filename = `cutout_${state.exportFormat.toLowerCase()}.${state.exportFormat.toLowerCase()}`;
      const disposition = response.headers.get('Content-Disposition');
      if (disposition && disposition.includes('filename=')) {
        const matches = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/.exec(disposition);
        if (matches != null && matches[1]) {
          filename = matches[1].replace(/['"]/g, '');
        }
      } else {
        const base = state.originalFilename.substring(0, state.originalFilename.lastIndexOf('.')) || 'image';
        filename = `${base}_no_bg.${state.exportFormat.toLowerCase()}`;
      }

      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = downloadUrl;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(downloadUrl);

      showToast(`Exported ${state.exportFormat.toUpperCase()} successfully!`, 'success', 3000);

    } catch (err) {
      console.error('Download error:', err);
      showToast(`Download failed: ${err.message}`, 'error', 4500);
    } finally {
      if (elements.downloadBtnText) {
        elements.downloadBtnText.textContent = origBtnText;
      }
      elements.downloadBtn.disabled = false;
    }
  }

  // =========================================================================
  // Identity & Session Management
  // =========================================================================
  function initIdentity() {
    let guestId = localStorage.getItem('lumina_guest_id');
    if (!guestId) {
      guestId = 'guest_' + Math.random().toString(36).substring(2, 11) + Date.now().toString(36);
      localStorage.setItem('lumina_guest_id', guestId);
    }
    state.guestSessionId = guestId;

    const savedUserJson = localStorage.getItem('lumina_user');
    if (savedUserJson) {
      try {
        state.currentUser = JSON.parse(savedUserJson);
      } catch (e) {
        state.currentUser = null;
      }
    }
    updateIdentityUI();
  }

  function getAuthHeaders() {
    const headers = {
      'X-Session-ID': state.guestSessionId || 'default'
    };
    if (state.currentUser && state.currentUser.user_id) {
      headers['X-User-ID'] = state.currentUser.user_id;
    }
    return headers;
  }

  function updateIdentityUI() {
    if (state.currentUser && state.currentUser.username) {
      if (elements.accountLabel) elements.accountLabel.textContent = state.currentUser.username;
      if (elements.sessionTypeDisplay) elements.sessionTypeDisplay.textContent = `User: ${state.currentUser.username}`;
      if (elements.sessionIdDisplay) elements.sessionIdDisplay.textContent = `User ID: ${state.currentUser.user_id}`;
    } else {
      if (elements.accountLabel) elements.accountLabel.textContent = 'Guest Session';
      if (elements.sessionTypeDisplay) elements.sessionTypeDisplay.textContent = 'Guest Session';
      if (elements.sessionIdDisplay) elements.sessionIdDisplay.textContent = `Session: ${state.guestSessionId}`;
    }
  }

  // =========================================================================
  // Image Library & History
  // =========================================================================
  function setupLibrary() {
    if (elements.refreshLibraryBtn) {
      elements.refreshLibraryBtn.addEventListener('click', () => fetchLibrary(state.libraryPage));
    }

    if (elements.clearAllHistoryBtn) {
      elements.clearAllHistoryBtn.addEventListener('click', clearAllHistory);
    }

    if (elements.navLibraryLink) {
      elements.navLibraryLink.addEventListener('click', (e) => {
        fetchLibrary(1);
      });
    }

    if (elements.emptyUploadBtn) {
      elements.emptyUploadBtn.addEventListener('click', () => {
        elements.uploadSection.scrollIntoView({ behavior: 'smooth' });
      });
    }

    // Search filter with debounce
    let searchTimeout;
    if (elements.librarySearchInput) {
      elements.librarySearchInput.addEventListener('input', (e) => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
          state.librarySearch = e.target.value.trim();
          fetchLibrary(1);
        }, 300);
      });
    }

    // Format filter chips
    if (elements.filterChips) {
      elements.filterChips.forEach(chip => {
        chip.addEventListener('click', () => {
          elements.filterChips.forEach(c => c.classList.remove('active'));
          chip.classList.add('active');
          state.libraryFilter = chip.getAttribute('data-filter') || 'all';
          fetchLibrary(1);
        });
      });
    }

    // Sort order
    if (elements.librarySortSelect) {
      elements.librarySortSelect.addEventListener('change', (e) => {
        state.librarySort = e.target.value;
        fetchLibrary(1);
      });
    }

    // Pagination buttons
    if (elements.prevPageBtn) {
      elements.prevPageBtn.addEventListener('click', () => {
        if (state.libraryPage > 1) {
          fetchLibrary(state.libraryPage - 1);
        }
      });
    }

    if (elements.nextPageBtn) {
      elements.nextPageBtn.addEventListener('click', () => {
        fetchLibrary(state.libraryPage + 1);
      });
    }

    // Detail modal close
    if (elements.closeDetailModalBtn) {
      elements.closeDetailModalBtn.addEventListener('click', closeDetailModal);
    }
    if (elements.libraryDetailModal) {
      elements.libraryDetailModal.addEventListener('click', (e) => {
        if (e.target === elements.libraryDetailModal) closeDetailModal();
      });
    }
  }

  async function fetchLibrary(page = 1) {
    state.libraryPage = page;
    const params = new URLSearchParams({
      page: state.libraryPage,
      limit: state.libraryLimit,
      q: state.librarySearch || '',
      format: state.libraryFilter || 'all',
      sort: state.librarySort || 'newest'
    });

    try {
      const response = await fetch(`${API_BASE}/api/images?${params.toString()}`, {
        headers: getAuthHeaders()
      });

      if (!response.ok) {
        throw new Error(`Failed to load library (${response.status})`);
      }

      const data = await response.json();
      if (!data.success) throw new Error(data.error || 'Failed to fetch library.');

      renderLibraryCards(data.images || []);
      updatePagination(data.pagination);

      // Update badge count
      if (elements.libraryCountBadge) {
        elements.libraryCountBadge.textContent = data.pagination.total_items || 0;
      }

    } catch (err) {
      console.error('Error fetching library:', err);
    }
  }

  function renderLibraryCards(images) {
    if (!elements.libraryGrid) return;
    elements.libraryGrid.innerHTML = '';

    if (!images || images.length === 0) {
      if (elements.libraryEmpty) elements.libraryEmpty.style.display = 'block';
      if (elements.libraryPagination) elements.libraryPagination.style.display = 'none';
      return;
    }

    if (elements.libraryEmpty) elements.libraryEmpty.style.display = 'none';

    images.forEach(img => {
      const card = document.createElement('div');
      card.className = 'library-card';
      card.innerHTML = `
        <div class="library-thumb-wrapper" title="Click to view details & comparison">
          <img class="library-thumb" src="${img.processed_url}" alt="${escapeHtml(img.original_filename)}" loading="lazy">
          <span class="library-card-badge">${escapeHtml(img.output_format.toUpperCase())}</span>
        </div>
        <div class="library-card-body">
          <h4 class="library-card-title" title="${escapeHtml(img.original_filename)}">${escapeHtml(img.original_filename)}</h4>
          <div class="library-card-meta">
            <span>${img.image_width} × ${img.image_height}</span>
            <span>•</span>
            <span>${formatFileSize(img.file_size)}</span>
            <span>•</span>
            <span>${formatDate(img.created_at)}</span>
          </div>
          <div class="library-card-actions">
            <button type="button" class="btn-card-action primary open-studio-btn" title="Open in Studio for adjustments">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:14px;height:14px;"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg>
              <span>Edit</span>
            </button>
            <button type="button" class="btn-card-action quick-dl-btn" title="Direct Download PNG Cutout">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:14px;height:14px;"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3"/></svg>
              <span>Download</span>
            </button>
            <button type="button" class="btn-card-action danger delete-img-btn" title="Delete image from database and storage">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:14px;height:14px;"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
            </button>
          </div>
        </div>
      `;

      // Event Listeners
      card.querySelector('.library-thumb-wrapper').addEventListener('click', () => openDetailModal(img));
      card.querySelector('.open-studio-btn').addEventListener('click', () => openImageInStudio(img));
      card.querySelector('.quick-dl-btn').addEventListener('click', () => triggerDirectDownload(img.processed_url, `${stripExt(img.original_filename)}_cutout.png`));
      card.querySelector('.delete-img-btn').addEventListener('click', () => deleteLibraryImage(img.image_id));

      elements.libraryGrid.appendChild(card);
    });
  }

  function updatePagination(pagination) {
    if (!elements.libraryPagination) return;
    if (!pagination || pagination.total_pages <= 1) {
      elements.libraryPagination.style.display = 'none';
      return;
    }
    elements.libraryPagination.style.display = 'flex';
    elements.pageIndicator.textContent = `Page ${pagination.current_page} of ${pagination.total_pages}`;
    elements.prevPageBtn.disabled = !pagination.has_prev;
    elements.nextPageBtn.disabled = !pagination.has_next;
  }

  async function openImageInStudio(imgData) {
    try {
      showToast('Loading image into Studio editor...', 'info', 2000);

      state.currentImageId = imgData.image_id;
      state.originalFilename = imgData.original_filename;
      state.originalImageSrc = imgData.original_url;
      state.processedImageSrc = imgData.processed_url;
      state.imageWidth = imgData.image_width;
      state.imageHeight = imgData.image_height;

      // Update UI elements
      if (elements.metaFilename) elements.metaFilename.textContent = imgData.original_filename;
      if (elements.metaStats) elements.metaStats.textContent = `${imgData.image_width} × ${imgData.image_height} px • Persistent DB`;

      elements.sliderOrigImg.src = imgData.original_url;
      elements.sliderProcImg.src = imgData.processed_url;
      elements.cutoutOnlyImg.src = imgData.processed_url;
      elements.sideOrigImg.src = imgData.original_url;
      elements.sideProcImg.src = imgData.processed_url;

      // Hide upload, show editor
      elements.uploadSection.style.display = 'none';
      elements.processingCard.style.display = 'none';
      elements.editorSection.style.display = 'block';

      updateBackgroundPreview();
      setZoom(1.0);
      setSplit(50);

      closeDetailModal();
      elements.editorSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
      showToast('Loaded into Studio workspace!', 'success', 2500);

    } catch (e) {
      console.error('Failed to load into studio:', e);
      showToast('Failed to load image into studio.', 'error', 3000);
    }
  }

  function openDetailModal(imgData) {
    if (!elements.libraryDetailModal) return;
    state.currentDetailImage = imgData;

    if (elements.modalImageTitle) elements.modalImageTitle.textContent = imgData.original_filename;
    if (elements.modalImageBadge) elements.modalImageBadge.textContent = `${imgData.output_format.toUpperCase()} Cutout`;
    if (elements.modalOrigImg) elements.modalOrigImg.src = imgData.original_url;
    if (elements.modalProcImg) elements.modalProcImg.src = imgData.processed_url;
    if (elements.modalMetaRes) elements.modalMetaRes.textContent = `${imgData.image_width} × ${imgData.image_height} px`;
    if (elements.modalMetaSize) elements.modalMetaSize.textContent = formatFileSize(imgData.file_size);
    if (elements.modalMetaDate) elements.modalMetaDate.textContent = formatDate(imgData.created_at);
    if (elements.modalMetaStatus) elements.modalMetaStatus.textContent = imgData.processing_status || 'Completed';

    // Hook up modal actions
    if (elements.modalOpenStudioBtn) {
      elements.modalOpenStudioBtn.onclick = () => openImageInStudio(imgData);
    }
    if (elements.modalDownloadBtn) {
      elements.modalDownloadBtn.onclick = () => triggerDirectDownload(imgData.processed_url, `${stripExt(imgData.original_filename)}_cutout.png`);
    }
    if (elements.modalDeleteBtn) {
      elements.modalDeleteBtn.onclick = () => {
        closeDetailModal();
        deleteLibraryImage(imgData.image_id);
      };
    }

    elements.libraryDetailModal.style.display = 'flex';
  }

  function closeDetailModal() {
    if (elements.libraryDetailModal) elements.libraryDetailModal.style.display = 'none';
    state.currentDetailImage = null;
  }

  async function deleteLibraryImage(imageId) {
    if (!confirm('Are you sure you want to delete this image? This will permanently remove its files from persistent storage and the database.')) {
      return;
    }

    try {
      const response = await fetch(`${API_BASE}/api/images/${imageId}`, {
        method: 'DELETE',
        headers: getAuthHeaders()
      });

      if (!response.ok) throw new Error(`Delete failed (${response.status})`);
      const data = await response.json();

      showToast('Image and persistent files deleted successfully.', 'success', 3000);
      fetchLibrary(state.libraryPage);

      // If deleted image was active in studio, reset
      if (state.currentImageId === imageId) {
        resetToUpload();
      }

    } catch (err) {
      console.error('Delete error:', err);
      showToast(`Delete failed: ${err.message}`, 'error', 4000);
    }
  }

  async function clearAllHistory() {
    if (!confirm('CAUTION: Are you sure you want to permanently clear your entire image library? All saved original images, cutouts, and database records will be erased.')) {
      return;
    }

    try {
      const response = await fetch(`${API_BASE}/api/images`, {
        method: 'DELETE',
        headers: getAuthHeaders()
      });

      if (!response.ok) throw new Error(`Clear history failed (${response.status})`);
      const data = await response.json();

      showToast(data.message || 'Entire library erased.', 'success', 3500);
      fetchLibrary(1);
      resetToUpload();

    } catch (err) {
      console.error('Clear history error:', err);
      showToast(`Failed to clear history: ${err.message}`, 'error', 4000);
    }
  }

  function triggerDirectDownload(url, filename) {
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
  }

  // =========================================================================
  // Account & Session Modal Handlers
  // =========================================================================
  function setupAccountAndSession() {
    if (elements.accountBtn) {
      elements.accountBtn.addEventListener('click', () => {
        if (elements.accountModal) elements.accountModal.style.display = 'flex';
      });
    }

    if (elements.closeAccountModalBtn) {
      elements.closeAccountModalBtn.addEventListener('click', () => {
        if (elements.accountModal) elements.accountModal.style.display = 'none';
      });
    }

    if (elements.accountModal) {
      elements.accountModal.addEventListener('click', (e) => {
        if (e.target === elements.accountModal) elements.accountModal.style.display = 'none';
      });
    }

    if (elements.copySessionBtn) {
      elements.copySessionBtn.addEventListener('click', () => {
        const textToCopy = state.currentUser ? state.currentUser.user_id : state.guestSessionId;
        navigator.clipboard.writeText(textToCopy).then(() => {
          showToast('Session identifier copied to clipboard!', 'info', 2000);
        });
      });
    }

    // Account tab switching (Sign in vs Register)
    let authMode = 'login';
    if (elements.accountTabs) {
      elements.accountTabs.forEach(tab => {
        tab.addEventListener('click', () => {
          elements.accountTabs.forEach(t => t.classList.remove('active'));
          tab.classList.add('active');
          authMode = tab.getAttribute('data-tab');

          if (authMode === 'register') {
            if (elements.emailGroup) elements.emailGroup.style.display = 'flex';
            if (elements.authSubmitBtn) elements.authSubmitBtn.querySelector('span').textContent = 'Create Account';
          } else {
            if (elements.emailGroup) elements.emailGroup.style.display = 'none';
            if (elements.authSubmitBtn) elements.authSubmitBtn.querySelector('span').textContent = 'Sign In';
          }
        });
      });
    }

    // Auth Form submission
    if (elements.authForm) {
      elements.authForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = elements.authUsername.value.trim();
        const email = elements.authEmail ? elements.authEmail.value.trim() : null;

        if (!username) return;

        const endpoint = authMode === 'register' ? '/api/auth/register' : '/api/auth/login';
        try {
          const res = await fetch(`${API_BASE}${endpoint}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, email })
          });

          const data = await res.json();
          if (!res.ok || !data.success) {
            throw new Error(data.error || 'Authentication failed');
          }

          state.currentUser = data.user;
          localStorage.setItem('lumina_user', JSON.stringify(data.user));
          updateIdentityUI();
          showToast(`Welcome, ${data.user.username}!`, 'success', 3000);
          if (elements.accountModal) elements.accountModal.style.display = 'none';
          fetchLibrary(1);

        } catch (err) {
          showToast(err.message, 'error', 4000);
        }
      });
    }
  }

  // =========================================================================
  // Privacy Banner & Modal Handlers
  // =========================================================================
  function setupPrivacyBanner() {
    const isDismissed = localStorage.getItem('lumina_privacy_dismissed');
    if (!isDismissed && elements.privacyBanner) {
      elements.privacyBanner.style.display = 'block';
    } else if (elements.privacyBanner) {
      elements.privacyBanner.style.display = 'none';
    }

    if (elements.dismissPrivacyBannerBtn) {
      elements.dismissPrivacyBannerBtn.addEventListener('click', () => {
        if (elements.privacyBanner) elements.privacyBanner.style.display = 'none';
        localStorage.setItem('lumina_privacy_dismissed', 'true');
      });
    }

    if (elements.openPrivacyModalBtn) {
      elements.openPrivacyModalBtn.addEventListener('click', () => {
        if (elements.privacyModal) elements.privacyModal.style.display = 'flex';
      });
    }

    if (elements.closePrivacyModalBtn) {
      elements.closePrivacyModalBtn.addEventListener('click', () => {
        if (elements.privacyModal) elements.privacyModal.style.display = 'none';
      });
    }

    if (elements.ackPrivacyBtn) {
      elements.ackPrivacyBtn.addEventListener('click', () => {
        if (elements.privacyModal) elements.privacyModal.style.display = 'none';
        if (elements.privacyBanner) elements.privacyBanner.style.display = 'none';
        localStorage.setItem('lumina_privacy_dismissed', 'true');
      });
    }
  }

  // =========================================================================
  // Formatting Utilities
  // =========================================================================
  function formatFileSize(bytes) {
    if (!bytes || bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  }

  function formatDate(dateStr) {
    if (!dateStr) return '';
    try {
      const d = new Date(dateStr);
      return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
    } catch (e) {
      return dateStr;
    }
  }

  function stripExt(filename) {
    if (!filename) return 'image';
    const idx = filename.lastIndexOf('.');
    return idx !== -1 ? filename.substring(0, idx) : filename;
  }

  function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/[&<>"']/g, (m) => ({
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#39;'
    }[m]));
  }

  // =========================================================================
  // Initialize on DOM Ready
  // =========================================================================
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

})();
