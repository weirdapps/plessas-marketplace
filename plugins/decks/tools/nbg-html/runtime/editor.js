/* NBG HTML deck runtime: in-place editing, free layout, saving, presenting, printing.
 *
 * nbg_html.py inlines this file into every deck it builds, so a deck opened from
 * disk, mail or a share needs nothing installed. It never touches the network:
 * no fonts, no scripts, no telemetry, no AI calls.
 *
 * Text       double-click to edit (Enter applies, Shift+Enter breaks the line,
 *            Esc cancels; paste arrives as plain text); B / I / U, size, colour
 *            and alignment from the text toolbar.
 * Shapes     click selects (a second click selects what is inside), Shift+click
 *            adds, drag on empty slide space draws a selection box, Tab selects the
 *            enclosing shape. Drag to move (snaps to the gutter, the centre and the
 *            other shapes; hold Alt to place freely), handles resize (Shift keeps
 *            the proportions), arrows nudge (Shift 10 px, Alt resizes). The shape
 *            toolbar sets X / Y / W / H, fill, border, corners, opacity, text size,
 *            colour and alignment, order, align and distribute.
 * Keys       Delete, Ctrl/Cmd+D duplicate, C / V copy and paste, A select all,
 *            ] / [ bring forward / send back, Z undo, Y redo, S save, P PDF.
 *            P presents full screen, Esc goes back.
 * Right-click  insert a text box, a box or a picture; duplicate, move or delete an
 *            item or a slide; add a slide.
 *
 * Moves are written as the CSS translate property and sizes as width / height, so
 * the design system's layout stays underneath and Reset puts a shape back.
 * Edits are kept in this browser (localStorage) until saved, so a reload loses
 * nothing. Save writes the same self-contained deck, runtime included.
 *
 * Opened as deck.html?nbg-check (headless Chrome, from `decks-py html-check`),
 * it shows no UI and writes a layout report into the page instead.
 */
(function () {
  'use strict';
  if (window.nbgDeck) return;

  var VERSION = '2';
  var W = 1920;
  var H = 1080;
  var SNAP = 8;
  var ITEM_SEL = 'li, .card, .kpi, .step, tr, .bar, .row, figure, .legend > span, ol.toc > li';
  var TEXT_SKIP = 'svg, .notes, [data-nbg-ui]';
  var INLINE = /^(inline|inline-block|contents)$/;
  var STYLE_PROPS = ['translate', 'width', 'height', 'flex', 'z-index', 'background', 'background-color', 'border',
    'border-radius', 'opacity', 'font-size', 'text-align', 'color', 'max-width', 'max-height'];
  var doc = document;
  var root = doc.documentElement;
  var main = doc.querySelector('main.deck');
  if (!main) return;

  if (/[?&]nbg-check\b/.test(location.search)) {
    root.classList.add('nbg-check');
    runCheck();
    return;
  }

  // ---------------------------------------------------------------- helpers
  function slides() { return Array.prototype.slice.call(main.querySelectorAll(':scope > .slide')); }
  function ui(tag, attrs, htmlText) {
    var n = doc.createElement(tag);
    n.setAttribute('data-nbg-ui', '');
    if (attrs) Object.keys(attrs).forEach(function (k) { n.setAttribute(k, attrs[k]); });
    if (htmlText != null) n.innerHTML = htmlText;
    return n;
  }
  function cssVar(name) { return getComputedStyle(root).getPropertyValue(name).trim(); }
  function pxVar(name) { return parseFloat(cssVar(name)) || 0; }
  function hash(s) {
    var h = 5381;
    for (var i = 0; i < s.length; i++) h = ((h << 5) + h + s.charCodeAt(i)) | 0;
    return (h >>> 0).toString(36);
  }
  function cleanNode(node) {
    node.querySelectorAll('[data-nbg-ui]').forEach(function (n) { n.remove(); });
    node.querySelectorAll('[contenteditable]').forEach(function (n) { n.removeAttribute('contenteditable'); });
    var all = [node].concat(Array.prototype.slice.call(node.querySelectorAll('[class*="nbg-"]')));
    all.forEach(function (n) {
      if (!n.classList) return;
      Array.prototype.slice.call(n.classList).forEach(function (c) { if (c.indexOf('nbg-') === 0) n.classList.remove(c); });
      if (n.getAttribute('class') === '') n.removeAttribute('class');
    });
    return node;
  }
  function cleanMain() { return cleanNode(main.cloneNode(true)).innerHTML; }
  function isPresent() { return root.classList.contains('nbg-present'); }
  function inField(t) { return t && t.closest && t.closest('input, select, textarea'); }
  function round(n) { return Math.round(n * 10) / 10; }

  // ------------------------------------------------------------- UI styling
  var uiCss = [
    '[data-nbg-ui]{font-family:' + cssVar('--font-stack') + ';box-sizing:border-box;font-size:13px;color:var(--c-dark-teal)}',
    '.nbg-panel{position:fixed;z-index:2147483000;display:flex;gap:4px;align-items:center;flex-wrap:wrap;background:var(--c-white);border:1px solid var(--c-light-grey);border-radius:8px;padding:5px 7px}',
    '.nbg-panel button,#nbg-menu button{font:inherit;border:0;background:transparent;color:var(--c-dark-teal);cursor:pointer;border-radius:5px;padding:4px 8px;min-width:26px}',
    '.nbg-panel button:hover,#nbg-menu button:hover,#nbg-menu button:focus{background:var(--c-takeaway-tint);outline:none}',
    '.nbg-panel select,.nbg-panel input{font:inherit;color:var(--c-dark-teal);border:1px solid var(--c-light-grey);border-radius:5px;padding:2px 4px;background:var(--c-white)}',
    '.nbg-panel input{width:62px}',
    '.nbg-panel .nbg-sep{width:1px;align-self:stretch;background:var(--c-light-grey);margin:0 3px}',
    '.nbg-panel .nbg-lbl{color:var(--c-caption-grey);padding:0 2px}',
    '.nbg-panel .nbg-sw{width:20px;height:20px;min-width:20px;padding:0;margin:0 1px;border-radius:50%;border:1px solid var(--c-light-grey)}',
    '.nbg-panel .nbg-sw.nbg-none{background:linear-gradient(135deg,var(--c-white) 45%,var(--c-alert) 45%,var(--c-alert) 55%,var(--c-white) 55%)}',
    '#nbg-bar{top:12px;right:12px}',
    '#nbg-bar .nbg-dot{width:8px;height:8px;border-radius:50%;background:var(--c-gold);display:none}',
    '#nbg-bar.nbg-dirty .nbg-dot{display:inline-block}',
    '#nbg-bar .nbg-hint{color:var(--c-caption-grey);padding:0 6px}',
    '#nbg-fmt,#nbg-shape{display:none;left:50%;transform:translateX(-50%);bottom:14px;max-width:96vw;justify-content:center}',
    '#nbg-menu{position:fixed;z-index:2147483002;display:none;flex-direction:column;min-width:240px;background:var(--c-white);border:1px solid var(--c-light-grey);border-radius:8px;padding:5px}',
    '#nbg-menu button{text-align:left;width:100%}',
    '#nbg-menu hr{border:0;border-top:1px solid var(--c-light-grey);margin:4px 0}',
    '#nbg-toast{position:fixed;left:50%;top:64px;transform:translateX(-50%);z-index:2147483003;background:var(--c-dark-teal);color:var(--c-white);border-radius:8px;padding:10px 16px;font-size:14px;display:none;max-width:80vw}',
    '#nbg-frame{position:fixed;z-index:2147482990;display:none;border:1.5px solid var(--c-teal);pointer-events:none}',
    '#nbg-frame i{position:absolute;width:12px;height:12px;margin:-6px 0 0 -6px;background:var(--c-white);border:1.5px solid var(--c-teal);pointer-events:auto;border-radius:2px}',
    '#nbg-frame .nbg-size{position:absolute;right:0;top:-24px;background:var(--c-teal);color:var(--c-white);font-size:11px;padding:2px 6px;border-radius:4px;white-space:nowrap}',
    '#nbg-band{position:fixed;z-index:2147482991;display:none;border:1px dashed var(--c-teal);background:rgba(0,123,133,.08);pointer-events:none}',
    '.nbg-guide{position:fixed;z-index:2147482992;background:var(--c-alert);pointer-events:none}',
    '.nbg-sel{outline:1.5px dashed var(--c-teal)!important;outline-offset:2px}',
    '.nbg-hover{outline:1.5px dashed var(--c-cyan)!important;outline-offset:2px}',
    '.nbg-editing{outline:3px solid var(--c-teal)!important;outline-offset:4px;cursor:text}',
    'main.deck .slide img{-webkit-user-drag:none}',
    'html:not(.nbg-present) main.deck .slide{cursor:default;user-select:none;-webkit-user-select:none}',
    'html:not(.nbg-present) main.deck .nbg-editing{user-select:text;-webkit-user-select:text}',
    'html.nbg-present [data-nbg-ui]:not(#nbg-toast){display:none!important}'
  ].join('\n');

  var zoomStyle = ui('style', { id: 'nbg-zoom' });
  doc.head.appendChild(ui('style', { id: 'nbg-ui-style' }, uiCss));
  doc.head.appendChild(zoomStyle);

  function fit() {
    var z = isPresent() ? Math.min(innerWidth / W, innerHeight / H) : Math.min(1, Math.max(0.2, (innerWidth - 56) / W));
    zoomStyle.textContent = ':root{--nbg-zoom:' + z.toFixed(4) + '}';
    drawFrame();
  }

  // ------------------------------------------------------------- UI chrome
  var bar = ui('div', { id: 'nbg-bar', class: 'nbg-panel' },
    '<span class="nbg-dot" title="Unsaved edits"></span>' +
    '<span class="nbg-hint">Click to select, double-click to edit text, right-click for more</span>' +
    '<button data-a="undo" title="Undo (Ctrl/Cmd+Z)">&#8630;</button>' +
    '<button data-a="redo" title="Redo (Ctrl/Cmd+Y)">&#8631;</button>' +
    '<button data-a="present" title="Present (P)">Present</button>' +
    '<button data-a="save" title="Save as HTML (Ctrl/Cmd+S)">Save</button>' +
    '<button data-a="pdf" title="Export to PDF (Ctrl/Cmd+P)">PDF</button>' +
    '<button data-a="more" title="More">&#8943;</button>');
  var toast = ui('div', { id: 'nbg-toast', role: 'status' });
  var menu = ui('div', { id: 'nbg-menu', role: 'menu' });
  var fmt = ui('div', { id: 'nbg-fmt', class: 'nbg-panel' });
  var tools = ui('div', { id: 'nbg-shape', class: 'nbg-panel' });
  var frame = ui('div', { id: 'nbg-frame' });
  var band = ui('div', { id: 'nbg-band' });
  [bar, toast, menu, fmt, tools, frame, band].forEach(function (n) { doc.body.appendChild(n); });
  ['nw', 'n', 'ne', 'e', 'se', 's', 'sw', 'w'].forEach(function (h) {
    var i = ui('i', { 'data-h': h });
    var x = h.indexOf('w') >= 0 ? '0' : h.indexOf('e') >= 0 ? '100%' : '50%';
    var y = h.indexOf('n') >= 0 ? '0' : h.indexOf('s') >= 0 ? '100%' : '50%';
    i.style.left = x;
    i.style.top = y;
    i.style.cursor = h + '-resize';
    frame.appendChild(i);
  });
  var sizeTag = ui('span', { class: 'nbg-size' });
  frame.appendChild(sizeTag);

  var toastTimer = 0;
  function say(msg, ms) {
    toast.textContent = msg;
    toast.style.display = 'block';
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { toast.style.display = 'none'; }, ms || 3000);
  }

  // ------------------------------------------------- persistence, undo, redo
  var original = cleanMain();
  var KEY = 'nbg-deck:' + location.pathname + ':' + hash(original);
  var undoStack = [];
  var redoStack = [];

  function store(val) {
    try {
      if (val == null) localStorage.removeItem(KEY);
      else localStorage.setItem(KEY, val);
    } catch (e) { /* private mode or full: the edits still live in the page */ }
  }
  function markDirty() {
    var now = cleanMain();
    bar.classList.toggle('nbg-dirty', now !== original);
    store(now === original ? null : now);
    drawFrame();
  }
  function checkpoint() {
    undoStack.push(cleanMain());
    if (undoStack.length > 80) undoStack.shift();
    redoStack.length = 0;
  }
  function setMain(htmlText) {
    clearSel();
    main.innerHTML = htmlText;
    markDirty();
  }
  function doUndo() {
    if (editing) cancel();
    if (!undoStack.length) { say('Nothing to undo'); return; }
    redoStack.push(cleanMain());
    setMain(undoStack.pop());
  }
  function doRedo() {
    if (!redoStack.length) { say('Nothing to redo'); return; }
    undoStack.push(cleanMain());
    setMain(redoStack.pop());
  }

  try {
    var kept = localStorage.getItem(KEY);
    if (kept && kept !== original) {
      main.innerHTML = kept;
      bar.classList.add('nbg-dirty');
      say('Your unsaved edits were restored. Save to keep them, or More > Discard all edits.', 6000);
    }
  } catch (e) { /* storage blocked */ }

  // --------------------------------------------------------- geometry
  function zoomOf(slide) { return slide.getBoundingClientRect().width / W || 1; }
  function boxOf(n) {
    var s = n.closest('.slide');
    var r = n.getBoundingClientRect();
    var sr = s.getBoundingClientRect();
    var z = sr.width / W || 1;
    return { x: (r.left - sr.left) / z, y: (r.top - sr.top) / z, w: r.width / z, h: r.height / z };
  }
  function union(list) {
    var b = null;
    list.forEach(function (n) {
      var r = boxOf(n);
      if (!b) { b = { x: r.x, y: r.y, r: r.x + r.w, b: r.y + r.h }; return; }
      b.x = Math.min(b.x, r.x); b.y = Math.min(b.y, r.y); b.r = Math.max(b.r, r.x + r.w); b.b = Math.max(b.b, r.y + r.h);
    });
    return b ? { x: b.x, y: b.y, w: b.r - b.x, h: b.b - b.y } : null;
  }
  function getT(n) {
    var p = (n.style.translate || '').split(/\s+/).map(parseFloat);
    return [p[0] || 0, p[1] || 0];
  }
  function setT(n, x, y) {
    x = round(x); y = round(y);
    if (!x && !y) n.style.removeProperty('translate');
    else n.style.translate = x + 'px ' + y + 'px';
  }
  function setSize(n, w, h) {
    if (w != null) n.style.width = Math.max(8, round(w)) + 'px';
    if (h != null) n.style.height = Math.max(8, round(h)) + 'px';
    var pd = n.parentElement && getComputedStyle(n.parentElement).display;
    if (pd && /flex/.test(pd)) n.style.flex = 'none';
    if (n.tagName === 'IMG') { n.style.maxWidth = 'none'; n.style.maxHeight = 'none'; }
  }

  // ------------------------------------------------------------ text edit
  var editing = null;
  var before = '';

  function textBlock(node) {
    if (node && node.nodeType !== 1) node = node.parentElement;
    if (!node || node.closest(TEXT_SKIP) || !node.closest('.slide')) return null;
    while (node && !node.classList.contains('slide') && INLINE.test(getComputedStyle(node).display)) node = node.parentElement;
    if (!node || node.classList.contains('slide') || !main.contains(node)) return null;
    // A block that holds other blocks (a card clicked on its padding) is not a text block.
    for (var i = 0; i < node.children.length; i++) {
      var c = node.children[i];
      if (c.tagName !== 'BR' && !INLINE.test(getComputedStyle(c).display)) return null;
    }
    return node.textContent.trim() || /^(TD|TH|P|LI|H\d|DIV|SPAN)$/.test(node.tagName) ? node : null;
  }

  function startEdit(node) {
    if (editing) commit();
    clearSel();
    checkpoint();
    editing = node;
    before = node.innerHTML;
    node.setAttribute('contenteditable', 'true');
    node.classList.add('nbg-editing');
    node.focus();
    var r = doc.createRange();
    r.selectNodeContents(node);
    r.collapse(false);
    var s = getSelection();
    s.removeAllRanges();
    s.addRange(r);
    fmt.style.display = 'flex';
  }
  function stopEdit() {
    var n = editing;
    n.removeAttribute('contenteditable');
    n.classList.remove('nbg-editing');
    // Browsers leave stray wrappers (div, font) around typed text.
    n.querySelectorAll('div, font').forEach(function (w) {
      if (w.tagName === 'DIV' && w.previousSibling) w.insertAdjacentElement('beforebegin', doc.createElement('br'));
      while (w.firstChild) w.parentNode.insertBefore(w.firstChild, w);
      w.remove();
    });
    editing = null;
    fmt.style.display = 'none';
  }
  function commit() {
    if (!editing) return;
    var changed = editing.innerHTML !== before;
    stopEdit();
    if (changed) markDirty();
    else undoStack.pop();
  }
  function cancel() {
    if (!editing) return;
    editing.innerHTML = before;
    stopEdit();
    undoStack.pop();
  }

  var TEXT_COLOURS = ['dark-teal', 'teal', 'cyan', 'body-text', 'caption-grey', 'white', 'alert', 'success'];
  var FILLS = ['white', 'off-white', 'takeaway-tint', 'highlight-tint', 'gold-tint', 'ownership-ask-fill', 'teal', 'dark-teal', 'cyan', 'light-grey'];
  function swatches(attr, names, none) {
    return (none ? '<button class="nbg-sw nbg-none" ' + attr + '="none" title="None"></button>' : '') +
      names.map(function (n) {
        return '<button class="nbg-sw" ' + attr + '="' + n + '" title="' + n.replace(/-/g, ' ') + '" style="background:var(--c-' + n + ')"></button>';
      }).join('');
  }

  fmt.innerHTML =
    '<button data-f="bold" title="Bold (Ctrl/Cmd+B)"><b>B</b></button>' +
    '<button data-f="italic" title="Italic (Ctrl/Cmd+I)"><i>I</i></button>' +
    '<button data-f="underline" title="Underline (Ctrl/Cmd+U)"><u>U</u></button>' +
    '<button data-f="smaller" title="Smaller">A&#8722;</button>' +
    '<button data-f="bigger" title="Bigger">A+</button>' +
    '<span class="nbg-sep"></span>' + swatches('data-c', TEXT_COLOURS) + '<span class="nbg-sep"></span>' +
    '<button data-f="left" title="Align left">&#8676;</button>' +
    '<button data-f="center" title="Centre">&#8596;</button>' +
    '<button data-f="right" title="Align right">&#8677;</button>' +
    '<span class="nbg-sep"></span>' +
    '<button data-f="removeFormat" title="Clear formatting">Clear</button>' +
    '<button data-f="done" title="Apply (Enter)">Done</button>';

  function sizeSelection(factor) {
    var s = getSelection();
    if (!s.rangeCount || s.isCollapsed) {
      var cur = parseFloat(getComputedStyle(editing).fontSize);
      editing.style.fontSize = Math.round(cur * factor) + 'px';
      return;
    }
    var anchor = s.anchorNode.nodeType === 1 ? s.anchorNode : s.anchorNode.parentElement;
    var size = Math.round(parseFloat(getComputedStyle(anchor).fontSize) * factor);
    doc.execCommand('styleWithCSS', false, false);
    doc.execCommand('fontSize', false, '7');
    editing.querySelectorAll('font[size="7"]').forEach(function (f) {
      var sp = doc.createElement('span');
      sp.style.fontSize = size + 'px';
      while (f.firstChild) sp.appendChild(f.firstChild);
      f.replaceWith(sp);
    });
  }
  fmt.addEventListener('mousedown', function (e) { e.preventDefault(); });
  fmt.addEventListener('click', function (e) {
    var b = e.target.closest('button');
    if (!b || !editing) return;
    var f = b.dataset.f;
    if (f === 'done') { commit(); return; }
    if (b.dataset.c) {
      doc.execCommand('styleWithCSS', false, true);
      doc.execCommand('foreColor', false, cssVar('--c-' + b.dataset.c));
      return;
    }
    if (f === 'smaller' || f === 'bigger') { sizeSelection(f === 'bigger' ? 1.1 : 1 / 1.1); return; }
    if (f === 'left' || f === 'center' || f === 'right') { editing.style.textAlign = f; return; }
    doc.execCommand('styleWithCSS', false, false);
    doc.execCommand(f, false, null);
  });

  // ------------------------------------------------------------- selection
  var sel = [];

  function shapeFrom(t) {
    if (!t || t.nodeType !== 1 || !main.contains(t) || t.closest('.notes')) return null;
    var svg = t.closest('svg');
    if (svg) {
      while (svg.parentElement && svg.parentElement.closest('svg')) svg = svg.parentElement.closest('svg');
      t = svg;
    }
    var n = t;
    while (n && n !== main && !n.classList.contains('slide') && n.tagName !== 'IMG' && n.tagName.toLowerCase() !== 'svg' &&
      INLINE.test(getComputedStyle(n).display)) n = n.parentElement;
    if (!n || n === main || n.classList.contains('slide') || n.classList.contains('body')) return null;
    return n;
  }
  // A bare layout wrapper (the grid of cards, the KPI row): no fill, no border,
  // several shapes inside. Clicks and selection boxes go through it to its shapes.
  function isBare(n) {
    if (n.classList.contains('free') || n.tagName === 'IMG' || n.tagName.toLowerCase() === 'svg') return false;
    var cs = getComputedStyle(n);
    return cs.backgroundColor === 'rgba(0, 0, 0, 0)' && cs.backgroundImage === 'none' &&
      !parseFloat(cs.borderTopWidth) && !parseFloat(cs.borderLeftWidth) && childShapes(n).length > 1 && !textBlock(n);
  }
  // The shapes a click passes through, outermost first: what the first click
  // selects, then one level further in with every click on the selection.
  function chainFor(hit) {
    var list = [];
    for (var n = hit; n; n = parentShape(n)) if (!isBare(n)) list.unshift(n);
    return list;
  }
  function parentShape(n) {
    var p = n.parentElement;
    while (p && p !== main && !p.classList.contains('slide') && (p.classList.contains('body') || INLINE.test(getComputedStyle(p).display))) {
      if (p.classList.contains('body')) return null;
      p = p.parentElement;
    }
    return p && p !== main && !p.classList.contains('slide') ? p : null;
  }
  function childShapes(n) {
    return Array.prototype.filter.call(n.children, function (c) { return c.getClientRects().length && !c.closest('.notes'); });
  }
  function topShapes(slide) {
    var list = [];
    Array.prototype.forEach.call(slide.children, function (c) {
      if (c.classList.contains('notes')) return;
      if (c.classList.contains('body')) list = list.concat(childShapes(c));
      else list.push(c);
    });
    return list.filter(function (n) { return n.getClientRects().length; });
  }
  function setSel(list) {
    sel.forEach(function (n) { n.classList.remove('nbg-sel'); });
    // Keep one slide, and never an element together with its own container.
    var slide = list.length ? list[0].closest('.slide') : null;
    sel = list.filter(function (n, i) {
      return n.closest('.slide') === slide && list.indexOf(n) === i &&
        !list.some(function (o) { return o !== n && o.contains(n); });
    });
    sel.forEach(function (n) { n.classList.add('nbg-sel'); n.classList.remove('nbg-hover'); });
    if (hoverEl && isSel(hoverEl)) hoverEl = null;
    drawFrame();
    syncTools();
  }
  function clearSel() { if (sel.length) setSel([]); }
  function isSel(n) { return sel.indexOf(n) >= 0; }

  function drawFrame() {
    if (!sel.length || isPresent() || !sel[0].isConnected) {
      frame.style.display = 'none';
      if (sel.length && !sel[0].isConnected) { sel = []; syncTools(); }
      return;
    }
    var l = Infinity, t = Infinity, r = -Infinity, b = -Infinity;
    sel.forEach(function (n) {
      var q = n.getBoundingClientRect();
      l = Math.min(l, q.left); t = Math.min(t, q.top); r = Math.max(r, q.right); b = Math.max(b, q.bottom);
    });
    frame.style.display = 'block';
    frame.style.left = l + 'px';
    frame.style.top = t + 'px';
    frame.style.width = (r - l) + 'px';
    frame.style.height = (b - t) + 'px';
    var u = union(sel);
    sizeTag.textContent = Math.round(u.w) + ' × ' + Math.round(u.h) + (sel.length > 1 ? '  (' + sel.length + ')' : '');
    syncGeom(u);
  }
  addEventListener('scroll', drawFrame, true);
  addEventListener('resize', fit);

  // ----------------------------------------------------------- shape toolbar
  tools.innerHTML =
    '<button data-s="parent" title="Select the enclosing shape (Tab)">&#8613;</button>' +
    '<span class="nbg-lbl">X</span><input data-g="x" type="number">' +
    '<span class="nbg-lbl">Y</span><input data-g="y" type="number">' +
    '<span class="nbg-lbl">W</span><input data-g="w" type="number" min="8">' +
    '<span class="nbg-lbl">H</span><input data-g="h" type="number" min="8">' +
    '<span class="nbg-sep"></span><span class="nbg-lbl">Fill</span>' + swatches('data-fill', FILLS, true) +
    '<span class="nbg-sep"></span>' +
    '<select data-p="border" title="Border"><option value="">Border</option><option value="none">None</option><option value="2px solid var(--c-light-grey)">Thin grey</option><option value="2px solid var(--c-teal)">Thin teal</option><option value="4px solid var(--c-teal)">Thick teal</option><option value="3px solid var(--c-gold)">Gold</option><option value="3px solid var(--c-alert)">Red</option></select>' +
    '<select data-p="border-radius" title="Corners"><option value="">Corners</option><option value="0">Square</option><option value="6px">Soft</option><option value="16px">Round</option><option value="999px">Pill</option></select>' +
    '<select data-p="opacity" title="Opacity"><option value="">Opacity</option><option value="1">100%</option><option value="0.8">80%</option><option value="0.6">60%</option><option value="0.4">40%</option><option value="0.2">20%</option></select>' +
    '<select data-p="color" title="Text colour"><option value="">Text colour</option>' +
    TEXT_COLOURS.map(function (c) { return '<option value="var(--c-' + c + ')">' + c.replace(/-/g, ' ') + '</option>'; }).join('') + '</select>' +
    '<button data-s="smaller" title="Smaller text">A&#8722;</button><button data-s="bigger" title="Bigger text">A+</button>' +
    '<button data-s="tleft" title="Text left">&#8676;</button><button data-s="tcenter" title="Text centre">&#8596;</button><button data-s="tright" title="Text right">&#8677;</button>' +
    '<span class="nbg-sep"></span>' +
    '<button data-s="front" title="Bring to front (Ctrl/Cmd+Shift+])">Front</button><button data-s="back" title="Send to back (Ctrl/Cmd+Shift+[)">Back</button>' +
    '<span class="nbg-sep"></span><span class="nbg-lbl" data-alignlbl>Align</span>' +
    '<button data-al="l" title="Align left">&#9703;</button><button data-al="c" title="Align centre">&#9707;</button><button data-al="r" title="Align right">&#9704;</button>' +
    '<button data-al="t" title="Align top">&#11205;</button><button data-al="m" title="Align middle">&#9644;</button><button data-al="b" title="Align bottom">&#11206;</button>' +
    '<button data-al="dh" title="Distribute horizontally (3 or more)">&#8660;</button><button data-al="dv" title="Distribute vertically (3 or more)">&#8661;</button>' +
    '<span class="nbg-sep"></span>' +
    '<button data-s="dup" title="Duplicate (Ctrl/Cmd+D)">Duplicate</button>' +
    '<button data-s="del" title="Delete (Del)">Delete</button>' +
    '<button data-s="reset" title="Back to the design system\'s position, size and style">Reset</button>' +
    '<button data-s="done" title="Deselect (Esc)">Done</button>';

  function syncTools() {
    tools.style.display = sel.length && !editing && !isPresent() ? 'flex' : 'none';
    var lbl = tools.querySelector('[data-alignlbl]');
    if (lbl) lbl.textContent = sel.length > 1 ? 'Align' : 'Align to slide';
    tools.querySelectorAll('select').forEach(function (s) { s.value = ''; });
  }
  function syncGeom(u) {
    ['x', 'y', 'w', 'h'].forEach(function (k) {
      var inp = tools.querySelector('[data-g="' + k + '"]');
      if (inp && doc.activeElement !== inp) inp.value = Math.round(u[k]);
    });
  }

  function change(label, fn) {
    if (editing) commit();
    checkpoint();
    fn();
    markDirty();
    if (label) say(label, 1500);
  }
  function eachSel(fn) { sel.forEach(fn); }

  function moveBy(dx, dy) { eachSel(function (n) { var t = getT(n); setT(n, t[0] + dx, t[1] + dy); }); }
  function moveTo(key, val) {
    var u = union(sel);
    if (key === 'x') moveBy(val - u.x, 0);
    else if (key === 'y') moveBy(0, val - u.y);
    else scaleSel(key === 'w' ? val / u.w : 1, key === 'h' ? val / u.h : 1, u);
  }
  function scaleSel(sx, sy, u) {
    var boxes = sel.map(boxOf);
    sel.forEach(function (n, i) {
      var b = boxes[i];
      var t = getT(n);
      var nx = u.x + (b.x - u.x) * sx;
      var ny = u.y + (b.y - u.y) * sy;
      setSize(n, b.w * sx, b.h * sy);
      setT(n, t[0] + nx - b.x, t[1] + ny - b.y);
    });
  }
  function resetShape(n) {
    STYLE_PROPS.forEach(function (p) { n.style.removeProperty(p); });
    if (n.style.position === 'relative' && !n.classList.contains('free')) n.style.removeProperty('position');
    if (!n.getAttribute('style')) n.removeAttribute('style');
  }
  function zOrder(front) {
    eachSel(function (n) {
      var sibs = Array.prototype.filter.call(n.parentElement.children, function (c) { return c !== n; });
      var zs = sibs.map(function (c) { return parseInt(getComputedStyle(c).zIndex, 10) || 0; });
      var z = front ? Math.max.apply(null, zs.concat([0])) + 1 : Math.min.apply(null, zs.concat([0])) - 1;
      if (getComputedStyle(n).position === 'static') n.style.position = 'relative';
      if (z < 0) n.parentElement.style.isolation = 'isolate';
      n.style.zIndex = z;
    });
  }
  function align(kind) {
    var area;
    if (sel.length > 1) area = union(sel);
    else {
      var g = pxVar('--gutter');
      var top = pxVar('--body-top');
      area = { x: g, y: top, w: W - 2 * g, h: pxVar('--body-bottom') - top };
    }
    if (kind === 'dh' || kind === 'dv') {
      if (sel.length < 3) { say('Distribute needs three or more shapes'); return; }
      var hz = kind === 'dh';
      var items = sel.map(function (n) { return { n: n, b: boxOf(n) }; })
        .sort(function (a, b) { return hz ? a.b.x - b.b.x : a.b.y - b.b.y; });
      var total = items.reduce(function (s, it) { return s + (hz ? it.b.w : it.b.h); }, 0);
      var gap = ((hz ? area.w : area.h) - total) / (items.length - 1);
      var pos = hz ? area.x : area.y;
      items.forEach(function (it) {
        var t = getT(it.n);
        if (hz) setT(it.n, t[0] + pos - it.b.x, t[1]);
        else setT(it.n, t[0], t[1] + pos - it.b.y);
        pos += (hz ? it.b.w : it.b.h) + gap;
      });
      return;
    }
    eachSel(function (n) {
      var b = boxOf(n);
      var t = getT(n);
      var dx = 0, dy = 0;
      if (kind === 'l') dx = area.x - b.x;
      if (kind === 'c') dx = area.x + area.w / 2 - (b.x + b.w / 2);
      if (kind === 'r') dx = area.x + area.w - (b.x + b.w);
      if (kind === 't') dy = area.y - b.y;
      if (kind === 'm') dy = area.y + area.h / 2 - (b.y + b.h / 2);
      if (kind === 'b') dy = area.y + area.h - (b.y + b.h);
      setT(n, t[0] + dx, t[1] + dy);
    });
  }
  function duplicate() {
    var copies = sel.map(function (n) {
      var c = cleanNode(n.cloneNode(true));
      n.after(c);
      if (c.classList.contains('free')) { var t = getT(c); setT(c, t[0] + 24, t[1] + 24); }
      return c;
    });
    setSel(copies);
  }
  function removeSel() {
    var gone = sel.slice();
    clearSel();
    gone.forEach(function (n) { n.remove(); });
  }

  tools.addEventListener('mousedown', function (e) { if (!inField(e.target)) e.preventDefault(); });
  tools.addEventListener('click', function (e) {
    var b = e.target.closest('button');
    if (!b || !sel.length) return;
    var s = b.dataset.s;
    if (b.dataset.fill) {
      change(null, function () {
        eachSel(function (n) {
          if (b.dataset.fill === 'none') n.style.background = 'transparent';
          else n.style.background = 'var(--c-' + b.dataset.fill + ')';
        });
      });
    } else if (b.dataset.al) change(null, function () { align(b.dataset.al); });
    else if (s === 'parent') selectParent();
    else if (s === 'done') clearSel();
    else if (s === 'dup') change('Duplicated', duplicate);
    else if (s === 'del') change('Deleted', removeSel);
    else if (s === 'reset') change('Reset', function () { eachSel(resetShape); });
    else if (s === 'front' || s === 'back') change(null, function () { zOrder(s === 'front'); });
    else if (s === 'smaller' || s === 'bigger') {
      change(null, function () {
        eachSel(function (n) { n.style.fontSize = Math.round(parseFloat(getComputedStyle(n).fontSize) * (s === 'bigger' ? 1.1 : 1 / 1.1)) + 'px'; });
      });
    } else if (s === 'tleft' || s === 'tcenter' || s === 'tright') {
      change(null, function () { eachSel(function (n) { n.style.textAlign = s.slice(1); }); });
    }
    drawFrame();
  });
  tools.addEventListener('change', function (e) {
    var t = e.target;
    if (!sel.length) return;
    if (t.dataset.p && t.value) {
      change(null, function () { eachSel(function (n) { n.style.setProperty(t.dataset.p, t.value); }); });
      t.value = '';
    } else if (t.dataset.g) {
      var v = parseFloat(t.value);
      if (!isNaN(v)) change(null, function () { moveTo(t.dataset.g, v); });
    }
    drawFrame();
  });
  tools.addEventListener('keydown', function (e) { if (e.key === 'Enter' && inField(e.target)) e.target.blur(); });

  function selectParent() {
    if (!sel.length) return;
    var p = parentShape(sel[0]);
    if (p) setSel([p]);
    else say('This is the outermost shape on the slide');
  }
  function selectChild() {
    if (!sel.length) return;
    var kids = childShapes(sel[0]);
    if (kids.length) setSel([kids[0]]);
  }

  // ----------------------------------------------------------- pointer work
  var drag = null;
  var guides = [];
  var hoverEl = null;

  function clearGuides() { guides.forEach(function (g) { g.remove(); }); guides = []; }
  function guide(slide, axis, at) {
    var sr = slide.getBoundingClientRect();
    var z = sr.width / W;
    var g = ui('div', { class: 'nbg-guide' });
    if (axis === 'x') { g.style.left = (sr.left + at * z) + 'px'; g.style.top = sr.top + 'px'; g.style.width = '1px'; g.style.height = sr.height + 'px'; }
    else { g.style.top = (sr.top + at * z) + 'px'; g.style.left = sr.left + 'px'; g.style.height = '1px'; g.style.width = sr.width + 'px'; }
    doc.body.appendChild(g);
    guides.push(g);
  }
  function snapLines(slide) {
    var gtr = pxVar('--gutter');
    var xs = [gtr, W - gtr, W / 2];
    var ys = [H / 2, pxVar('--title-y'), pxVar('--body-top'), pxVar('--body-bottom')];
    topShapes(slide).concat(Array.prototype.slice.call(slide.querySelectorAll('.free'))).forEach(function (n) {
      if (sel.some(function (s) { return s === n || s.contains(n) || n.contains(s); })) return;
      var b = boxOf(n);
      xs.push(b.x, b.x + b.w / 2, b.x + b.w);
      ys.push(b.y, b.y + b.h / 2, b.y + b.h);
    });
    return { xs: xs, ys: ys };
  }
  function snapAxis(edges, lines) {
    var best = null;
    edges.forEach(function (e) {
      lines.forEach(function (l) {
        var d = l - e;
        if (Math.abs(d) <= SNAP && (best === null || Math.abs(d) < Math.abs(best.d))) best = { d: d, at: l };
      });
    });
    return best;
  }

  main.addEventListener('pointerdown', function (e) {
    if (isPresent() || e.button !== 0) return;
    if (editing && editing.contains(e.target)) return;
    var slide = e.target.closest('.slide');
    if (!slide) return;
    var leaf = shapeFrom(e.target);
    var chain = leaf ? chainFor(leaf) : [];
    if (!chain.length) {
      if (!e.shiftKey) clearSel();
      drag = { kind: 'band', slide: slide, x0: e.clientX, y0: e.clientY, add: e.shiftKey, moved: false };
      e.preventDefault();
      return;
    }
    var level = -1;
    chain.forEach(function (n, i) { if (isSel(n)) level = i; });
    if (e.shiftKey) {
      var pick = level >= 0 ? chain[level] : chain[0];
      setSel(isSel(pick) ? sel.filter(function (n) { return n !== pick; }) : sel.concat([pick]));
      e.preventDefault();
      return;
    }
    if (level < 0) setSel([chain[0]]);
    drag = {
      kind: 'move', slide: slide, x0: e.clientX, y0: e.clientY, moved: false,
      deeper: level >= 0 && level + 1 < chain.length ? chain[level + 1] : null,
      z: zoomOf(slide), starts: sel.map(getT), u0: union(sel), lines: null
    };
    e.preventDefault();
  });

  frame.addEventListener('pointerdown', function (e) {
    var h = e.target.dataset && e.target.dataset.h;
    if (!h || !sel.length) return;
    e.preventDefault();
    e.stopPropagation();
    var slide = sel[0].closest('.slide');
    drag = {
      kind: 'resize', h: h, slide: slide, x0: e.clientX, y0: e.clientY, moved: false, z: zoomOf(slide),
      u0: union(sel), boxes: sel.map(boxOf), starts: sel.map(getT)
    };
  });

  doc.addEventListener('pointermove', function (e) {
    if (!drag) {
      if (isPresent() || editing) return;
      var leaf = main.contains(e.target) ? shapeFrom(e.target) : null;
      var chain = leaf ? chainFor(leaf) : [];
      var lv = -1;
      chain.forEach(function (n, i) { if (isSel(n)) lv = i; });
      var h = chain[lv + 1] || null;
      if (h !== hoverEl) {
        if (hoverEl) hoverEl.classList.remove('nbg-hover');
        hoverEl = h && !isSel(h) ? h : null;
        if (hoverEl) hoverEl.classList.add('nbg-hover');
      }
      return;
    }
    var dxs = e.clientX - drag.x0;
    var dys = e.clientY - drag.y0;
    if (!drag.moved && Math.abs(dxs) + Math.abs(dys) < 4) return;
    if (!drag.moved) {
      drag.moved = true;
      if (drag.kind !== 'band') checkpoint();
      if (hoverEl) { hoverEl.classList.remove('nbg-hover'); hoverEl = null; }
    }
    if (drag.kind === 'band') {
      band.style.display = 'block';
      band.style.left = Math.min(e.clientX, drag.x0) + 'px';
      band.style.top = Math.min(e.clientY, drag.y0) + 'px';
      band.style.width = Math.abs(dxs) + 'px';
      band.style.height = Math.abs(dys) + 'px';
      return;
    }
    var dx = dxs / drag.z;
    var dy = dys / drag.z;
    clearGuides();
    if (drag.kind === 'move') {
      if (!e.altKey) {
        if (!drag.lines) drag.lines = snapLines(drag.slide);
        var u = drag.u0;
        var sx = snapAxis([u.x + dx, u.x + dx + u.w / 2, u.x + dx + u.w], drag.lines.xs);
        var sy = snapAxis([u.y + dy, u.y + dy + u.h / 2, u.y + dy + u.h], drag.lines.ys);
        if (sx) { dx += sx.d; guide(drag.slide, 'x', sx.at); }
        if (sy) { dy += sy.d; guide(drag.slide, 'y', sy.at); }
      }
      sel.forEach(function (n, i) { setT(n, drag.starts[i][0] + dx, drag.starts[i][1] + dy); });
    } else {
      var u0 = drag.u0;
      var hd = drag.h;
      var w = u0.w + (hd.indexOf('e') >= 0 ? dx : hd.indexOf('w') >= 0 ? -dx : 0);
      var hh = u0.h + (hd.indexOf('s') >= 0 ? dy : hd.indexOf('n') >= 0 ? -dy : 0);
      var keep = e.shiftKey || (sel.length === 1 && sel[0].tagName === 'IMG' && hd.length === 2);
      if (keep) {
        var f = Math.max(w / u0.w, hh / u0.h);
        w = u0.w * f;
        hh = u0.h * f;
      }
      w = Math.max(8, w);
      hh = Math.max(8, hh);
      var sxf = w / u0.w;
      var syf = hh / u0.h;
      var ox = hd.indexOf('w') >= 0 ? u0.x + u0.w - w : u0.x;
      var oy = hd.indexOf('n') >= 0 ? u0.y + u0.h - hh : u0.y;
      sel.forEach(function (n, i) {
        var b = drag.boxes[i];
        var nw = hd === 'n' || hd === 's' ? (sel.length > 1 ? b.w : null) : b.w * sxf;
        var nh = hd === 'e' || hd === 'w' ? (sel.length > 1 ? b.h : null) : b.h * syf;
        setSize(n, nw, nh);
        var nx = ox + (b.x - u0.x) * sxf;
        var ny = oy + (b.y - u0.y) * syf;
        setT(n, drag.starts[i][0] + nx - b.x, drag.starts[i][1] + ny - b.y);
      });
    }
    drawFrame();
  });

  doc.addEventListener('pointerup', function (e) {
    if (!drag) return;
    var d = drag;
    drag = null;
    clearGuides();
    if (d.kind === 'band') {
      band.style.display = 'none';
      if (!d.moved) return;
      var l = Math.min(e.clientX, d.x0), r = Math.max(e.clientX, d.x0), t = Math.min(e.clientY, d.y0), b = Math.max(e.clientY, d.y0);
      var inside = function (n) {
        var q = n.getBoundingClientRect();
        return q.left >= l && q.right <= r && q.top >= t && q.bottom <= b;
      };
      var open = function (n) { return isBare(n) ? childShapes(n).filter(inside) : [n]; };
      var picked = [];
      topShapes(d.slide).concat(Array.prototype.slice.call(d.slide.querySelectorAll('.free'))).filter(inside)
        .forEach(function (n) { picked = picked.concat(open(n)); });
      setSel((d.add ? sel : []).concat(picked));
      return;
    }
    if (d.moved) { markDirty(); return; }
    // A click without a drag on an already selected shape selects what is inside it.
    if (d.kind === 'move' && d.deeper) setSel([d.deeper]);
  });

  main.addEventListener('dragstart', function (e) { e.preventDefault(); });

  main.addEventListener('dblclick', function (e) {
    if (isPresent()) return;
    var t = textBlock(e.target);
    if (t) { if (t !== editing) startEdit(t); return; }
    var img = e.target.closest('img');
    if (img && main.contains(img)) { replaceImage(img); return; }
    if (e.target.closest('svg')) say('Chart and diagram labels are part of the drawing: ask Claude to change them');
  });
  main.addEventListener('paste', function (e) {
    if (!editing) return;
    e.preventDefault();
    var text = (e.clipboardData || window.clipboardData).getData('text/plain');
    doc.execCommand('insertText', false, text.replace(/\r?\n/g, ' '));
  });
  main.addEventListener('drop', function (e) { if (editing) e.preventDefault(); });
  doc.addEventListener('mousedown', function (e) {
    if (editing && !editing.contains(e.target) && !fmt.contains(e.target)) commit();
    if (!menu.contains(e.target)) hideMenu();
  }, true);

  // ---------------------------------------------------------------- inserts
  function slideAt(x, y) {
    var hit = doc.elementFromPoint(x, y);
    var s = hit && hit.closest && hit.closest('.slide');
    return s || slides()[centreSlide()];
  }
  function pointIn(slide, x, y) {
    var sr = slide.getBoundingClientRect();
    var z = sr.width / W;
    return [Math.max(0, (x - sr.left) / z), Math.max(0, (y - sr.top) / z)];
  }
  function insertFree(slide, at, node) {
    node.classList.add('free');
    node.style.position = 'absolute';
    node.style.left = Math.round(Math.min(at[0], W - 200)) + 'px';
    node.style.top = Math.round(Math.min(at[1], H - 120)) + 'px';
    slide.appendChild(node);
    setSel([node]);
  }
  function addText(slide, at) {
    change('Text box added: double-click to type', function () {
      var n = doc.createElement('p');
      n.textContent = 'New text';
      n.style.width = '640px';
      insertFree(slide, at, n);
    });
  }
  function addBox(slide, at) {
    change('Box added', function () {
      var n = doc.createElement('div');
      n.className = 'card';
      n.style.width = '480px';
      n.style.height = '240px';
      n.innerHTML = '<h2>Title</h2><p>Text</p>';
      insertFree(slide, at, n);
    });
  }
  function pickImage(done) {
    var input = doc.createElement('input');
    input.type = 'file';
    input.accept = 'image/png,image/jpeg,image/svg+xml,image/webp,image/gif';
    input.onchange = function () {
      var f = input.files && input.files[0];
      if (!f) return;
      var rd = new FileReader();
      rd.onload = function () { done(rd.result); };
      rd.readAsDataURL(f);
    };
    input.click();
  }
  function addPicture(slide, at) {
    pickImage(function (uri) {
      change('Picture added', function () {
        var n = doc.createElement('img');
        n.src = uri;
        n.alt = '';
        n.style.width = '640px';
        insertFree(slide, at, n);
      });
    });
  }
  function replaceImage(img) {
    pickImage(function (uri) { change('Picture replaced', function () { img.removeAttribute('srcset'); img.src = uri; }); });
  }
  function addSlide(after) {
    change('Slide added', function () {
      var s = doc.createElement('section');
      s.className = 'slide';
      s.innerHTML = '<h1>Slide title: the message in one sentence</h1><div class="body"><ul><li>First point</li></ul></div>';
      after.after(s);
      s.scrollIntoView({ block: 'center' });
    });
  }

  // clipboard: shapes copied inside this deck
  var clip = null;
  function copySel() {
    if (!sel.length) return;
    clip = { html: sel.map(function (n) { return cleanNode(n.cloneNode(true)).outerHTML; }), parent: sel[0].parentElement };
    say(sel.length + ' copied', 1200);
  }
  function pasteClip(slide) {
    if (!clip) { say('Nothing copied'); return; }
    change('Pasted', function () {
      var tpl = doc.createElement('template');
      tpl.innerHTML = clip.html.join('');
      var nodes = Array.prototype.slice.call(tpl.content.children);
      var anchor = sel.length ? sel[sel.length - 1] : null;
      var host = anchor ? null : clip.parent && slide.contains(clip.parent) ? clip.parent : slide.querySelector(':scope > .body') || slide;
      nodes.forEach(function (n) {
        if (anchor) { anchor.after(n); anchor = n; }
        else host.appendChild(n);
        if (n.classList.contains('free')) { var t = getT(n); setT(n, t[0] + 24, t[1] + 24); }
      });
      setSel(nodes);
    });
  }

  // ----------------------------------------------------------- context menu
  function hideMenu() { menu.style.display = 'none'; }
  function showMenu(x, y, items) {
    menu.innerHTML = '';
    items.forEach(function (it) {
      if (it === '-') { menu.appendChild(doc.createElement('hr')); return; }
      var b = doc.createElement('button');
      b.textContent = it[0];
      b.setAttribute('role', 'menuitem');
      b.onclick = function () { hideMenu(); it[1](); };
      menu.appendChild(b);
    });
    menu.style.display = 'flex';
    menu.style.left = Math.max(8, Math.min(x, innerWidth - menu.offsetWidth - 8)) + 'px';
    menu.style.top = Math.max(8, Math.min(y, innerHeight - menu.offsetHeight - 8)) + 'px';
    var first = menu.querySelector('button');
    if (first) first.focus();
  }
  function itemOf(node) {
    var it = node.closest(ITEM_SEL);
    return it && main.contains(it) && !it.closest('svg') ? it : null;
  }
  function moveSibling(node, dir) {
    var sib = dir < 0 ? node.previousElementSibling : node.nextElementSibling;
    if (!sib) { say(dir < 0 ? 'Already first' : 'Already last'); return; }
    if (dir < 0) sib.before(node);
    else sib.after(node);
  }

  main.addEventListener('contextmenu', function (e) {
    if (e.target.closest('a, input, textarea') || isPresent()) return;
    var slide = e.target.closest('.slide');
    if (!slide || editing) return;
    e.preventDefault();
    var at = pointIn(slide, e.clientX, e.clientY);
    var leaf = shapeFrom(e.target);
    var chain = leaf ? chainFor(leaf) : [];
    if (chain.length && !chain.some(isSel)) setSel([chain[0]]);
    var items = [];
    var t = textBlock(e.target);
    var img = e.target.closest('img');
    var item = itemOf(e.target);
    if (t) items.push(['Edit text', function () { startEdit(t); }]);
    if (img && main.contains(img)) items.push(['Replace picture…', function () { replaceImage(img); }]);
    if (sel.length) {
      items.push(['Bring to front', function () { change(null, function () { zOrder(true); }); }],
        ['Send to back', function () { change(null, function () { zOrder(false); }); }],
        ['Select the enclosing shape', selectParent],
        ['Copy', copySel],
        ['Reset position, size and style', function () { change('Reset', function () { eachSel(resetShape); }); }]);
    }
    if (clip) items.push(['Paste', function () { pasteClip(slide); }]);
    if (item) {
      var name = item.tagName === 'LI' ? 'bullet' : item.tagName === 'TR' ? 'row' : 'item';
      items.push('-',
        ['Duplicate ' + name, function () { change('Duplicated', function () { item.after(cleanNode(item.cloneNode(true))); }); }],
        ['Move ' + name + ' earlier', function () { change(null, function () { moveSibling(item, -1); }); }],
        ['Move ' + name + ' later', function () { change(null, function () { moveSibling(item, 1); }); }],
        ['Delete ' + name, function () { change('Deleted', function () { clearSel(); item.remove(); }); }]);
    }
    items.push('-',
      ['Add a text box here', function () { addText(slide, at); }],
      ['Add a box here', function () { addBox(slide, at); }],
      ['Add a picture here…', function () { addPicture(slide, at); }],
      '-',
      ['New slide after this one', function () { addSlide(slide); }],
      ['Duplicate slide', function () { change('Slide duplicated', function () { clearSel(); slide.after(cleanNode(slide.cloneNode(true))); }); }],
      ['Move slide up', function () { change(null, function () { moveSibling(slide, -1); }); }],
      ['Move slide down', function () { change(null, function () { moveSibling(slide, 1); }); }],
      ['Delete slide', function () {
        if (slides().length < 2) { say('A deck keeps at least one slide'); return; }
        change('Slide deleted', function () { clearSel(); slide.remove(); });
      }],
      '-',
      ['Undo', doUndo],
      ['Present from this slide', function () { present(slide); }],
      ['Export to PDF', exportPdf],
      ['Save as HTML', save]);
    showMenu(e.clientX, e.clientY, items);
  });

  menu.addEventListener('keydown', function (e) {
    var bs = Array.prototype.slice.call(menu.querySelectorAll('button'));
    var i = bs.indexOf(doc.activeElement);
    if (e.key === 'ArrowDown') { e.preventDefault(); bs[(i + 1) % bs.length].focus(); }
    if (e.key === 'ArrowUp') { e.preventDefault(); bs[(i - 1 + bs.length) % bs.length].focus(); }
    if (e.key === 'Escape') hideMenu();
  });

  // ------------------------------------------------------------- save, PDF
  function deckHtml() {
    var copy = root.cloneNode(true);
    cleanNode(copy);
    copy.querySelector('main.deck').innerHTML = cleanMain();
    return '<!doctype html>\n' + copy.outerHTML;
  }
  function fileName() {
    var n = decodeURIComponent(location.pathname.split('/').pop() || 'deck.html');
    return /\.html?$/i.test(n) ? n : n + '.html';
  }
  function save() {
    if (editing) commit();
    var blob = new Blob([deckHtml()], { type: 'text/html' });
    if (window.showSaveFilePicker) {
      window.showSaveFilePicker({ suggestedName: fileName(), types: [{ description: 'HTML deck', accept: { 'text/html': ['.html'] } }] })
        .then(function (h) { return h.createWritable().then(function (w) { return w.write(blob).then(function () { return w.close(); }); }); })
        .then(saved)
        .catch(function (err) { if (err && err.name !== 'AbortError') download(blob); });
      return;
    }
    download(blob);
  }
  function download(blob) {
    var a = doc.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = fileName();
    doc.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(function () { URL.revokeObjectURL(a.href); }, 4000);
    saved();
  }
  function saved() {
    original = cleanMain();
    store(null);
    bar.classList.remove('nbg-dirty');
    say('Saved. The file opens and edits exactly like this one.');
  }
  function exportPdf() {
    if (editing) commit();
    clearSel();
    if (isPresent()) endPresent();
    say('Choose "Save as PDF" in the print dialog. Keep the scale at 100%.', 6000);
    setTimeout(function () { window.print(); }, 60);
  }
  addEventListener('beforeprint', function () { if (editing) commit(); hideMenu(); clearSel(); });

  // ------------------------------------------------------------- presenting
  var current = 0;
  function centreSlide() {
    var mid = innerHeight / 2;
    var best = 0;
    var dist = Infinity;
    slides().forEach(function (s, i) {
      var r = s.getBoundingClientRect();
      var d = Math.abs((r.top + r.bottom) / 2 - mid);
      if (d < dist) { dist = d; best = i; }
    });
    return best;
  }
  function show(i) {
    var all = slides();
    current = Math.max(0, Math.min(all.length - 1, i));
    all.forEach(function (s, k) { s.classList.toggle('nbg-current', k === current); });
  }
  function present(slide) {
    if (editing) commit();
    hideMenu();
    clearSel();
    var i = slide ? slides().indexOf(slide) : centreSlide();
    root.classList.add('nbg-present');
    show(i);
    fit();
    if (root.requestFullscreen) root.requestFullscreen().catch(function () {});
  }
  function endPresent() {
    var s = slides()[current];
    root.classList.remove('nbg-present');
    slides().forEach(function (x) { x.classList.remove('nbg-current'); });
    fit();
    if (doc.fullscreenElement && doc.exitFullscreen) doc.exitFullscreen().catch(function () {});
    if (s) s.scrollIntoView({ block: 'center' });
  }
  doc.addEventListener('fullscreenchange', function () {
    if (!doc.fullscreenElement && isPresent()) endPresent();
  });
  doc.addEventListener('click', function (e) {
    if (isPresent() && !e.target.closest('a')) show(current + 1);
  });

  // ---------------------------------------------------------------- keys
  doc.addEventListener('keydown', function (e) {
    var mod = e.metaKey || e.ctrlKey;
    var k = e.key;
    if (editing) {
      if (k === 'Escape') { e.preventDefault(); cancel(); }
      else if (k === 'Enter' && !e.shiftKey) { e.preventDefault(); commit(); }
      else if (k === 'Enter' && e.shiftKey) { e.preventDefault(); doc.execCommand('insertLineBreak'); }
      return;
    }
    if (isPresent()) {
      if (['ArrowRight', 'ArrowDown', 'PageDown', ' ', 'Enter'].indexOf(k) >= 0) { e.preventDefault(); show(current + 1); }
      else if (['ArrowLeft', 'ArrowUp', 'PageUp', 'Backspace'].indexOf(k) >= 0) { e.preventDefault(); show(current - 1); }
      else if (k === 'Home') show(0);
      else if (k === 'End') show(slides().length - 1);
      else if (k === 'Escape') endPresent();
      return;
    }
    if (inField(e.target)) return;
    var low = k.toLowerCase();
    if (mod && low === 'z' && !e.shiftKey) { e.preventDefault(); doUndo(); return; }
    if (mod && (low === 'y' || (low === 'z' && e.shiftKey))) { e.preventDefault(); doRedo(); return; }
    if (mod && low === 's') { e.preventDefault(); save(); return; }
    if (mod && low === 'p') { e.preventDefault(); exportPdf(); return; }
    if (mod && low === 'v') { e.preventDefault(); pasteClip(sel.length ? sel[0].closest('.slide') : slides()[centreSlide()]); return; }
    if (mod && low === 'a') {
      e.preventDefault();
      var s = sel.length ? sel[0].closest('.slide') : slides()[centreSlide()];
      setSel(topShapes(s));
      return;
    }
    if (sel.length) {
      var step = e.shiftKey ? 10 : 1;
      var arrows = { ArrowLeft: [-step, 0], ArrowRight: [step, 0], ArrowUp: [0, -step], ArrowDown: [0, step] };
      if (arrows[k]) {
        e.preventDefault();
        change(null, function () {
          if (e.altKey) {
            var u = union(sel);
            scaleSel((u.w + arrows[k][0]) / u.w, (u.h + arrows[k][1]) / u.h, u);
          } else moveBy(arrows[k][0], arrows[k][1]);
        });
        return;
      }
      if (k === 'Delete' || k === 'Backspace') { e.preventDefault(); change('Deleted', removeSel); return; }
      if (mod && low === 'd') { e.preventDefault(); change('Duplicated', duplicate); return; }
      if (mod && low === 'c') { e.preventDefault(); copySel(); return; }
      if (mod && (k === ']' || k === '}')) { e.preventDefault(); change(null, function () { zOrder(true); }); return; }
      if (mod && (k === '[' || k === '{')) { e.preventDefault(); change(null, function () { zOrder(false); }); return; }
      if (k === 'Tab') { e.preventDefault(); if (e.shiftKey) selectChild(); else selectParent(); return; }
      if (k === 'Enter') {
        var tb = textBlock(sel[0]);
        if (tb) { e.preventDefault(); startEdit(tb); }
        return;
      }
      if (k === 'Escape') { clearSel(); return; }
    }
    if (!mod && low === 'p') present();
    else if (k === 'Escape') hideMenu();
  });

  bar.addEventListener('click', function (e) {
    var b = e.target.closest('button');
    if (!b) return;
    var a = b.dataset.a;
    if (a === 'present') present();
    else if (a === 'save') save();
    else if (a === 'pdf') exportPdf();
    else if (a === 'undo') doUndo();
    else if (a === 'redo') doRedo();
    else if (a === 'more') {
      var r = b.getBoundingClientRect();
      showMenu(r.left - 200, r.bottom + 6, [
        ['New slide at the end', function () { addSlide(slides()[slides().length - 1]); }],
        ['Discard all edits', function () {
          if (!confirm('Discard every edit made since this file was saved?')) return;
          checkpoint();
          setMain(original);
          say('Edits discarded');
        }],
        '-',
        ['How editing works', function () {
          say('Click selects, drag moves (Alt: no snapping), handles resize. Double-click edits text. Right-click adds text, boxes, pictures and slides. Save writes the HTML; PDF prints one page per slide.', 10000);
        }]
      ]);
    }
  });

  fit();
  syncTools();

  window.nbgDeck = {
    version: VERSION,
    edit: { start: startEdit, commit: commit, cancel: cancel, textBlock: textBlock },
    shape: {
      select: function (list) { setSel([].concat(list)); }, selection: function () { return sel.slice(); },
      moveBy: function (dx, dy) { change(null, function () { moveBy(dx, dy); }); },
      set: function (k, v) { change(null, function () { moveTo(k, v); }); },
      align: function (kind) { change(null, function () { align(kind); }); },
      order: function (front) { change(null, function () { zOrder(front); }); },
      reset: function () { change(null, function () { eachSel(resetShape); }); },
      remove: function () { change(null, removeSel); },
      duplicate: function () { change(null, duplicate); },
      box: boxOf
    },
    undo: doUndo,
    redo: doRedo,
    html: deckHtml,
    save: save,
    exportPdf: exportPdf,
    present: present
  };

  // ------------------------------------------------------- layout report
  function runCheck() {
    var ready = doc.fonts && doc.fonts.ready ? doc.fonts.ready : Promise.resolve();
    ready.then(function () {
      var imgs = Array.prototype.slice.call(doc.images);
      return Promise.all(imgs.map(function (im) {
        return im.complete ? null : new Promise(function (r) { im.onload = im.onerror = r; });
      }));
    }).then(function () {
      var out = { version: VERSION, slides: [], aptos: !!(doc.fonts && doc.fonts.check('16px Aptos')) };
      var keynote = main.classList.contains('keynote');
      out.keynote = keynote;
      var gutter = pxVar(keynote ? '--k-gutter' : '--gutter');
      var footer = pxVar(keynote ? '--k-footer-top' : '--footer-top');
      var minFont = pxVar(keynote ? '--k-fs-min' : '--fs-min');
      var pillFont = pxVar('--fs-pill');
      // WCAG AA, measured against the nearest solid fill behind the text. Text over a
      // photograph or an unknown gradient is left to the visual QA.
      var rgb = function (s) { var m = s.match(/[\d.]+/g); return m ? m.map(Number) : null; };
      var lum = function (c) {
        var f = function (v) { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); };
        return 0.2126 * f(c[0]) + 0.7152 * f(c[1]) + 0.0722 * f(c[2]);
      };
      var groundTo = rgb(getComputedStyle(root).getPropertyValue('--k-ground-to').trim().replace('#', '').match(/../g).map(function (h) { return parseInt(h, 16); }).join(','));
      var behind = function (n) {
        for (var p = n; p && p !== main; p = p.parentElement) {
          if (p.closest('.bg') || (keynote && p.parentElement && p.parentElement.querySelector(':scope > .bg') && p.parentElement.classList.contains('slide'))) return null;
          var cs = getComputedStyle(p);
          var c = rgb(cs.backgroundColor);
          if (c && (c.length < 4 || c[3] >= 0.95)) return c;
          if (p.classList.contains('slide')) return keynote ? groundTo : [255, 255, 255];
          if (cs.backgroundImage !== 'none') return null;
        }
        return null;
      };
      main.querySelectorAll(':scope > .slide').forEach(function (s, i) {
        var issues = [];
        var sr = s.getBoundingClientRect();
        if (s.offsetWidth !== W || s.offsetHeight !== H) issues.push({ level: 'error', what: 'slide box is ' + s.offsetWidth + 'x' + s.offsetHeight + ', not 1920x1080' });
        var label = function (n) {
          var t = (n.textContent || n.getAttribute('alt') || n.tagName).replace(/\s+/g, ' ').trim();
          var cls = typeof n.className === 'string' && n.className ? '.' + n.className.split(' ')[0] : '';
          return n.tagName.toLowerCase() + cls + ' "' + t.slice(0, 50) + '"';
        };
        // One report per problem per branch: a flagged element hides the same
        // problem in its descendants, never a different one.
        var seen = {};
        var flag = function (n, level, what) {
          var kind = what.replace(/[\d.]+/g, '#');
          var list = seen[kind] || (seen[kind] = []);
          for (var k = 0; k < list.length; k++) if (list[k].contains(n)) return;
          list.push(n);
          if (issues.length < 12) issues.push({ level: level, what: what + ': ' + label(n) });
        };
        s.querySelectorAll('*').forEach(function (n) {
          if (n.closest('.notes') || (n.closest('svg') && n.tagName.toLowerCase() !== 'svg')) return;
          var r = n.getBoundingClientRect();
          if (!r.width || !r.height) return;
          var x0 = r.left - sr.left, y0 = r.top - sr.top, x1 = r.right - sr.left, y1 = r.bottom - sr.top;
          // .ksource is the keynote footer row's own text, below the content line by design.
          var bleed = n.closest('.bleed, .bg, .ksource');
          if (x0 < -1 || y0 < -1 || x1 > W + 1 || y1 > H + 1) flag(n, 'error', 'runs off the slide');
          else if (!bleed && (x0 < gutter - 1 || x1 > W - gutter + 1)) flag(n, 'error', 'crosses the side gutter');
          else if (!bleed && y1 > footer + 1) flag(n, 'error', 'enters the footer zone');
          if (n.scrollHeight > n.clientHeight + 2 && /hidden|clip|auto|scroll/.test(getComputedStyle(n).overflowY)) flag(n, 'error', 'text is clipped');
        });
        var body = s.querySelector(':scope > .body');
        if (body) {
          var br = body.getBoundingClientRect();
          Array.prototype.forEach.call(body.querySelectorAll('*'), function (n) {
            var r = n.getBoundingClientRect();
            if (r.height && r.bottom > br.bottom + 1 && !n.closest('svg')) flag(n, 'error', 'runs past the bottom of the body area');
          });
          // Standard #2.7: content fills 60-85% of the body. Measured as the
          // children's own heights, so a strip pushed to the bottom does not count as fill.
          var used = 0;
          Array.prototype.forEach.call(body.children, function (c) {
            if (!c.classList.contains('grow')) used += c.getBoundingClientRect().height;
          });
          var grows = body.querySelector(':scope > .grow');
          var fill = br.height ? used / br.height : 1;
          if (!grows && body.children.length && fill < 0.5) {
            issues.push({ level: 'warning', what: 'the body is ' + Math.round(fill * 100) + '% full (aim for 60-85%): larger text, a larger exhibit or fewer slides' });
          }
        }
        var walker = doc.createTreeWalker(s, NodeFilter.SHOW_TEXT);
        var tn;
        while ((tn = walker.nextNode())) {
          if (!tn.nodeValue.trim()) continue;
          var p = tn.parentElement;
          if (!p || p.closest('.notes')) continue;
          var pcs = getComputedStyle(p);
          var size = parseFloat(pcs.fontSize);
          var floor = p.closest('.pill') ? pillFont : minFont;
          if (size < floor - 0.1) flag(p, 'error', 'text is ' + (size / 2) + 'pt, under the ' + (floor / 2) + 'pt floor');
          var fg = rgb(pcs.color);
          var bg = behind(p);
          if (fg && bg) {
            var l1 = lum(fg), l2 = lum(bg);
            var ratio = (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05);
            var large = size >= 36 || (size >= 28 && parseInt(pcs.fontWeight, 10) >= 700);
            var need = large ? 3 : 4.5;
            if (ratio < need - 0.01) flag(p, 'error', 'contrast ' + ratio.toFixed(2) + ':1, under ' + need + ':1');
          }
        }
        // Free placement makes overlaps possible: text over other text is never intended.
        var texts = [];
        s.querySelectorAll('*').forEach(function (n) {
          if (n.closest('.notes, svg')) return;
          var own = Array.prototype.some.call(n.childNodes, function (c) { return c.nodeType === 3 && c.nodeValue.trim(); });
          if (own) texts.push({ n: n, r: n.getBoundingClientRect() });
        });
        for (var a = 0; a < texts.length; a++) {
          for (var c = a + 1; c < texts.length; c++) {
            var A = texts[a], B = texts[c];
            if (A.n.contains(B.n) || B.n.contains(A.n)) continue;
            // Two inline runs of one paragraph share lines, not space.
            var blkA = A.n, blkB = B.n;
            while (blkA.parentElement && /^inline/.test(getComputedStyle(blkA).display)) blkA = blkA.parentElement;
            while (blkB.parentElement && /^inline/.test(getComputedStyle(blkB).display)) blkB = blkB.parentElement;
            if (blkA === blkB || blkA.contains(B.n) || blkB.contains(A.n)) continue;
            var ow = Math.min(A.r.right, B.r.right) - Math.max(A.r.left, B.r.left);
            var oh = Math.min(A.r.bottom, B.r.bottom) - Math.max(A.r.top, B.r.top);
            if (ow > 4 && oh > 4) flag(B.n, 'warning', 'text overlaps ' + label(A.n));
          }
        }
        s.querySelectorAll('img').forEach(function (im) {
          if (!im.naturalWidth) issues.push({ level: 'error', what: 'picture did not load: ' + (im.getAttribute('alt') || im.src.slice(0, 60)) });
        });
        out.slides.push({ index: i + 1, issues: issues });
      });
      var pre = doc.createElement('script');
      pre.type = 'application/json';
      pre.id = 'nbg-check-result';
      pre.textContent = JSON.stringify(out);
      doc.body.appendChild(pre);
    });
  }
})();
