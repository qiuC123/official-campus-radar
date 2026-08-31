const csrf = () => document.cookie.split('; ').find(item => item.startsWith('csrftoken='))?.split('=')[1] || '';
const toast = message => {
  const node = document.querySelector('#toast');
  node.textContent = message;
  node.classList.add('show');
  setTimeout(() => node.classList.remove('show'), 1800);
};

function checkedValues(container) {
  return [...container.querySelectorAll('.multi-options input:checked')].map(input => input.value);
}

function updateTrigger(container) {
  const values = [...container.querySelectorAll('.multi-options input:checked')].map(input => input.nextElementSibling.textContent);
  const label = container.dataset.label;
  container.querySelector('.multi-trigger').textContent = values.length
    ? `${label}：${values.length <= 2 ? values.join('、') : `已选 ${values.length} 项`}`
    : label + (container.dataset.max ? '（省份，最多 5 个）' : '');
}

function syncLimitState(container) {
  const max = Number(container.dataset.max || 0);
  const checked = container.querySelectorAll('.multi-options input:checked').length;
  const message = container.querySelector('.multi-message');
  if (max) {
    container.querySelectorAll('.multi-options input:not(:checked)').forEach(input => { input.disabled = checked >= max; });
    message.textContent = `已选 ${checked}/${max} 个省份`;
  } else {
    message.textContent = checked ? `已选择 ${checked} 项` : '';
  }
}

function restoreSnapshot(container) {
  const saved = JSON.parse(container.dataset.snapshot || '[]');
  container.querySelectorAll('.multi-options input').forEach(input => {
    input.checked = saved.includes(input.value);
    input.disabled = false;
  });
  syncLimitState(container);
  updateTrigger(container);
}

function closeMenu(container, restore = false) {
  if (restore) restoreSnapshot(container);
  container.querySelector('.multi-menu').hidden = true;
  container.querySelector('.multi-trigger').setAttribute('aria-expanded', 'false');
}

function placePositionTooltip(preview) {
  const shell = preview.closest('.table-shell');
  if (!shell) return;
  const previewRect = preview.getBoundingClientRect();
  const shellRect = shell.getBoundingClientRect();
  const spaceAbove = previewRect.top - shellRect.top;
  const spaceBelow = shellRect.bottom - previewRect.bottom;
  preview.classList.toggle('tooltip-above', spaceBelow < 248 && spaceAbove >= 248);
}

document.querySelectorAll('.multi-filter').forEach(container => {
  updateTrigger(container);
  syncLimitState(container);
});

document.querySelector('#filter-form')?.addEventListener('click', event => {
  const trigger = event.target.closest('.multi-trigger');
  if (trigger) {
    const container = trigger.closest('.multi-filter');
    document.querySelectorAll('.multi-filter').forEach(item => { if (item !== container) closeMenu(item, true); });
    const menu = container.querySelector('.multi-menu');
    const opening = menu.hidden;
    if (opening) container.dataset.snapshot = JSON.stringify(checkedValues(container));
    menu.hidden = !opening;
    trigger.setAttribute('aria-expanded', String(opening));
    return;
  }
  const cancel = event.target.closest('.multi-cancel');
  if (cancel) {
    closeMenu(cancel.closest('.multi-filter'), true);
    return;
  }
  const confirm = event.target.closest('.multi-confirm');
  if (confirm) {
    const container = confirm.closest('.multi-filter');
    updateTrigger(container);
    closeMenu(container);
  }
});

document.querySelector('#filter-form')?.addEventListener('change', event => {
  if (!event.target.matches('.multi-options input')) return;
  const container = event.target.closest('.multi-filter');
  const max = Number(container.dataset.max || 0);
  if (max && container.querySelectorAll('.multi-options input:checked').length > max) {
    event.target.checked = false;
    toast('地点最多同时选择 5 个省份');
  }
  syncLimitState(container);
});

document.addEventListener('click', event => {
  if (event.target.closest('.multi-filter')) return;
  document.querySelectorAll('.multi-filter').forEach(container => {
    if (!container.querySelector('.multi-menu').hidden) closeMenu(container, true);
  });
});

document.addEventListener('pointerover', event => {
  const preview = event.target.closest('.positions-preview');
  if (preview) placePositionTooltip(preview);
});

document.addEventListener('click', event => {
  const preview = event.target.closest('.positions-preview');
  const opening = preview && !preview.classList.contains('tooltip-open');
  document.querySelectorAll('.positions-preview.tooltip-open').forEach(item => {
    item.classList.remove('tooltip-open');
  });
  if (opening) {
    placePositionTooltip(preview);
    preview.classList.add('tooltip-open');
  }
});

document.addEventListener('focusin', event => {
  const preview = event.target.closest('.positions-preview');
  if (preview) placePositionTooltip(preview);
});

document.addEventListener('focusout', event => {
  const preview = event.target.closest('.positions-preview');
  if (preview) preview.classList.remove('tooltip-open');
});

document.addEventListener('click', async event => {
  const previewLink = event.target.closest('.preview-external');
  if (previewLink) {
    event.preventDefault();
    toast('这是模拟入口，预览页不会打开企业网站');
  }
});

document.addEventListener('change', async event => {
  const select = event.target.closest('.batch-progress');
  if (!select) return;
  const previous = select.dataset.currentValue;
  if (window.PHASE02_PREVIEW) {
    select.dataset.currentValue = select.value;
    toast(`模拟保存：${select.options[select.selectedIndex].text}`);
    return;
  }
  try {
    const response = await fetch(select.dataset.saveUrl, {
      method: 'POST',
      headers: {'X-CSRFToken': csrf(), 'Content-Type': 'application/x-www-form-urlencoded'},
      body: new URLSearchParams({status: select.value}),
    });
    if (!response.ok) throw new Error();
    select.dataset.currentValue = select.value;
    toast('投递进度已保存');
  } catch (error) {
    select.value = previous;
    toast('保存失败，已恢复原值');
  }
});
