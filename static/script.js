/**
 * 중고책 가격 비교 웹서비스 - 프론트엔드 로직
 * =============================================
 * - 검색 API 호출 및 결과 렌더링
 * - 실시간 정렬 (정확도, 가격)
 * - 로딩/에러 상태 관리
 */

// ── DOM 요소 참조 ──
const searchForm = document.getElementById('search-form');
const searchInput = document.getElementById('search-input');
const searchBtn = document.getElementById('search-btn');
const loadingEl = document.getElementById('loading');
const errorBanner = document.getElementById('error-banner');
const errorText = document.getElementById('error-text');
const resultsSection = document.getElementById('results-section');
const resultsCount = document.getElementById('results-count');
const resultsList = document.getElementById('results-list');
const queryDisplay = document.getElementById('query-display');
const sortSelect = document.getElementById('sort-select');

// 전역 상태
let currentResults = [];
let currentQuery = "";

// ── 가격 포맷팅 (천 단위 콤마) ──
function formatPrice(price) {
  if (!price || price === 0) return '가격 정보 없음';
  return price.toLocaleString('ko-KR');
}

function getStoreBadgeClass(store) {
  if (store.includes('알라딘')) return 'store-badge--aladin';
  if (store.includes('예스24') || store.includes('YES24')) return 'store-badge--yes24';
  if (store.includes('개똥이네')) return 'store-badge--gaeddong';
  return '';
}

function getStoreIcon(store) {
  if (store.includes('알라딘')) return '📕';
  if (store.includes('예스24') || store.includes('YES24')) return '📘';
  if (store.includes('개똥이네')) return '📗';
  return '📖';
}

// ── 대체 이미지 (표지가 없을 때) ──
const DEFAULT_COVER = 'data:image/svg+xml;charset=UTF-8,' + encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="100" height="140" viewBox="0 0 100 140"><rect width="100" height="140" fill="#2d3748"/><text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" fill="#a0aec0" font-size="14">No Image</text></svg>');

function showLoading() {
  loadingEl.classList.add('active');
  resultsSection.classList.remove('active');
  errorBanner.classList.remove('active');
  searchBtn.disabled = true;
  searchBtn.textContent = '검색 중...';
}

function hideLoading() {
  loadingEl.classList.remove('active');
  searchBtn.disabled = false;
  searchBtn.textContent = '검색';
}

function showError(messages) {
  if (messages && messages.length > 0) {
    errorText.innerHTML = messages
      .map(msg => `<span class="error-banner__icon">⚠️</span>${msg}`)
      .join('<br>');
    errorBanner.classList.add('active');
  }
}

function showResults() {
  resultsSection.classList.add('active');
}

/**
 * 정확도 계산 알고리즘
 * 0: 완벽 일치, 1: 제목에 포함, 2: 키워드 분산 포함, 3: 기타
 */
function calculateAccuracy(title, query) {
  const t = normalizeTitle(title);
  const q = normalizeTitle(query);
  
  if (t === q) return 0;
  if (t.startsWith(q)) return 1;
  if (t.includes(q)) return 2;
  return 3;
}

function normalizeTitle(title) {
  // 괄호 및 그 안의 내용 제거 ([중고], (양장) 등)
  let clean = title.replace(/\[.*?\]|\(.*?\)|<.*?>/g, '');
  // 특수문자 및 공백 제거
  clean = clean.replace(/[^a-zA-Z0-9가-힣]/g, '');
  return clean.toLowerCase();
}

function strictNormalizeTitle(title) {
  // 괄호는 살리고 특수문자/공백만 제거 (더 보수적인 병합)
  let clean = title.replace(/[^a-zA-Z0-9가-힣\(\)\[\]]/g, '');
  return clean.toLowerCase();
}

function extractIsbn(isbnStr) {
  if (!isbnStr) return null;
  const match13 = isbnStr.match(/\b\d{13}\b/);
  if (match13) return match13[0];
  const match10 = isbnStr.match(/\b\d{10}\b/);
  if (match10) return match10[0];
  return null;
}

function groupResults(results) {
  const groups = []; // 배열로 관리
  
  results.forEach(item => {
    const itemIsbn = extractIsbn(item.isbn);
    const normalizedTitle = normalizeTitle(item.title);
    const strictTitle = strictNormalizeTitle(item.title);
    if (!normalizedTitle && !itemIsbn) return; 

    let targetGroup = null;

    // 1. ISBN 일치하는 그룹 찾기
    if (itemIsbn) {
      targetGroup = groups.find(g => g.isbn === itemIsbn);
    }
    
    // 2. ISBN이 없거나 못 찾은 경우, "엄격하게 정규화된 제목"이 일치하는 그룹 찾기
    if (!targetGroup && strictTitle) {
      targetGroup = groups.find(g => strictNormalizeTitle(g.title) === strictTitle);
    }

    if (!targetGroup) {
      targetGroup = {
        title: item.title,
        normalizedTitle: normalizedTitle,
        isbn: itemIsbn,
        cover: item.cover,
        author: item.author,
        publisher: item.publisher,
        stores: []
      };
      groups.push(targetGroup);
    } else {
      // 기존 그룹에 ISBN이 없고 현재 아이템에 ISBN이 있다면 갱신
      if (!targetGroup.isbn && itemIsbn) {
        targetGroup.isbn = itemIsbn;
      }
    }
    targetGroup.stores.push(item);
  });
  
  // 그룹별 최저가 및 대표 메타데이터(표지, 작가) 보정
  return groups.map(g => {
    const validPrices = g.stores.filter(s => s.price > 0).map(s => s.price);
    g.minPrice = validPrices.length > 0 ? Math.min(...validPrices) : 0;
    
    // 표지 이미지가 없거나 Noimg인 경우, 다른 서점의 표지로 대체
    if (!g.cover || g.cover.includes('Noimg')) {
      const betterCover = g.stores.find(s => s.cover && !s.cover.includes('Noimg'));
      if (betterCover) g.cover = betterCover.cover;
    }
    
    // 작가 정보 보정
    if (!g.author) {
      const betterAuthor = g.stores.find(s => s.author);
      if (betterAuthor) g.author = betterAuthor.author;
    }
    
    return g;
  });
}

/**
 * 정렬 및 화면 렌더링
 */
function sortAndRenderResults() {
  const sortValue = sortSelect ? sortSelect.value : 'accuracy';
  
  // 1. 도서명+ISBN 기준으로 결과 그룹핑
  const grouped = groupResults(currentResults);
  
  // 2. 정렬 로직 (그룹 단위로 정렬)
  grouped.sort((a, b) => {
    if (a.minPrice === 0 && b.minPrice !== 0) return 1;
    if (a.minPrice !== 0 && b.minPrice === 0) return -1;
    
    if (sortValue === 'accuracy') {
      const accA = calculateAccuracy(a.title, currentQuery);
      const accB = calculateAccuracy(b.title, currentQuery);
      if (accA !== accB) return accA - accB; 
      return a.minPrice - b.minPrice; 
    } else if (sortValue === 'price_asc') {
      return a.minPrice - b.minPrice;
    } else if (sortValue === 'price_desc') {
      return b.minPrice - a.minPrice;
    }
    return 0;
  });
  
  renderCards(grouped);
}

function renderCards(groups) {
  if (!groups || groups.length === 0) {
    resultsList.innerHTML = `
      <div class="empty-state">
        <div class="empty-state__icon">📚</div>
        <div class="empty-state__title">검색 결과가 없습니다</div>
        <div class="empty-state__desc">다른 검색어로 다시 시도해 보세요</div>
      </div>
    `;
    return;
  }

  resultsList.innerHTML = groups.map((group, index) => {
    // 3. 그룹 내 상점들을 플랫폼별로 분류
    const plats = { '알라딘': [], '예스24': [], '개똥이네': [], '기타': [] };
    group.stores.forEach(item => {
      let p = '기타';
      if(item.store.includes('알라딘')) p = '알라딘';
      else if(item.store.includes('예스24') || item.store.includes('YES24')) p = '예스24';
      else if(item.store.includes('개똥이네')) p = '개똥이네';
      else plats[p] = []; // fallback
      if(!plats[p]) plats[p] = [];
      plats[p].push(item);
    });

    let storesHtml = '';
    const groupMinPrice = group.minPrice;

    for (const p in plats) {
      const items = plats[p];
      if (items.length === 0) continue;
      
      items.sort((a, b) => {
        if (a.price === 0) return 1;
        if (b.price === 0) return -1;
        return a.price - b.price;
      });

      const bestItem = items[0];
      const isLowest = bestItem.price > 0 && bestItem.price === groupMinPrice;
      const priceText = bestItem.price > 0
        ? `<span class="price-value ${isLowest ? 'price-value--lowest' : ''}">${formatPrice(bestItem.price)}원</span>`
        : '<span class="price-value" style="color: var(--text-muted);">가격없음</span>';

      storesHtml += `
        <div class="store-platform-group">
          <div class="store-row">
            <div class="store-row__name">
              <span class="store-badge ${getStoreBadgeClass(bestItem.store)}">${getStoreIcon(bestItem.store)} ${bestItem.store}</span>
              <span class="store-row__cond">${bestItem.condition || '중고'}</span>
            </div>
            <div class="store-row__action">
              ${isLowest ? '<span class="lowest-badge">🏷️ 최저가</span>' : ''}
              ${priceText}
              <a href="${bestItem.link}" target="_blank" rel="noopener noreferrer" class="store-row__btn">바로가기</a>
            </div>
          </div>
      `;

      if (items.length > 1) {
        const restItemsHtml = items.slice(1).map(item => `
          <div class="store-row store-row--sub">
            <div class="store-row__name">
              <span class="store-row__cond" style="margin-left:24px; color:var(--text-muted);">└ ${item.condition || '중고'}</span>
            </div>
            <div class="store-row__action">
              <span class="price-value">${formatPrice(item.price)}원</span>
              <a href="${item.link}" target="_blank" rel="noopener noreferrer" class="store-row__btn store-row__btn--sub">바로가기</a>
            </div>
          </div>
        `).join('');

        const accordionId = `acc_${Math.random().toString(36).substr(2, 9)}`;
        storesHtml += `
          <div class="store-accordion">
            <button type="button" class="store-accordion__toggle" onclick="document.getElementById('${accordionId}').classList.toggle('active'); this.classList.toggle('active')">
              + ${items.length - 1}개의 매물 더보기 <span class="store-accordion__icon">▼</span>
            </button>
            <div id="${accordionId}" class="store-accordion__content">
              ${restItemsHtml}
            </div>
          </div>
        `;
      }
      storesHtml += `</div>`; // end store-platform-group
    }

    const metaParts = [];
    if (group.author) metaParts.push(`<span class="meta-author">${group.author}</span>`);
    if (group.publisher) metaParts.push(`<span class="meta-publisher">${group.publisher}</span>`);
    if (group.isbn) metaParts.push(`<span class="meta-isbn">ISBN: ${group.isbn}</span>`);
    const metaHtml = metaParts.length > 0 ? `<div class="book-meta">${metaParts.join('<span class="meta-divider">|</span>')}</div>` : '';

    const delay = index * 0.04;

    return `
      <div class="book-group-card" style="animation-delay: ${delay}s">
        <div class="bgc-cover-wrap">
          <img src="${group.cover || DEFAULT_COVER}" alt="${group.title} 표지" onerror="this.src='${DEFAULT_COVER}'" class="bgc-cover">
        </div>
        <div class="bgc-info">
          <h3 class="book-title" title="${group.title}">${group.title}</h3>
          ${metaHtml}
          <div class="store-list">
            ${storesHtml}
          </div>
        </div>
      </div>
    `;
  }).join('');
}

// ── 검색 API 호출 ──
async function performSearch(query) {
  showLoading();
  currentQuery = query;

  try {
    const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
    if (!response.ok) {
      throw new Error(`서버 응답 오류: ${response.status}`);
    }

    const data = await response.json();
    currentResults = data.results || [];
    
    queryDisplay.textContent = data.query;
    resultsCount.innerHTML = `총 <strong>${data.total}</strong>건`;
    showError(data.errors);
    
    sortAndRenderResults();
    showResults();

  } catch (error) {
    console.error('검색 오류:', error);
    showError([`검색 중 오류가 발생했습니다: ${error.message}`]);
    resultsSection.classList.remove('active');
  } finally {
    hideLoading();
  }
}

// ── 이벤트 리스너 등록 ──
searchForm.addEventListener('submit', (e) => {
  e.preventDefault();
  const query = searchInput.value.trim();
  if (!query) {
    searchInput.focus();
    return;
  }
  performSearch(query);
});

searchInput.addEventListener('keypress', (e) => {
  if (e.key === 'Enter') {
    e.preventDefault();
    searchForm.dispatchEvent(new Event('submit'));
  }
});

if (sortSelect) {
  sortSelect.addEventListener('change', () => {
    sortAndRenderResults();
  });
}

window.addEventListener('DOMContentLoaded', () => {
  searchInput.focus();
});
