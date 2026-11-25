'use strict';
const $ = (selector) => document.querySelector(selector);
const all = (selector) => Array.from(document.querySelectorAll(selector));
const rtl = document.documentElement.dir === 'rtl';
const reduced = matchMedia('(prefers-reduced-motion: reduce)');
const menu = $('#menu');
menu.addEventListener('click', () => {
  const open = $('#nav').classList.toggle('open');
  menu.setAttribute('aria-expanded', String(open));
});
const frames = all('.frame');
if (frames.length) {
  let slide = 0;
  let paused = reduced.matches;
  let timer;
  const selectors = all('[data-slide]');
  function show(index) {
    slide = index;
    frames.forEach((frame, i) => { frame.hidden = i !== index; });
    selectors.forEach((button, i) => button.setAttribute('aria-pressed', String(i === index)));
  }
  function playback() {
    clearInterval(timer);
    $('.hero-media').classList.toggle('paused', paused);
    $('#pause').textContent = paused ? '▷' : 'Ⅱ';
    $('#pause').setAttribute('aria-pressed', String(paused));
    if (!paused && !document.hidden) timer = setInterval(() => show((slide + 1) % frames.length), 7600);
  }
  selectors.forEach((button,i) => button.addEventListener('click', () => { show(i); paused = true; playback(); }));
  $('#pause').addEventListener('click', () => { paused = !paused; playback(); });
  document.addEventListener('visibilitychange', playback);
  reduced.addEventListener('change', () => { paused = reduced.matches; playback(); });
  playback();
}
all('[data-scroll]').forEach(button => button.addEventListener('click', () => {
  const rail = $('.rail');
  const step = rail.firstElementChild.getBoundingClientRect().width + parseFloat(getComputedStyle(rail).gap);
  rail.scrollBy({ left: step * Number(button.dataset.scroll) * (rtl ? -1 : 1), behavior: reduced.matches ? 'auto' : 'smooth' });
}));
function filter() {
  const cards = all('.grid [data-sector], .grid [data-project]');
  for (const card of cards) {
    const match = (!$('#sector')?.value || card.dataset.sector === $('#sector').value)
      && (!$('#service')?.value || card.dataset.services?.split(' ').includes($('#service').value))
      && (!$('#gallery-project')?.value || card.dataset.project === $('#gallery-project').value)
      && (!$('#kind')?.value || $('#kind').value === (card.matches('.movie') ? 'video' : 'photo'));
    card.hidden = !match;
    if (!match) card.querySelector('video')?.pause();
  }
  $('#empty').hidden = cards.some(card => !card.hidden);
}
all('.filters select').forEach(select => select.addEventListener('change', filter));
const dialog = $('dialog');
let gallery = [], index = 0;
function display(i) {
  index = (i + gallery.length) % gallery.length;
  const {photo,title,link} = gallery[index].dataset;
  $('#large').src = photo;
  $('#large').alt = title;
  $('#caption').textContent = title + ' ↗';
  $('#caption').href = link;
}
all('.media').forEach(button => button.addEventListener('click', () => {
  gallery = all('.media:not([hidden])');
  display(gallery.indexOf(button));
  dialog.showModal();
}));
$('.close').addEventListener('click', () => dialog.close());
all('[data-step]').forEach(button => button.addEventListener('click', () => display(index + Number(button.dataset.step))));
dialog.addEventListener('keydown', event => {
  if (['ArrowLeft','ArrowRight'].includes(event.key)) display(index + (event.key === 'ArrowRight' ? 1 : -1) * (rtl ? -1 : 1));
});
let touchX;
dialog.addEventListener('touchstart', e => {touchX=e.changedTouches[0].clientX;},{passive:true});
dialog.addEventListener('touchend', e => {
  const diff=touchX-e.changedTouches[0].clientX;
  if(Math.abs(diff)>55) display(index+Math.sign(diff)*(rtl?-1:1));
},{passive:true});
const offlineForm = document.querySelector('form[data-offline]');
if (offlineForm) {
  const params = new URLSearchParams(location.search);
  const names = JSON.parse($('#project-names').textContent);
  const topic = params.get('type');
  if (['project','tender','quality'].includes(topic)) offlineForm.elements.type.value=topic;
  offlineForm.elements.message.value=names[params.get('project')] || '';
  const switcher=document.querySelector('.headtools > a');
  switcher.href+=location.search;
  offlineForm.addEventListener('submit', event => {
    event.preventDefault();
    const fields=offlineForm.elements;
    const subject=fields.type.selectedOptions[0].text+' · '+fields.company.value;
    const body=[fields.message.value,'',fields.name.value,fields.company.value,fields.email.value].join('\n');
    const status=$('#draft-message');
    status.textContent=rtl?'أكمل الإرسال في تطبيق البريد، ويمكنك إضافة مرفقات هناك.':'Finish sending in your email app. You can add attachments there.';
    location.href='mailto:info@redowlco.com?subject='+encodeURIComponent(subject)+'&body='+encodeURIComponent(body);
  });
}
