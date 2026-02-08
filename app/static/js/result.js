// result.js

// DOM Elements
const audioEl = document.getElementById('roast-audio-el');
const playBtn = document.getElementById('play-btn');
const timeDisplay = document.getElementById('time-display');
const visualizer = document.getElementById('visualizer');
const scriptContainer = document.getElementById('script-container');
const drawer = document.getElementById('evidence-drawer');
const drawerOverlay = document.getElementById('drawer-overlay');
const closeDrawerBtn = document.getElementById('close-drawer');
const openDrawerBtn = document.getElementById('evidence-toggle');

document.addEventListener('DOMContentLoaded', () => {

    // 1. Initialize Mermaid with error handling
    try {
        mermaid.initialize({
            startOnLoad: true,
            theme: 'neutral',
            securityLevel: 'loose',
            logLevel: 'error' // Suppress warnings
        });

        // Check if diagram rendered successfully
        setTimeout(() => {
            const mermaidEl = document.querySelector('.mermaid');
            if (mermaidEl && mermaidEl.getAttribute('data-processed') !== 'true') {
                // Mermaid failed to render
                mermaidEl.innerHTML = `
                    <div class="flex flex-col items-center justify-center p-8 text-gray-600">
                        <svg class="w-12 h-12 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                        </svg>
                        <p class="text-sm font-medium">Diagram syntax error</p>
                        <p class="text-xs text-gray-500 mt-1">The architecture diagram could not be rendered</p>
                    </div>
                `;
            }
        }, 1000);
    } catch (error) {
        console.error('Mermaid initialization failed:', error);
        const mermaidEl = document.querySelector('.mermaid');
        if (mermaidEl) {
            mermaidEl.innerHTML = '<p class="text-red-500 text-sm p-4">Architecture diagram unavailable</p>';
        }
    }

    // 2. Render Markdown Guide
    const guideContent = document.getElementById('guide-content');
    if (ROAST_DATA.developer_guide) {
        guideContent.innerHTML = marked.parse(ROAST_DATA.developer_guide);
    }

    // 3. Render Script
    if (ROAST_DATA.roast_dialogue) {
        renderScript(ROAST_DATA.roast_dialogue);
    }

    // 4. Initialize Code Viewer (Lazy Load)
    loadRepoFiles();

    // 5. Audio Player
    if (audioEl && playBtn) {
        setupAudioPlayer();
    }

    // 6. Drawer Logic
    setupDrawer();

    // 7. Initialize Mermaid Zoom/Pan
    setupMermaidControls();
});

/* -------------------------------------------------------------------------- */
/*                               Script Rendering                             */
/* -------------------------------------------------------------------------- */

function renderScript(dialogue) {
    scriptContainer.innerHTML = '';
    dialogue.forEach(turn => {
        const div = document.createElement('div');
        div.className = 'script-turn';

        const isRoaster = turn.speaker.toLowerCase().includes('roast');
        const colorClass = isRoaster ? 'text-[#f85149]' : 'text-[#58a6ff]';
        const label = isRoaster ? 'AI ROASTER' : 'DEV DEFENSE';

        div.innerHTML = `
            <div class="script-label ${colorClass}">
                ${label}
            </div>
            <div class="script-text">
                ${turn.text}
            </div>
        `;
        scriptContainer.appendChild(div);
    });
}

function downloadScript() {
    let content = "# Roast Transcript\n\n";
    ROAST_DATA.roast_dialogue.forEach(turn => {
        content += `**${turn.speaker}**: ${turn.text}\n\n`;
    });
    const blob = new Blob([content], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `roast-${REPO_HASH.substring(0, 8)}.md`;
    a.click();
}

async function downloadGuide() {
    const element = document.getElementById('guide-content');

    // Create a wrapper for better PDF styling
    const wrapper = document.createElement('div');

    // FORCE styles to override any dark mode inheritance
    wrapper.style.cssText = `
        font-family: 'Inter', sans-serif;
        color: #24292f !important;
        background: #ffffff !important;
        padding: 40px;
        width: 800px; /* Fixed width for consistent rendering */
    `;

    // Clone content to manipulate it safely
    const contentClone = element.cloneNode(true);

    // Strip classes that might enforce dark mode colors if they are global
    // But since we are using inline styles on the wrapper, we mainly need to ensure text color wins.
    // Let's iterate and force color on all elements just to be safe.
    const allElements = contentClone.querySelectorAll('*');
    allElements.forEach(el => {
        el.style.color = '#24292f';
        el.style.backgroundColor = 'transparent';
        if (el.tagName === 'PRE' || el.tagName === 'CODE') {
            el.style.backgroundColor = '#f6f8fa'; // Light gray for code blocks
            el.style.color = '#24292f';
            el.style.border = '1px solid #d0d7de';
            el.style.borderRadius = '6px';
        }
    });

    wrapper.innerHTML = `
        <div style="border-bottom: 1px solid #d0d7de; padding-bottom: 20px; margin-bottom: 30px;">
            <h1 style="font-size: 24px; font-weight: 600; margin: 0; color: #24292f;">RepoRoast Developer Guide</h1>
            <p style="font-size: 14px; color: #57606a; margin-top: 5px;">Repository Analysis: ${REPO_HASH}</p>
        </div>
        <div class="markdown-body" style="font-size: 12px; line-height: 1.6; color: #24292f !important;">
            <!-- Injected Content -->
        </div>
        <div style="margin-top: 40px; border-top: 1px solid #d0d7de; padding-top: 20px; text-align: center; font-size: 10px; color: #8b949e;">
            Generated by RepoRoast AI
        </div>
    `;

    // Inject the cloned content
    wrapper.querySelector('.markdown-body').appendChild(contentClone);

    // Options for html2pdf
    const opt = {
        margin: [10, 10], // top, left, bottom, right
        filename: `developer_guide_${REPO_HASH.substring(0, 8)}.pdf`,
        image: { type: 'jpeg', quality: 0.98 },
        html2canvas: { scale: 2, useCORS: true, logging: false, backgroundColor: '#ffffff' },
        jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' },
        pagebreak: { mode: ['avoid-all', 'css', 'legacy'] }
    };

    html2pdf().set(opt).from(wrapper).save();
}

function downloadDiagram() {
    const svg = document.querySelector('.mermaid svg');
    if (!svg) {
        alert("Diagram not ready yet.");
        return;
    }
    const serializer = new XMLSerializer();
    const source = serializer.serializeToString(svg);
    const blob = new Blob([source], { type: 'image/svg+xml;charset=utf-8' });
    const url = URL.createObjectURL(blob);

    // Create link and click
    const a = document.createElement('a');
    a.href = url;
    a.download = `architecture-${REPO_HASH.substring(0, 8)}.svg`;
    a.click();
}

/* -------------------------------------------------------------------------- */
/*                                Audio Player                                */
/* -------------------------------------------------------------------------- */

let audioTimeline = [];

function setupAudioPlayer() {
    let isPlaying = false;

    // Generate Timeline estimation
    if (ROAST_DATA.roast_dialogue) {
        audioTimeline = generateTimeline(ROAST_DATA.roast_dialogue);
    }

    // Create Visualizer Bars
    visualizer.innerHTML = '<div class="absolute inset-0 bg-gradient-to-r from-[#0d1117] via-transparent to-[#0d1117] pointer-events-none z-10"></div>';
    const numBars = 40;
    for (let i = 0; i < numBars; i++) {
        const bar = document.createElement('div');
        bar.className = 'bar';
        bar.style.width = '3px';
        bar.style.margin = '0 1px';
        bar.style.backgroundColor = '#58a6ff'; // Default to blue
        bar.style.borderRadius = '2px';
        bar.style.height = '4px';
        bar.style.transition = 'height 0.1s ease, background-color 0.2s';
        visualizer.appendChild(bar);
    }
    const bars = document.querySelectorAll('.bar');

    playBtn.addEventListener('click', () => {
        if (isPlaying) {
            audioEl.pause();
            playBtn.innerHTML = '<svg class="w-5 h-5 ml-0.5" fill="currentColor" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>';
            stopVisualizer(bars);
        } else {
            audioEl.play();
            playBtn.innerHTML = '<svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/></svg>';
            startPodcastVisualizer(bars);
        }
        isPlaying = !isPlaying;
    });

    audioEl.addEventListener('timeupdate', () => {
        const currentTime = audioEl.currentTime;
        const duration = audioEl.duration || 0;

        // Update Time Display
        timeDisplay.innerText = `${formatTime(currentTime)} / ${formatTime(duration)}`;

        // Sync Avatars
        syncAvatars(currentTime, isPlaying);
    });

    audioEl.addEventListener('ended', () => {
        isPlaying = false;
        playBtn.innerHTML = '<svg class="w-5 h-5 ml-0.5" fill="currentColor" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>';
        stopVisualizer(bars);
    });
}

// Estimate timestamps based on word count (approx 2.6 words/sec for 1.1x speed)
function generateTimeline(dialogue) {
    let currentTime = 0;
    const WORDS_PER_SEC = 2.6;

    return dialogue.map(turn => {
        const wordCount = turn.text.split(/\s+/).length;
        const duration = Math.max(1.5, wordCount / WORDS_PER_SEC); // Min 1.5s per turn
        const segment = {
            start: currentTime,
            end: currentTime + duration,
            speaker: turn.speaker.toLowerCase().includes('roast') ? 'roast' : 'host'
        };
        currentTime += duration;
        return segment;
    });
}

function syncAvatars(currentTime, isPlaying) {
    if (!isPlaying) return;

    // Find current active speaker
    const totalEstimated = audioTimeline.length > 0 ? audioTimeline[audioTimeline.length - 1].end : 1;
    const actualDuration = audioEl.duration || totalEstimated;
    const scaleFactor = actualDuration / totalEstimated;

    const scaledTime = currentTime / scaleFactor;

    // Find segment
    const currentSegment = audioTimeline.find(seg => scaledTime >= seg.start && scaledTime < seg.end);

    // Default to host (Blue) if no segment found (e.g. silence or start)
    const activeSpeaker = currentSegment ? currentSegment.speaker : 'host';

    const hostAvatar = document.getElementById('avatar-host');
    const roastAvatar = document.getElementById('avatar-roast');

    // Use classes instead of inline styles for better consistency
    if (activeSpeaker === 'host') {
        // HOST ACTIVE (Blue)
        hostAvatar.classList.remove('opacity-50', 'scale-100');
        hostAvatar.classList.add('opacity-100', 'scale-110');

        // ROAST INACTIVE
        roastAvatar.classList.remove('opacity-100', 'scale-110');
        roastAvatar.classList.add('opacity-50', 'scale-100');
    } else {
        // ROAST ACTIVE (Red)
        hostAvatar.classList.remove('opacity-100', 'scale-110');
        hostAvatar.classList.add('opacity-50', 'scale-100');

        // ROAST ACTIVE
        roastAvatar.classList.remove('opacity-50', 'scale-100');
        roastAvatar.classList.add('opacity-100', 'scale-110');
    }
}

function startPodcastVisualizer(bars) {
    function animate() {
        // We now determine color based on ACTIVE speaker state in DOM
        // because syncAvatars handles the logic
        const hostActive = document.getElementById('avatar-host').classList.contains('scale-110');
        const color = hostActive ? '#58a6ff' : '#f85149';

        bars.forEach(bar => {
            const noise = Math.random();
            const h = noise > 0.6 ? Math.random() * 24 + 4 : 4;
            bar.style.height = h + 'px';
            bar.style.backgroundColor = color;
        });

        requestAnimationFrame(animate);
    }

    const id = setInterval(animate, 80);
    bars[0].dataset.interval = id;
}

function stopVisualizer(bars) {
    clearInterval(bars[0].dataset.interval);
    bars.forEach(bar => {
        bar.style.height = '4px';
        bar.style.backgroundColor = '#30363d';
    });

    // Reset both avatars to inactive state using classes
    const hostAvatar = document.getElementById('avatar-host');
    const roastAvatar = document.getElementById('avatar-roast');

    hostAvatar.classList.remove('opacity-100', 'scale-110');
    hostAvatar.classList.add('opacity-50', 'scale-100');

    roastAvatar.classList.remove('opacity-100', 'scale-110');
    roastAvatar.classList.add('opacity-50', 'scale-100');
}

function formatTime(seconds) {
    if (isNaN(seconds)) return "00:00";
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
}


/* -------------------------------------------------------------------------- */
/*                             Zoom Logic (Mermaid)                           */
/* -------------------------------------------------------------------------- */

let panState = {
    scale: 1,
    panning: false,
    pointX: 0,
    pointY: 0,
    startX: 0,
    startY: 0
}

function setupMermaidControls() {
    const wrapper = document.getElementById('mermaid-wrapper');
    const inner = document.getElementById('mermaid-inner');

    if (!wrapper || !inner) return;

    // Reset State
    panState = { scale: 1, panning: false, pointX: 0, pointY: 0, startX: 0, startY: 0 };
    updateTransform();

    // Mouse Down
    wrapper.addEventListener('mousedown', (e) => {
        e.preventDefault();
        panState.startX = e.clientX - panState.pointX;
        panState.startY = e.clientY - panState.pointY;
        panState.panning = true;
        wrapper.style.cursor = 'grabbing';
    });

    // Mouse Up
    document.addEventListener('mouseup', (e) => {
        panState.panning = false;
        wrapper.style.cursor = 'grab';
    });

    // Mouse Move
    wrapper.addEventListener('mousemove', (e) => {
        e.preventDefault();
        if (!panState.panning) return;

        panState.pointX = e.clientX - panState.startX;
        panState.pointY = e.clientY - panState.startY;
        updateTransform();
    });

    // Wheel Zoom
    wrapper.addEventListener('wheel', (e) => {
        e.preventDefault();
        const xs = (e.clientX - panState.pointX) / panState.scale;
        const ys = (e.clientY - panState.pointY) / panState.scale;

        const delta = -Math.sign(e.deltaY) * 0.1;
        const oldScale = panState.scale;
        panState.scale = Math.min(Math.max(0.5, panState.scale + delta), 5);

        const scaleRatio = panState.scale - oldScale;
        // Zoom towards mouse pointer logic would go here, 
        // but simple zoom is often sufficient for this use case if we center correctly.

        updateTransform();
    });
}

function updateTransform() {
    const inner = document.getElementById('mermaid-inner');
    if (inner) {
        inner.style.transform = `translate(${panState.pointX}px, ${panState.pointY}px) scale(${panState.scale})`;
    }
}

// Global Zoom Buttons
window.zoomMermaid = function (delta) {
    panState.scale = Math.min(Math.max(0.5, panState.scale + delta), 5);
    updateTransform();
}

window.resetZoomMermaid = function () {
    panState.scale = 1;
    panState.pointX = 0;
    panState.pointY = 0;
    updateTransform();
}


/* -------------------------------------------------------------------------- */
/*                              Evidence Drawer                               */
/* -------------------------------------------------------------------------- */

function setupDrawer() {
    function open() {
        drawer.classList.remove('translate-x-full');
        drawerOverlay.classList.remove('hidden');
        setTimeout(() => drawerOverlay.classList.remove('opacity-0'), 10);
    }

    function close() {
        drawer.classList.add('translate-x-full');
        drawerOverlay.classList.add('opacity-0');
        setTimeout(() => drawerOverlay.classList.add('hidden'), 300);
    }

    openDrawerBtn.addEventListener('click', open);
    closeDrawerBtn.addEventListener('click', close);
    drawerOverlay.addEventListener('click', close);
}

/* -------------------------------------------------------------------------- */
/*                               File Tree                                    */
/* -------------------------------------------------------------------------- */

async function loadRepoFiles() {
    const treeContainer = document.getElementById('file-tree');
    try {
        const response = await fetch(`/api/repo/${REPO_HASH}/files`);
        const data = await response.json();

        if (data.files) {
            treeContainer.innerHTML = '';
            const root = buildFileTree(data.files);
            treeContainer.appendChild(renderTree(root));
        }
    } catch (e) {
        treeContainer.innerText = "Failed to load files.";
        console.error(e);
    }
}

function buildFileTree(paths) {
    const root = {};
    paths.forEach(path => {
        const parts = path.split('/');
        let current = root;
        parts.forEach((part, index) => {
            if (!current[part]) {
                current[part] = index === parts.length - 1 ? null : {};
            }
            current = current[part];
        });
    });
    return root;
}

function renderTree(node, pathPrefix = '') {
    const div = document.createElement('div');
    div.className = pathPrefix === '' ? '' : 'tree-children pl-3 border-l border-[#30363d] ml-2.5';

    // Sort: Folders first, then files
    const entries = Object.entries(node).sort((a, b) => {
        const aIsFolder = a[1] !== null;
        const bIsFolder = b[1] !== null;
        if (aIsFolder && !bIsFolder) return -1;
        if (!aIsFolder && bIsFolder) return 1;
        return a[0].localeCompare(b[0]);
    });

    entries.forEach(([name, children]) => {
        const fullPath = pathPrefix ? `${pathPrefix}/${name}` : name;
        const item = document.createElement('div');

        if (children === null) {
            // FILE - No Icon, just text (indented to align with folder text)
            item.className = 'tree-item hover:bg-[#161b22] cursor-pointer py-1 px-2 flex items-center gap-2 text-sm text-[#8b949e]';
            item.innerHTML = `
                <span class="truncate pl-5">${name}</span>
            `;
            item.onclick = () => loadFileContent(fullPath, item);
        } else {
            // FOLDER - Text Arrow + Name (No folder icon)
            item.className = 'tree-item font-semibold text-[#c9d1d9] hover:bg-[#161b22] cursor-pointer py-1 px-2 flex items-center gap-2 text-sm';
            item.innerHTML = `
                <span class="icon-arrow leading-none text-[#8b949e] w-4 text-center transition-transform duration-200">▶</span>
                <span class="truncate">${name}</span>
            `;

            const childrenContainer = renderTree(children, fullPath);
            childrenContainer.style.display = 'none'; // Default collapsed

            item.onclick = (e) => {
                e.stopPropagation();
                const arrow = item.querySelector('.icon-arrow');
                if (childrenContainer.style.display === 'block') {
                    childrenContainer.style.display = 'none';
                    arrow.style.transform = 'rotate(0deg)';
                } else {
                    childrenContainer.style.display = 'block';
                    arrow.style.transform = 'rotate(90deg)';
                }
            };
            div.appendChild(item);
            div.appendChild(childrenContainer);
            return; // Append handled above
        }
        div.appendChild(item);
    });

    return div;
}

async function loadFileContent(path, element) {
    document.querySelectorAll('.tree-item').forEach(el => el.classList.remove('active'));
    element.classList.add('active');

    const pathDisplay = document.getElementById('current-file-path');
    const codeBlock = document.getElementById('code-content');

    pathDisplay.innerText = path;
    codeBlock.innerText = "Loading...";

    try {
        const response = await fetch(`/api/repo/${REPO_HASH}/file?path=${encodeURIComponent(path)}`);
        const data = await response.json();

        // Remove highlighting classes
        codeBlock.className = 'text-xs font-mono block bg-transparent !p-0';
        codeBlock.innerText = data.content;

        // Add new class and highlight
        codeBlock.classList.add(`language-${data.language ? data.language.toLowerCase() : 'text'}`);
        hljs.highlightElement(codeBlock);

    } catch (e) {
        codeBlock.innerText = "Error loading content.";
    }
}
