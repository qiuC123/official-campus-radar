const statuses = ["未投递", "已投递", "已笔试", "已面试", "未通过", "面试通过", "暂不投递"];
const prototypeToday = "2026-08-26";
const filterDefinitions = {
  companyType: ["央国企", "民企", "事业单位", "银行", "外资", "中外合资", "社会机构"],
  recruitmentType: ["春招", "秋招", "秋招补录", "秋招提前批", "实习", "春招补录"],
  progress: statuses,
  location: ["北京", "天津", "河北", "山西", "内蒙古", "辽宁", "吉林", "黑龙江", "上海", "江苏", "浙江", "安徽", "福建", "江西", "山东", "河南", "湖北", "湖南", "广东", "广西", "海南", "重庆", "四川", "贵州", "云南", "西藏", "陕西", "甘肃", "青海", "宁夏", "新疆", "香港", "澳门", "台湾"],
};
const selectedFilters = { companyType: [], recruitmentType: [], progress: [], location: [] };

const batches = [
  {
    id: 1, company: "星河科技", companyType: "民企", industry: "互联网/科技", recruitmentType: "秋招", audience: "2027届",
    title: "星河科技 2027 届校园招聘", updated: "2026-08-26", deadline: "2026-09-01", official: "https://example.invalid/galaxy", status: "active",
    positions: [
      ["后端开发工程师", ["上海", "浙江"], "2026-08-26"], ["算法工程师", ["北京"], "2026-08-25"],
      ["产品经理", ["广东"], "2026-08-24"], ["数据分析师", ["上海"], "2026-08-23"],
      ["测试开发工程师", ["全国"], "2026-08-22"], ["客户端开发工程师", ["广东"], "2026-08-21"],
      ["交互设计师", ["远程"], "2026-08-20"],
    ],
  },
  {
    id: 2, company: "远航能源", companyType: "央国企", industry: "能源/电力", recruitmentType: "秋招", audience: "2026届",
    title: "远航能源集团秋季校园招聘", updated: "2026-08-24", deadline: "", official: "https://example.invalid/energy", status: "active",
    positions: [["电气工程师", ["湖北", "全国"], "2026-08-24"], ["财务管理岗", ["北京"], "2026-08-20"]],
  },
  {
    id: 3, company: "云帆智能", companyType: "外资", industry: "互联网/科技", recruitmentType: "实习", audience: "实习生",
    title: "云帆智能长期实习生招聘", updated: "2026-08-23", deadline: "2026-10-31", official: "https://example.invalid/cloud", status: "active",
    positions: [["前端开发实习生", ["远程", "浙江"], "2026-08-23"], ["交互设计实习生", ["远程"], "2026-08-21"]],
  },
  {
    id: 4, company: "青峦银行", companyType: "银行", industry: "金融", recruitmentType: "秋招", audience: "2025届",
    title: "青峦银行管理培训生项目", updated: "2026-08-20", deadline: "2026-09-20", official: "https://example.invalid/bank", status: "active",
    positions: [["金融科技管培生", ["北京", "上海", "广东"], "2026-08-20"], ["风险管理岗", ["北京"], "2026-08-19"]],
  },
  {
    id: 5, company: "矩阵机器人", companyType: "中外合资", industry: "制造业", recruitmentType: "秋招提前批", audience: "2028届",
    title: "矩阵机器人全球校园招聘", updated: "2026-08-18", deadline: "2026-11-30", official: "https://example.invalid/robot", status: "active",
    positions: [["机器人控制算法", ["广东"], "2026-08-18"], ["机械设计", ["上海"], "2026-08-17"]],
  },
  {
    id: 6, company: "海岳通信", companyType: "民企", industry: "通信", recruitmentType: "春招补录", audience: "2024届",
    title: "海岳通信春季补录", updated: "2026-05-12", deadline: "2026-06-30", official: "https://example.invalid/telecom", status: "history",
    positions: [["网络研发工程师", ["四川"], "2026-05-12"], ["无线通信工程师", ["湖北"], "2026-05-11"]],
  },
];

let currentView = "active";
let filteredBatches = [];

function updateTrigger(container) {
  const key = container.dataset.filter;
  const label = container.dataset.label;
  const values = selectedFilters[key];
  container.querySelector(".multi-trigger").textContent = values.length
    ? `${label}：${values.length <= 2 ? values.join("、") : `已选 ${values.length} 项`}`
    : label + (key === "location" ? "（省份，最多 5 个）" : "");
}

function closeMultiFilter(container) {
  container.querySelector(".multi-menu").hidden = true;
  container.querySelector(".multi-trigger").setAttribute("aria-expanded", "false");
}

function syncLimitState(container) {
  const max = Number(container.dataset.max || 0);
  const checked = [...container.querySelectorAll(".multi-options input:checked")];
  const message = container.querySelector(".multi-message");
  if (!max) {
    message.textContent = checked.length ? `已选择 ${checked.length} 项` : "";
    return;
  }
  container.querySelectorAll(".multi-options input:not(:checked)").forEach(input => { input.disabled = checked.length >= max; });
  message.textContent = `已选 ${checked.length}/${max} 个省份`;
}

document.querySelectorAll(".multi-filter").forEach(container => {
  const key = container.dataset.filter;
  container.querySelector(".multi-options").innerHTML = filterDefinitions[key]
    .map(value => `<label><input type="checkbox" value="${value}"><span>${value}</span></label>`).join("");
  updateTrigger(container);
});

document.querySelector("#filter-form").addEventListener("click", event => {
  const trigger = event.target.closest(".multi-trigger");
  if (trigger) {
    const container = trigger.closest(".multi-filter");
    document.querySelectorAll(".multi-filter").forEach(item => { if (item !== container) closeMultiFilter(item); });
    const menu = container.querySelector(".multi-menu");
    const opening = menu.hidden;
    if (opening) {
      const applied = selectedFilters[container.dataset.filter];
      container.querySelectorAll(".multi-options input").forEach(input => { input.checked = applied.includes(input.value); input.disabled = false; });
      syncLimitState(container);
    }
    menu.hidden = !opening;
    trigger.setAttribute("aria-expanded", String(opening));
    return;
  }
  const cancel = event.target.closest(".multi-cancel");
  if (cancel) {
    closeMultiFilter(cancel.closest(".multi-filter"));
    return;
  }
  const confirm = event.target.closest(".multi-confirm");
  if (confirm) {
    const container = confirm.closest(".multi-filter");
    selectedFilters[container.dataset.filter] = [...container.querySelectorAll(".multi-options input:checked")].map(input => input.value);
    updateTrigger(container);
    closeMultiFilter(container);
  }
});

document.querySelector("#filter-form").addEventListener("change", event => {
  if (!event.target.matches(".multi-options input")) return;
  const container = event.target.closest(".multi-filter");
  const max = Number(container.dataset.max || 0);
  const checkedCount = container.querySelectorAll(".multi-options input:checked").length;
  if (max && checkedCount > max) event.target.checked = false;
  syncLimitState(container);
});

document.addEventListener("click", event => {
  if (event.target.closest(".multi-filter")) return;
  document.querySelectorAll(".multi-filter").forEach(closeMultiFilter);
});

function parseTerms(value) {
  return value.split(/[，,]/).map(item => item.trim()).filter(Boolean);
}

function effectivePositions(batch, form) {
  const positionKeywords = parseTerms(form.position.value.toLowerCase());
  const wantedLocations = selectedFilters.location;
  return batch.positions.filter(([title, locations]) => {
    const matchesWanted = !wantedLocations.length || locations.some(city => wantedLocations.includes(city));
    const matchesSpecial = !wantedLocations.length || locations.some(city => city === "全国" || city === "远程");
    const cityMatch = matchesWanted || matchesSpecial;
    const keywordMatch = !positionKeywords.length || positionKeywords.some(keyword => title.toLowerCase().includes(keyword));
    return keywordMatch && cityMatch;
  });
}

function daysUntil(deadline) {
  if (!deadline) return null;
  return Math.round((new Date(`${deadline}T00:00:00`) - new Date(`${prototypeToday}T00:00:00`)) / 86400000);
}

function filterBatches() {
  const form = document.querySelector("#filter-form");
  const company = form.company.value.trim().toLowerCase();
  filteredBatches = batches.filter(batch => {
    if (batch.status !== currentView) return false;
    if (company && !batch.company.toLowerCase().includes(company)) return false;
    if (selectedFilters.companyType.length && !selectedFilters.companyType.includes(batch.companyType)) return false;
    if (selectedFilters.recruitmentType.length && !selectedFilters.recruitmentType.includes(batch.recruitmentType)) return false;
    if (form.audience.value && batch.audience !== form.audience.value) return false;
    if (selectedFilters.progress.length && !selectedFilters.progress.includes(batchProgress(batch))) return false;
    return effectivePositions(batch, form).length > 0;
  }).sort((a, b) => b.updated.localeCompare(a.updated));
  render();
}

function typeClass(companyType) {
  return { "民企": "private", "央国企": "state", "外资": "foreign", "中外合资": "foreign", "银行": "bank" }[companyType] || "other";
}

function batchProgress(batch) {
  return localStorage.getItem(`prototype-batch-progress-${batch.id}`) || "未投递";
}

function rowMarkup(batch) {
  const positions = effectivePositions(batch, document.querySelector("#filter-form"));
  const representative = positions.slice(0, 5).map(([title]) => title);
  const positionText = `${representative.join("、")}${positions.length > representative.length ? `，另有 ${positions.length - representative.length} 个岗位` : ""}`;
  const allLocations = [...new Set(positions.flatMap(([, locations]) => locations))];
  const progress = batchProgress(batch);
  const options = statuses.map(status => `<option ${status === progress ? "selected" : ""}>${status}</option>`).join("");
  const positionDetails = positions.map(([title, locations, updated]) => `<li><strong>${title}</strong><span>${locations.join("、")} · 更新 ${updated}</span></li>`).join("");
  return `<tr data-batch-id="${batch.id}">
    <td class="company-cell"><strong>${batch.company}</strong><small title="${batch.title}">${batch.title}</small></td>
    <td><span class="badge company-${typeClass(batch.companyType)}">${batch.companyType}</span></td>
    <td>${batch.industry}</td>
    <td><span class="badge recruit-badge">${batch.recruitmentType}</span></td>
    <td><span class="badge audience-badge">${batch.audience}</span></td>
    <td class="locations-cell">${allLocations.join("、")}</td>
    <td><button type="button" class="positions-summary" aria-expanded="false" title="点击查看全部岗位">${positionText}</button></td>
    <td><select class="batch-progress" aria-label="${batch.company}投递进度">${options}</select></td>
    <td class="date-cell">${batch.updated}</td>
    <td><a class="action-link apply" href="${batch.official}" onclick="return false">投递</a></td>
    <td><a class="action-link notice" href="${batch.official}" onclick="return false">官方页</a></td>
  </tr><tr class="positions-detail-row" data-detail-for="${batch.id}" hidden><td colspan="11"><div class="positions-detail"><strong>全部岗位</strong><ul>${positionDetails}</ul></div></td></tr>`;
}

function tableMarkup() {
  if (!filteredBatches.length) return `<div class="empty">当前条件下没有${currentView === "active" ? "招聘中的" : "历史"}批次。</div>`;
  return `<table class="recruitment-table">
    <thead><tr>
      <th>公司名称</th><th>公司类型</th><th>所属行业</th><th>招聘类型</th><th>招聘对象</th><th>工作地点</th>
      <th>岗位 <small>（点击查看全部）</small></th><th>投递进度</th><th>更新时间</th><th>相关链接</th><th>批次官网</th>
    </tr></thead>
    <tbody>${filteredBatches.map(rowMarkup).join("")}</tbody>
  </table>`;
}

function updateSummary() {
  const todayCount = filteredBatches.filter(batch => batch.updated === prototypeToday).length;
  const recentCount = filteredBatches.filter(batch => batch.updated >= "2026-08-24").length;
  const dueInOneDay = filteredBatches.filter(batch => { const days = daysUntil(batch.deadline); return days !== null && days >= 0 && days <= 1; }).length;
  const dueInThreeDays = filteredBatches.filter(batch => { const days = daysUntil(batch.deadline); return days !== null && days >= 0 && days <= 3; }).length;
  document.querySelector("#filter-summary").textContent = `今日：${todayCount}家｜近三天：${recentCount}家｜1天内截止：${dueInOneDay}家｜3天内截止：${dueInThreeDays}家`;
}

function render() {
  document.querySelector("#batch-list").innerHTML = tableMarkup();
  document.querySelector("#batch-count").textContent = `${filteredBatches.length} 个招聘批次 · 原型每页最多 20 个`;
  updateSummary();
}

document.querySelector("#filter-form").addEventListener("submit", event => { event.preventDefault(); filterBatches(); });
document.querySelector("#reset-filters").addEventListener("click", () => {
  document.querySelector("#filter-form").reset();
  Object.keys(selectedFilters).forEach(key => { selectedFilters[key] = []; });
  document.querySelectorAll(".multi-filter").forEach(container => {
    container.querySelectorAll(".multi-options input").forEach(input => { input.checked = false; input.disabled = false; });
    updateTrigger(container);
    closeMultiFilter(container);
  });
  filterBatches();
});
document.querySelectorAll("[data-view]").forEach(button => button.addEventListener("click", () => {
  currentView = button.dataset.view;
  document.querySelectorAll("[data-view]").forEach(item => item.classList.toggle("active", item === button));
  document.querySelector("#results-title").textContent = currentView === "active" ? "招聘中的批次" : "历史批次";
  filterBatches();
}));
document.querySelectorAll("[data-health-choice]").forEach(button => button.addEventListener("click", () => {
  const panel = document.querySelector(".health-panel");
  panel.dataset.health = button.dataset.healthChoice;
  document.querySelectorAll("[data-health-choice]").forEach(item => item.classList.toggle("selected", item === button));
  const content = {
    healthy: ["运行正常", "最近成功更新：今天 08:20"],
    missing: ["22:00 计划更新未完成", "可以稍后手动更新，本原型不会执行操作"],
    failure: ["1 个来源更新失败", "其他来源保留上次成功数据"],
  }[button.dataset.healthChoice];
  panel.querySelector(".health-title").textContent = content[0];
  panel.querySelector(".health-copy").textContent = content[1];
}));
document.querySelector("#batch-list").addEventListener("change", event => {
  if (!event.target.matches(".batch-progress")) return;
  const batchId = event.target.closest("tr").dataset.batchId;
  localStorage.setItem(`prototype-batch-progress-${batchId}`, event.target.value);
  const toast = document.querySelector("#toast");
  toast.textContent = `模拟保存：${event.target.value}`;
  toast.classList.add("show");
  setTimeout(() => toast.classList.remove("show"), 1500);
});
document.querySelector("#batch-list").addEventListener("click", event => {
  const trigger = event.target.closest(".positions-summary");
  if (!trigger) return;
  const row = trigger.closest("tr");
  const details = row.nextElementSibling;
  details.hidden = !details.hidden;
  trigger.setAttribute("aria-expanded", String(!details.hidden));
});

filterBatches();
