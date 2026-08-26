const statuses = ["未投递", "已投递", "已笔试", "已面试", "未通过", "面试通过", "暂不投递"];
const cities = ["北京", "上海", "杭州", "深圳", "广州", "成都", "武汉", "全国", "远程"];

const batches = [
  {
    id: 1, company: "星河科技", companyType: "民企", industry: "互联网/科技", recruitmentType: "校园招聘", audience: "2027届",
    title: "星河科技 2027 届校园招聘", updated: "2026-08-26", deadline: "2026-09-01", official: "https://example.invalid/galaxy", status: "active",
    positions: [
      ["后端开发工程师", ["上海", "杭州"], "2026-08-26"], ["算法工程师", ["北京"], "2026-08-25"],
      ["产品经理", ["深圳"], "2026-08-24"], ["数据分析师", ["上海"], "2026-08-23"],
      ["测试开发工程师", ["全国"], "2026-08-22"], ["客户端开发工程师", ["广州"], "2026-08-21"],
      ["交互设计师", ["远程"], "2026-08-20"],
    ],
  },
  {
    id: 2, company: "远航能源", companyType: "国企", industry: "能源/电力", recruitmentType: "校园招聘", audience: "2026届",
    title: "远航能源集团秋季校园招聘", updated: "2026-08-24", deadline: "", official: "https://example.invalid/energy", status: "active",
    positions: [["电气工程师", ["武汉", "全国"], "2026-08-24"], ["财务管理岗", ["北京"], "2026-08-20"]],
  },
  {
    id: 3, company: "云帆智能", companyType: "外企", industry: "互联网/科技", recruitmentType: "实习招聘", audience: "实习生",
    title: "云帆智能长期实习生招聘", updated: "2026-08-23", deadline: "2026-10-31", official: "https://example.invalid/cloud", status: "active",
    positions: [["前端开发实习生", ["远程", "杭州"], "2026-08-23"], ["交互设计实习生", ["远程"], "2026-08-21"]],
  },
  {
    id: 4, company: "青峦银行", companyType: "国企", industry: "金融", recruitmentType: "校园招聘", audience: "2025届",
    title: "青峦银行管理培训生项目", updated: "2026-08-20", deadline: "2026-09-20", official: "https://example.invalid/bank", status: "active",
    positions: [["金融科技管培生", ["北京", "上海", "深圳"], "2026-08-20"], ["风险管理岗", ["北京"], "2026-08-19"]],
  },
  {
    id: 5, company: "矩阵机器人", companyType: "外企", industry: "制造业", recruitmentType: "校园招聘", audience: "2028届",
    title: "矩阵机器人全球校园招聘", updated: "2026-08-18", deadline: "2026-11-30", official: "https://example.invalid/robot", status: "active",
    positions: [["机器人控制算法", ["深圳"], "2026-08-18"], ["机械设计", ["上海"], "2026-08-17"]],
  },
  {
    id: 6, company: "海岳通信", companyType: "民企", industry: "通信", recruitmentType: "校园招聘", audience: "2024届",
    title: "海岳通信春季补录", updated: "2026-05-12", deadline: "2026-06-30", official: "https://example.invalid/telecom", status: "history",
    positions: [["网络研发工程师", ["成都"], "2026-05-12"], ["无线通信工程师", ["武汉"], "2026-05-11"]],
  },
];

let currentView = "active";
let filteredBatches = [];

function choiceMarkup(name, values) {
  return values.map(value => `<label class="choice"><input type="checkbox" name="${name}" value="${value}">${value}</label>`).join("");
}

document.querySelector("#city-options").innerHTML = choiceMarkup("city", cities);

function selected(form, name) {
  return [...form.querySelectorAll(`[name="${name}"]:checked`)].map(item => item.value);
}

function effectivePositions(batch, form) {
  const positionKeyword = form.position.value.trim().toLowerCase();
  const selectedCities = selected(form, "city");
  return batch.positions.filter(([title, locations]) => {
    const cityMatch = !selectedCities.length || locations.some(city => selectedCities.includes(city) || city === "全国" || city === "远程");
    return (!positionKeyword || title.toLowerCase().includes(positionKeyword)) && cityMatch;
  });
}

function filterBatches() {
  const form = document.querySelector("#filter-form");
  const company = form.company.value.trim().toLowerCase();
  filteredBatches = batches.filter(batch => {
    if (batch.status !== currentView) return false;
    if (company && !batch.company.toLowerCase().includes(company)) return false;
    for (const key of ["companyType", "industry", "recruitmentType", "audience"]) {
      if (form[key].value && batch[key] !== form[key].value) return false;
    }
    if (form.deadline.value && (!batch.deadline || batch.deadline > form.deadline.value)) return false;
    return effectivePositions(batch, form).length > 0;
  }).sort((a, b) => b.updated.localeCompare(a.updated));
  render();
}

function typeClass(companyType) {
  return { "民企": "private", "国企": "state", "外企": "foreign" }[companyType] || "other";
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
  return `<tr data-batch-id="${batch.id}">
    <td class="company-cell"><strong>${batch.company}</strong><small title="${batch.title}">${batch.title}</small></td>
    <td><span class="badge company-${typeClass(batch.companyType)}">${batch.companyType}</span></td>
    <td>${batch.industry}</td>
    <td><span class="badge recruit-badge">${batch.recruitmentType}</span></td>
    <td><span class="badge audience-badge">${batch.audience}</span></td>
    <td class="locations-cell">${allLocations.join("、")}</td>
    <td><button type="button" class="positions-summary" title="${positionText}">${positionText}</button></td>
    <td><select class="batch-progress" aria-label="${batch.company}投递进度">${options}</select></td>
    <td class="date-cell">${batch.updated}</td>
    <td class="deadline-cell">${batch.deadline || "招满为止"}</td>
    <td><a class="action-link apply" href="${batch.official}" onclick="return false">投递</a></td>
    <td><a class="action-link notice" href="${batch.official}" onclick="return false">公告</a></td>
  </tr>`;
}

function tableMarkup() {
  if (!filteredBatches.length) return `<div class="empty">当前条件下没有${currentView === "active" ? "招聘中的" : "历史"}批次。</div>`;
  return `<table class="recruitment-table">
    <thead><tr>
      <th>公司名称</th><th>公司类型</th><th>所属行业</th><th>招聘类型</th><th>招聘对象</th><th>工作地点</th>
      <th>岗位 <small>（代表岗位）</small></th><th>投递进度</th><th>更新时间</th><th>投递截止</th><th>相关链接</th><th>招聘公告</th>
    </tr></thead>
    <tbody>${filteredBatches.map(rowMarkup).join("")}</tbody>
  </table>`;
}

function updateMetrics() {
  const positions = filteredBatches.flatMap(batch => effectivePositions(batch, document.querySelector("#filter-form")).map(position => ({ batch, position })));
  document.querySelector("#metric-active").textContent = positions.length;
  document.querySelector("#metric-recent").textContent = positions.filter(({ position }) => position[2] >= "2026-08-24").length;
  document.querySelector("#metric-deadline").textContent = positions.filter(({ batch }) => batch.deadline && batch.deadline <= "2026-09-02").length;
  document.querySelector("#metric-companies").textContent = new Set(filteredBatches.map(batch => batch.company)).size;
}

function render() {
  document.querySelector("#batch-list").innerHTML = tableMarkup();
  document.querySelector("#batch-count").textContent = `${filteredBatches.length} 个招聘批次 · 原型每页最多 20 个`;
  document.querySelector("#result-hint").textContent = `找到 ${filteredBatches.length} 个招聘批次`;
  updateMetrics();
}

document.querySelector("#filter-form").addEventListener("submit", event => { event.preventDefault(); filterBatches(); });
document.querySelector("#reset-filters").addEventListener("click", () => { document.querySelector("#filter-form").reset(); filterBatches(); });
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

filterBatches();
