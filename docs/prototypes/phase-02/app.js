const statuses = ["未投递", "已投递", "已笔试", "已面试", "未通过", "面试通过", "暂不投递"];
const cities = ["北京", "上海", "杭州", "深圳", "广州", "成都", "武汉", "全国", "远程"];
const optionalColumns = [
  ["companyType", "公司类型"], ["industry", "行业"], ["recruitmentType", "招聘类型"],
  ["audience", "招聘对象"], ["updated", "更新时间"], ["deadline", "截止时间"], ["official", "官方招聘页"],
];
const batches = [
  {
    id: 1, company: "星河科技", companyType: "互联网/科技", industry: "互联网", recruitmentType: "校园招聘", audience: "2027届",
    title: "星河科技 2027 届校园招聘", updated: "2026-08-26", deadline: "2026-09-01", official: "https://example.invalid/galaxy", status: "active",
    positions: [
      ["后端开发工程师", ["上海", "杭州"], "负责业务服务与数据平台研发。\n要求：熟悉至少一门后端语言，具备扎实的计算机基础。", "未投递", "2026-08-26", true],
      ["算法工程师", ["北京"], "参与推荐与搜索模型的训练、评估和工程化。", "已投递", "2026-08-25", true],
      ["产品经理", ["深圳"], "负责需求分析、产品设计和跨团队协作。", "未投递", "2026-08-24", true],
      ["数据分析师", ["上海"], "构建业务指标体系并输出洞察。", "已笔试", "2026-08-23", true],
      ["测试开发工程师", ["全国"], "建设自动化测试和质量平台。", "暂不投递", "2026-08-22", true],
    ],
  },
  {
    id: 2, company: "远航能源", companyType: "央企/国企", industry: "新能源", recruitmentType: "校园招聘", audience: "2026/2027届",
    title: "远航能源集团秋季校园招聘", updated: "2026-08-24", deadline: "", official: "https://example.invalid/energy", status: "active",
    positions: [
      ["电气工程师", ["武汉", "全国"], "参与新能源项目电气系统设计与交付。", "未投递", "2026-08-24", true],
      ["财务管理岗", ["北京"], "负责预算、核算和经营分析。", "已面试", "2026-08-20", false],
    ],
  },
  {
    id: 3, company: "云帆智能", companyType: "互联网/科技", industry: "科技", recruitmentType: "实习", audience: "在校生",
    title: "云帆智能长期实习生招聘", updated: "2026-08-23", deadline: "2026-10-31", official: "https://example.invalid/cloud", status: "active",
    positions: [
      ["前端开发实习生", ["远程", "杭州"], "参与工作台前端研发，关注可访问性与性能。", "已投递", "2026-08-23", true],
      ["交互设计实习生", ["远程"], "参与复杂信息产品的交互和视觉设计。", "未投递", "2026-08-21", true],
    ],
  },
  {
    id: 4, company: "青峦银行", companyType: "其他", industry: "金融", recruitmentType: "校园招聘", audience: "2027届",
    title: "青峦银行 2027 管培生项目", updated: "2026-08-20", deadline: "2026-09-20", official: "https://example.invalid/bank", status: "active",
    positions: [["金融科技管培生", ["北京", "上海", "深圳"], "轮岗参与数字化银行产品和技术项目。", "面试通过", "2026-08-20", true]],
  },
  {
    id: 5, company: "矩阵机器人", companyType: "互联网/科技", industry: "科技", recruitmentType: "校园招聘", audience: "2027届",
    title: "矩阵机器人全球校园招聘", updated: "2026-08-18", deadline: "2026-11-30", official: "https://example.invalid/robot", status: "active",
    positions: [["机器人控制算法工程师", ["深圳"], "研发运动控制和轨迹规划算法。", "未通过", "2026-08-18", true]],
  },
  {
    id: 6, company: "海岳通信", companyType: "央企/国企", industry: "科技", recruitmentType: "校园招聘", audience: "2026届",
    title: "海岳通信 2026 春季招聘", updated: "2026-05-12", deadline: "2026-06-30", official: "https://example.invalid/telecom", status: "history",
    positions: [["网络研发工程师", ["成都"], "参与通信网络平台研发。", "已面试", "2026-05-12", true]],
  },
];

let currentView = "active";
let filteredBatches = [];

function choiceMarkup(name, values) {
  return values.map(value => `<label class="choice"><input type="checkbox" name="${name}" value="${value}">${value}</label>`).join("");
}
document.querySelector("#city-options").innerHTML = choiceMarkup("city", cities);
document.querySelector("#progress-options").innerHTML = choiceMarkup("progress", statuses);
document.querySelector("#column-options").innerHTML = optionalColumns.map(([key, label]) => `<label class="choice"><input type="checkbox" data-column-toggle="${key}" checked>${label}</label>`).join("");

function selected(form, name) {
  return [...form.querySelectorAll(`[name="${name}"]:checked`)].map(item => item.value);
}

function effectivePositions(batch, form) {
  const positionKeyword = form.position.value.trim().toLowerCase();
  const selectedCities = selected(form, "city");
  const selectedProgress = selected(form, "progress");
  return batch.positions.filter(position => {
    const [title, locations, , progress] = position;
    const cityMatch = !selectedCities.length || locations.some(city => selectedCities.includes(city) || city === "全国" || city === "远程");
    const progressMatch = !selectedProgress.length || selectedProgress.includes(progress);
    return (!positionKeyword || title.toLowerCase().includes(positionKeyword)) && cityMatch && progressMatch;
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

function positionRows(batch, positions) {
  return positions.map((position, index) => {
    const [title, locations, description, progress, updated, directLink] = position;
    const optionMarkup = statuses.map(status => `<option ${status === progress ? "selected" : ""}>${status}</option>`).join("");
    const locationMarkup = locations.map(city => `<span class="tag ${city === "全国" || city === "远程" ? "special" : ""}">${city}</span>`).join("");
    const hidden = index >= 3 ? "hidden" : "";
    return `<tr class="position-row ${index >= 3 ? "extra-position" : ""}" ${hidden} data-batch="${batch.id}" data-position="${index}">
      <td><button class="position-title" aria-expanded="false">${title}</button></td>
      <td><div class="location-tags">${locationMarkup}</div></td>
      <td><select class="progress-select" aria-label="${title}投递进度">${optionMarkup}</select></td>
      <td data-column="updated">${updated}</td>
      <td><a class="apply-link" href="${batch.official}" onclick="return false">${directLink ? "岗位投递" : "批次官网"}</a></td>
    </tr><tr class="description-row" hidden><td colspan="5"><div class="description-box">${description}</div></td></tr>`;
  }).join("");
}

function batchMarkup(batch) {
  const positions = effectivePositions(batch, document.querySelector("#filter-form"));
  const deadlineSoon = batch.deadline && batch.deadline <= "2026-09-02";
  return `<article class="batch-card">
    <header class="batch-head">
      <div><div class="company">${batch.company}</div><div class="batch-title">${batch.title} · ${positions.length} 个匹配岗位</div></div>
      <div class="meta" data-column="companyType"><span>公司类型</span><strong>${batch.companyType}</strong></div>
      <div class="meta" data-column="industry"><span>行业</span><strong>${batch.industry}</strong></div>
      <div class="meta" data-column="recruitmentType"><span>招聘类型</span><strong>${batch.recruitmentType}</strong></div>
      <div class="meta ${deadlineSoon ? "deadline-soon" : ""}" data-column="deadline"><span>截止时间</span><strong>${batch.deadline || "未说明"}</strong></div>
      <a class="official-link" data-column="official" href="${batch.official}" onclick="return false">官方招聘页</a>
    </header>
    <table class="positions"><thead><tr><th>招聘岗位</th><th>城市</th><th>投递进度</th><th data-column="updated">更新时间</th><th>投递入口</th></tr></thead>
    <tbody>${positionRows(batch, positions)}</tbody></table>
    ${positions.length > 3 ? `<footer class="batch-footer"><button class="expand-button" data-expanded="false">展开其余 ${positions.length - 3} 个岗位</button></footer>` : ""}
  </article>`;
}

function updateMetrics() {
  const positions = filteredBatches.flatMap(batch => effectivePositions(batch, document.querySelector("#filter-form")).map(position => ({ batch, position })));
  document.querySelector("#metric-active").textContent = positions.length;
  document.querySelector("#metric-recent").textContent = positions.filter(({ position }) => position[4] >= "2026-08-24").length;
  document.querySelector("#metric-deadline").textContent = positions.filter(({ batch }) => batch.deadline && batch.deadline <= "2026-09-02").length;
  document.querySelector("#metric-progress").textContent = positions.filter(({ position }) => ["已投递", "已笔试", "已面试"].includes(position[3])).length;
}

function applyColumns() {
  document.querySelectorAll("[data-column-toggle]").forEach(control => {
    const hidden = !control.checked;
    document.querySelectorAll(`[data-column="${control.dataset.columnToggle}"]`).forEach(node => node.dataset.hidden = hidden);
  });
}

function render() {
  document.querySelector("#batch-list").innerHTML = filteredBatches.length ? filteredBatches.map(batchMarkup).join("") : `<div class="empty">当前条件下没有${currentView === "active" ? "招聘中的" : "历史"}批次。</div>`;
  document.querySelector("#batch-count").textContent = `${filteredBatches.length} 个招聘批次 · 原型每页最多 20 个`;
  document.querySelector("#result-hint").textContent = `找到 ${filteredBatches.length} 个招聘批次`;
  updateMetrics();
  applyColumns();
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
document.querySelector("#column-options").addEventListener("change", event => {
  if (!event.target.dataset.columnToggle) return;
  localStorage.setItem(`prototype-column-${event.target.dataset.columnToggle}`, event.target.checked ? "show" : "hide");
  applyColumns();
});
document.querySelectorAll("[data-column-toggle]").forEach(control => control.checked = localStorage.getItem(`prototype-column-${control.dataset.columnToggle}`) !== "hide");
document.querySelector("#batch-list").addEventListener("click", event => {
  const titleButton = event.target.closest(".position-title");
  if (titleButton) {
    const row = titleButton.closest("tr");
    const detail = row.nextElementSibling;
    detail.hidden = !detail.hidden;
    titleButton.setAttribute("aria-expanded", String(!detail.hidden));
  }
  const expandButton = event.target.closest(".expand-button");
  if (expandButton) {
    const expanded = expandButton.dataset.expanded === "true";
    expandButton.closest(".batch-card").querySelectorAll(".extra-position").forEach(row => row.hidden = expanded);
    expandButton.dataset.expanded = String(!expanded);
    expandButton.textContent = expanded ? "展开更多岗位" : "收起额外岗位";
  }
});
document.querySelector("#batch-list").addEventListener("change", event => {
  if (!event.target.matches(".progress-select")) return;
  const row = event.target.closest(".position-row");
  const batch = batches.find(item => item.id === Number(row.dataset.batch));
  batch.positions[Number(row.dataset.position)][3] = event.target.value;
  const toast = document.querySelector("#toast");
  toast.textContent = `模拟保存：${event.target.value}`;
  toast.classList.add("show");
  setTimeout(() => toast.classList.remove("show"), 1500);
  updateMetrics();
});

filterBatches();
