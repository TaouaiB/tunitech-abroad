
function toggleDrawer(open) {
  const drawer = document.querySelector('[data-filter-drawer]');
  const backdrop = document.querySelector('[data-drawer-backdrop]');
  if (!drawer || !backdrop) return;
  drawer.classList.toggle('open', open);
  backdrop.classList.toggle('open', open);
}
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('[data-drawer-open]').forEach(btn => btn.addEventListener('click', () => toggleDrawer(true)));
  document.querySelectorAll('[data-drawer-close]').forEach(btn => btn.addEventListener('click', () => toggleDrawer(false)));
  document.querySelectorAll('.tta-dropzone').forEach(zone => {
    ['dragenter','dragover'].forEach(e => zone.addEventListener(e, ev => { ev.preventDefault(); zone.classList.add('dragover'); }));
    ['dragleave','drop'].forEach(e => zone.addEventListener(e, ev => { ev.preventDefault(); zone.classList.remove('dragover'); }));
  });
});


// v2 polish additions: auto-dismiss toasts with hover pause.
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('[data-toast-autodismiss]').forEach((toast) => {
    const delay = Number(toast.getAttribute('data-toast-autodismiss') || 4000);
    let remaining = delay;
    let startedAt = Date.now();
    let timer = null;
    const hide = () => {
      toast.setAttribute('data-hidden', 'true');
      setTimeout(() => toast.remove(), 320);
    };
    const start = () => {
      startedAt = Date.now();
      timer = setTimeout(hide, remaining);
    };
    const pause = () => {
      if (timer) clearTimeout(timer);
      remaining -= Date.now() - startedAt;
    };
    toast.addEventListener('mouseenter', pause);
    toast.addEventListener('mouseleave', start);
    start();
  });
});
