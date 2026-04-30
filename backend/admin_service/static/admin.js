'use strict';

/**
 * Custom Select Dropdown — стилизованный дропдаун с видимым скроллбаром.
 * Применяется ко всем <select class="select-enhanced"> на странице.
 *
 * Принцип работы:
 *  1. Обёртка (.csel) вставляется вокруг нативного <select>.
 *  2. Нативный <select> скрывается визуально, но участвует в submit формы.
 *  3. Клик по кнопке-тригеру открывает кастомный список с видимым скроллбаром.
 *  4. Выбор опции синхронизируется обратно в нативный <select>.
 */
(function () {

  /* ------------------------------------------------------------------ */
  /* Инициализация всех select-элементов на странице                     */
  /* ------------------------------------------------------------------ */
  function initAll() {
    document.querySelectorAll('select.select-enhanced').forEach(initOne);
  }

  /* ------------------------------------------------------------------ */
  /* Инициализация одного <select>                                        */
  /* ------------------------------------------------------------------ */
  function initOne(native) {
    if (native.dataset.csEnhanced) return;
    native.dataset.csEnhanced = '1';

    /* --- Обёртка --- */
    const wrapper = document.createElement('div');
    wrapper.className = 'csel';
    native.parentNode.insertBefore(wrapper, native);
    wrapper.appendChild(native);

    /* --- Кнопка-тригер --- */
    const trigger = document.createElement('button');
    trigger.type = 'button';
    trigger.className = 'csel__trigger';
    trigger.setAttribute('aria-haspopup', 'listbox');
    trigger.setAttribute('aria-expanded', 'false');
    wrapper.insertBefore(trigger, native);

    const display = document.createElement('span');
    display.className = 'csel__display';
    trigger.appendChild(display);

    const caret = document.createElement('span');
    caret.className = 'csel__caret';
    caret.innerHTML = `<svg width="12" height="12" viewBox="0 0 12 12" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M2 4L6 8L10 4" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>`;
    trigger.appendChild(caret);

    /* --- Выпадающая панель --- */
    const panel = document.createElement('div');
    panel.className = 'csel__panel';
    panel.setAttribute('role', 'listbox');
    panel.hidden = true;
    wrapper.appendChild(panel);

    /* Строка поиска (показываем только если опций > 6) */
    let searchInput = null;
    if (native.options.length > 6) {
      const searchWrap = document.createElement('div');
      searchWrap.className = 'csel__search-wrap';
      searchInput = document.createElement('input');
      searchInput.type = 'text';
      searchInput.className = 'csel__search';
      searchInput.placeholder = 'Поиск…';
      searchInput.setAttribute('autocomplete', 'off');
      searchWrap.appendChild(searchInput);
      panel.appendChild(searchWrap);
    }

    /* Скролл-контейнер со списком */
    const scroller = document.createElement('div');
    scroller.className = 'csel__scroller';
    panel.appendChild(scroller);

    /* ---------------------------------------------------------------- */
    /* Рендер опций (с учётом фильтра поиска)                           */
    /* ---------------------------------------------------------------- */
    function buildOptions(filter) {
      scroller.innerHTML = '';
      const query = (filter || '').toLowerCase();
      let hasVisible = false;

      Array.from(native.options).forEach((opt, i) => {
        if (query && !opt.text.toLowerCase().includes(query)) return;
        hasVisible = true;

        const item = document.createElement('div');
        item.className = 'csel__option';
        item.setAttribute('role', 'option');
        if (i === native.selectedIndex) {
          item.classList.add('is-selected');
          item.setAttribute('aria-selected', 'true');
        }
        item.dataset.index = i;

        /* Подсветка совпадения в строке поиска */
        if (query) {
          const idx = opt.text.toLowerCase().indexOf(query);
          item.innerHTML =
            escHtml(opt.text.slice(0, idx)) +
            '<mark>' + escHtml(opt.text.slice(idx, idx + query.length)) + '</mark>' +
            escHtml(opt.text.slice(idx + query.length));
        } else {
          item.textContent = opt.text;
        }

        item.addEventListener('mousedown', function (e) {
          e.preventDefault();
          selectOption(i);
          close();
        });

        scroller.appendChild(item);
      });

      if (!hasVisible) {
        const empty = document.createElement('div');
        empty.className = 'csel__empty';
        empty.textContent = 'Ничего не найдено';
        scroller.appendChild(empty);
      }
    }

    /* ---------------------------------------------------------------- */
    /* Обновить отображаемое значение на кнопке                         */
    /* ---------------------------------------------------------------- */
    function updateDisplay() {
      const opt = native.options[native.selectedIndex];
      display.textContent = opt ? opt.text : '';
    }

    /* ---------------------------------------------------------------- */
    /* Выбрать опцию по индексу                                         */
    /* ---------------------------------------------------------------- */
    function selectOption(index) {
      native.selectedIndex = index;
      native.dispatchEvent(new Event('change', { bubbles: true }));
      updateDisplay();
      /* Обновить подсветку в DOM без полного перестроения */
      scroller.querySelectorAll('.csel__option').forEach(el => {
        const active = parseInt(el.dataset.index, 10) === index;
        el.classList.toggle('is-selected', active);
        el.setAttribute('aria-selected', active ? 'true' : 'false');
      });
    }

    /* ---------------------------------------------------------------- */
    /* Открыть панель                                                   */
    /* ---------------------------------------------------------------- */
    function open() {
      buildOptions('');
      panel.hidden = false;
      trigger.classList.add('is-open');
      trigger.setAttribute('aria-expanded', 'true');

      /* Прокрутить к выбранному элементу */
      requestAnimationFrame(() => {
        const selItem = scroller.querySelector('.is-selected');
        if (selItem) selItem.scrollIntoView({ block: 'nearest' });
        if (searchInput) {
          searchInput.value = '';
          searchInput.focus();
        }
      });
    }

    /* ---------------------------------------------------------------- */
    /* Закрыть панель                                                   */
    /* ---------------------------------------------------------------- */
    function close() {
      panel.hidden = true;
      trigger.classList.remove('is-open');
      trigger.setAttribute('aria-expanded', 'false');
    }

    /* ---------------------------------------------------------------- */
    /* Обработчики событий                                              */
    /* ---------------------------------------------------------------- */
    trigger.addEventListener('click', function () {
      if (!panel.hidden) {
        close();
        return;
      }
      /* Закрыть все другие открытые дропдауны */
      document.querySelectorAll('.csel__panel:not([hidden])').forEach(p => {
        p.hidden = true;
        p.closest('.csel').querySelector('.csel__trigger').classList.remove('is-open');
      });
      open();
    });

    /* Поиск внутри дропдауна */
    if (searchInput) {
      searchInput.addEventListener('input', function () {
        buildOptions(this.value);
      });
    }

    /* Клавиатурная навигация */
    trigger.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        panel.hidden ? open() : close();
      }
      if (e.key === 'Escape') close();
      if (e.key === 'ArrowDown' && panel.hidden) {
        e.preventDefault();
        open();
      }
    });

    panel.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') {
        close();
        trigger.focus();
      }
    });

    /* Закрыть при клике вне */
    document.addEventListener('click', function (e) {
      if (!wrapper.contains(e.target)) close();
    });

    /* Скрыть нативный select (но оставить в потоке формы) */
    native.style.cssText = 'position:absolute;opacity:0;pointer-events:none;width:1px;height:1px;overflow:hidden;';

    updateDisplay();
  }

  /* ------------------------------------------------------------------ */
  /* Утилита: экранирование HTML                                         */
  /* ------------------------------------------------------------------ */
  function escHtml(str) {
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  /* ------------------------------------------------------------------ */
  /* Запуск после загрузки DOM                                           */
  /* ------------------------------------------------------------------ */
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initAll);
  } else {
    initAll();
  }

})();


(function () {

  const DEFAULT_PER_PAGE = 20;
  const SEARCH_DEBOUNCE_MS = 220;

  function initAll() {
    document.querySelectorAll('[data-csel-remote]').forEach(initOne);
  }

  function initOne(root) {
    if (root.dataset.cselRemoteInit) return;
    root.dataset.cselRemoteInit = '1';

    const endpoint = root.getAttribute('data-endpoint');
    const inputName = root.getAttribute('data-name') || 'source_id';
    const placeholder = root.getAttribute('data-placeholder') || '— выберите —';
    const allowEmpty = root.getAttribute('data-allow-empty') === '1';
    const emptyLabel = root.getAttribute('data-empty-label') || '— все —';
    const initialId = root.getAttribute('data-selected-id');
    const initialLabel = root.getAttribute('data-selected-label');
    const submitOnChange = root.getAttribute('data-submit-on-change') === '1';

    const hidden = document.createElement('input');
    hidden.type = 'hidden';
    hidden.name = inputName;
    hidden.value = initialId || '';
    root.appendChild(hidden);

    const trigger = document.createElement('button');
    trigger.type = 'button';
    trigger.className = 'csel__trigger';
    trigger.setAttribute('aria-haspopup', 'listbox');
    trigger.setAttribute('aria-expanded', 'false');

    const display = document.createElement('span');
    display.className = 'csel__display';
    trigger.appendChild(display);

    const caret = document.createElement('span');
    caret.className = 'csel__caret';
    caret.innerHTML = `<svg width="12" height="12" viewBox="0 0 12 12" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M2 4L6 8L10 4" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>`;
    trigger.appendChild(caret);

    root.appendChild(trigger);

    const panel = document.createElement('div');
    panel.className = 'csel__panel';
    panel.hidden = true;
    root.appendChild(panel);

    const searchWrap = document.createElement('div');
    searchWrap.className = 'csel__search-wrap';
    const searchInput = document.createElement('input');
    searchInput.type = 'text';
    searchInput.className = 'csel__search';
    searchInput.placeholder = 'Поиск…';
    searchInput.setAttribute('autocomplete', 'off');
    searchWrap.appendChild(searchInput);
    panel.appendChild(searchWrap);

    const scroller = document.createElement('div');
    scroller.className = 'csel__scroller';
    panel.appendChild(scroller);

    const footer = document.createElement('div');
    footer.className = 'csel__footer';
    panel.appendChild(footer);

    const prevBtn = document.createElement('button');
    prevBtn.type = 'button';
    prevBtn.className = 'csel__pager';
    prevBtn.textContent = '←';

    const nextBtn = document.createElement('button');
    nextBtn.type = 'button';
    nextBtn.className = 'csel__pager';
    nextBtn.textContent = '→';

    const pageInfo = document.createElement('span');
    pageInfo.className = 'csel__pageinfo';

    footer.appendChild(prevBtn);
    footer.appendChild(pageInfo);
    footer.appendChild(nextBtn);

    let currentPage = 1;
    let totalPages = 1;
    let lastQuery = '';
    let debounceTimer = null;
    let inflight = 0;

    function setSelected(id, label, options) {
      const previous = hidden.value;
      hidden.value = id || '';
      if (!id) {
        display.textContent = allowEmpty ? emptyLabel : placeholder;
        display.classList.toggle('is-empty', !allowEmpty);
      } else {
        display.textContent = label;
        display.classList.remove('is-empty');
      }
      hidden.dispatchEvent(new Event('change', { bubbles: true }));
      if (submitOnChange && options && options.userInitiated && previous !== hidden.value) {
        const form = root.closest('form');
        if (form) form.submit();
      }
    }

    function escHtml(str) {
      return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
    }

    function renderItems(items, query) {
      scroller.innerHTML = '';

      if (allowEmpty && currentPage === 1 && !query) {
        const emptyOpt = document.createElement('div');
        emptyOpt.className = 'csel__option';
        emptyOpt.textContent = emptyLabel;
        if (!hidden.value) emptyOpt.classList.add('is-selected');
        emptyOpt.addEventListener('mousedown', function (e) {
          e.preventDefault();
          setSelected('', '', { userInitiated: true });
          close();
        });
        scroller.appendChild(emptyOpt);
      }

      if (!items.length) {
        const empty = document.createElement('div');
        empty.className = 'csel__empty';
        empty.textContent = 'Ничего не найдено';
        scroller.appendChild(empty);
        return;
      }

      items.forEach(function (item) {
        const el = document.createElement('div');
        el.className = 'csel__option';
        if (String(hidden.value) === String(item.id)) el.classList.add('is-selected');
        const text = item.name || item.url || ('#' + item.id);
        if (query) {
          const idx = text.toLowerCase().indexOf(query.toLowerCase());
          if (idx >= 0) {
            el.innerHTML =
              escHtml(text.slice(0, idx)) +
              '<mark>' + escHtml(text.slice(idx, idx + query.length)) + '</mark>' +
              escHtml(text.slice(idx + query.length));
          } else {
            el.textContent = text;
          }
        } else {
          el.textContent = text;
        }
        el.addEventListener('mousedown', function (e) {
          e.preventDefault();
          setSelected(item.id, text, { userInitiated: true });
          close();
        });
        scroller.appendChild(el);
      });
    }

    function updateFooter() {
      pageInfo.textContent = totalPages > 0 ? (currentPage + ' / ' + totalPages) : '0';
      prevBtn.disabled = currentPage <= 1;
      nextBtn.disabled = currentPage >= totalPages;
    }

    async function load(page, query) {
      const ticket = ++inflight;
      const url = new URL(endpoint, window.location.origin);
      url.searchParams.set('page', page);
      url.searchParams.set('per_page', DEFAULT_PER_PAGE);
      if (query) url.searchParams.set('q', query);
      try {
        const res = await fetch(url.toString(), {
          credentials: 'same-origin',
          headers: { 'Accept': 'application/json' },
        });
        if (!res.ok) throw new Error('HTTP ' + res.status);
        const data = await res.json();
        if (ticket !== inflight) return;
        currentPage = data.page;
        totalPages = data.total_pages || 1;
        renderItems(data.items || [], query);
        updateFooter();
      } catch (err) {
        if (ticket !== inflight) return;
        scroller.innerHTML = '';
        const empty = document.createElement('div');
        empty.className = 'csel__empty';
        empty.textContent = 'Ошибка загрузки';
        scroller.appendChild(empty);
        totalPages = 1;
        currentPage = 1;
        updateFooter();
      }
    }

    function open() {
      panel.hidden = false;
      trigger.classList.add('is-open');
      trigger.setAttribute('aria-expanded', 'true');
      searchInput.value = lastQuery;
      load(currentPage, lastQuery);
      requestAnimationFrame(() => searchInput.focus());
    }

    function close() {
      panel.hidden = true;
      trigger.classList.remove('is-open');
      trigger.setAttribute('aria-expanded', 'false');
    }

    trigger.addEventListener('click', function () {
      if (!panel.hidden) {
        close();
        return;
      }
      document.querySelectorAll('.csel__panel:not([hidden])').forEach(p => {
        p.hidden = true;
        const t = p.parentNode.querySelector('.csel__trigger');
        if (t) t.classList.remove('is-open');
      });
      open();
    });

    searchInput.addEventListener('input', function () {
      const q = this.value.trim();
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => {
        lastQuery = q;
        currentPage = 1;
        load(currentPage, lastQuery);
      }, SEARCH_DEBOUNCE_MS);
    });

    prevBtn.addEventListener('click', function () {
      if (currentPage > 1) load(currentPage - 1, lastQuery);
    });
    nextBtn.addEventListener('click', function () {
      if (currentPage < totalPages) load(currentPage + 1, lastQuery);
    });

    document.addEventListener('click', function (e) {
      if (!root.contains(e.target)) close();
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && !panel.hidden) close();
    });

    if (initialId) {
      setSelected(initialId, initialLabel || ('#' + initialId));
    } else {
      setSelected('', '');
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initAll);
  } else {
    initAll();
  }

})();
