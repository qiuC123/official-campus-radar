document.querySelectorAll('[data-column]').forEach((control) => {
  if (control.type !== 'checkbox') return;
  const key = `radar-column-${control.dataset.column}`;
  control.checked = localStorage.getItem(key) !== 'hidden';
  const update = () => document.querySelectorAll(`th[data-column="${control.dataset.column}"], td[data-column="${control.dataset.column}"]`).forEach((cell) => { cell.hidden = !control.checked; });
  update();
  control.addEventListener('change', () => { localStorage.setItem(key, control.checked ? 'shown' : 'hidden'); update(); });
});
