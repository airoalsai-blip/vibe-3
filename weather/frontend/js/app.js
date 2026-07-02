const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000";
const API_BASE_URL_KEY = "weather_backend_base_url";

const els = {
  refreshButton: document.getElementById("refreshButton"),
  summaryRefreshButton: document.getElementById("summaryRefreshButton"),
  alertReloadButton: document.getElementById("alertReloadButton"),
  saveBackendUrlButton: document.getElementById("saveBackendUrlButton"),
  backendUrlInput: document.getElementById("backendUrlInput"),
  backendUrlLabel: document.getElementById("backendUrlLabel"),
  connectionStatusLabel: document.getElementById("connectionStatusLabel"),
  regionCount: document.getElementById("regionCount"),
  departmentCount: document.getElementById("departmentCount"),
  employeeCount: document.getElementById("employeeCount"),
  selectedRegionLabel: document.getElementById("selectedRegionLabel"),
  currentAlertLabel: document.getElementById("currentAlertLabel"),
  nextDutyLabel: document.getElementById("nextDutyLabel"),
  alertList: document.getElementById("alertList"),
  dutyList: document.getElementById("dutyList"),
  regionList: document.getElementById("regionList"),
  employeeList: document.getElementById("employeeList"),
  policyList: document.getElementById("policyList"),
  historyList: document.getElementById("historyList"),
  regionForm: document.getElementById("regionForm"),
  employeeForm: document.getElementById("employeeForm"),
  manualEntryForm: document.getElementById("manualEntryForm"),
  policyForm: document.getElementById("policyForm"),
  alertForm: document.getElementById("alertForm"),
  importForm: document.getElementById("importForm"),
  importFileInput: document.getElementById("importFileInput"),
  regionSidoInput: document.getElementById("regionSidoInput"),
  regionSigunguInput: document.getElementById("regionSigunguInput"),
  regionAdminCodeInput: document.getElementById("regionAdminCodeInput"),
  employeeDepartmentSelect: document.getElementById("employeeDepartmentSelect"),
  employeeNameInput: document.getElementById("employeeNameInput"),
  employeePositionInput: document.getElementById("employeePositionInput"),
  employeePhoneInput: document.getElementById("employeePhoneInput"),
  employeeEmailInput: document.getElementById("employeeEmailInput"),
  employeeDutyOrderInput: document.getElementById("employeeDutyOrderInput"),
  employeeMemoInput: document.getElementById("employeeMemoInput"),
  manualDepartmentSelect: document.getElementById("manualDepartmentSelect"),
  manualNameInput: document.getElementById("manualNameInput"),
  manualPositionInput: document.getElementById("manualPositionInput"),
  manualPhoneInput: document.getElementById("manualPhoneInput"),
  manualEmailInput: document.getElementById("manualEmailInput"),
  manualDutyOrderInput: document.getElementById("manualDutyOrderInput"),
  policyDepartmentSelect: document.getElementById("policyDepartmentSelect"),
  policyRegionSelect: document.getElementById("policyRegionSelect"),
  alertRegionSelect: document.getElementById("alertRegionSelect"),
  alertTypeInput: document.getElementById("alertTypeInput"),
  alertSeverityInput: document.getElementById("alertSeverityInput"),
  alertChannelSelect: document.getElementById("alertChannelSelect"),
  alertNotifyKindSelect: document.getElementById("alertNotifyKindSelect"),
  alertStatusSelect: document.getElementById("alertStatusSelect"),
  importJobList: document.getElementById("importJobList"),
};

const state = {
  regions: [],
  departments: [],
  employees: [],
  policies: [],
  weatherAlerts: [],
  notificationLogs: [],
  importJobs: [],
  manualEntries: [],
};

let editingPolicyId = null;
let editingManualEntryId = null;
let API_BASE_URL = localStorage.getItem(API_BASE_URL_KEY) || DEFAULT_API_BASE_URL;

function formatRegionLabel(region) {
  return `${region.sido_name ?? "지역"} ${region.sigungu_name ?? ""}`.trim();
}

function setList(container, items, renderItem, emptyText) {
  if (!container) {
    return;
  }

  container.innerHTML = "";

  if (!items.length) {
    const empty = document.createElement("div");
    empty.className = "record-item";
    empty.textContent = emptyText;
    container.appendChild(empty);
    return;
  }

  items.forEach((item) => {
    container.appendChild(renderItem(item));
  });
}

function createRecordItem(title, subtitle, detail) {
  const article = document.createElement("article");
  article.className = "record-item";

  const strong = document.createElement("strong");
  strong.textContent = title;
  article.appendChild(strong);

  if (subtitle) {
    const span = document.createElement("span");
    span.textContent = subtitle;
    article.appendChild(span);
  }

  if (detail) {
    const small = document.createElement("span");
    small.textContent = detail;
    article.appendChild(small);
  }

  return article;
}

function fillSelect(select, options, placeholder) {
  if (!select) {
    return;
  }

  select.innerHTML = "";

  if (placeholder) {
    const option = document.createElement("option");
    option.value = "";
    option.textContent = placeholder;
    select.appendChild(option);
  }

  options.forEach((optionData) => {
    const option = document.createElement("option");
    option.value = String(optionData.value);
    option.textContent = optionData.label;
    select.appendChild(option);
  });
}

function updatePolicyFormFromItem(item) {
  editingPolicyId = item.id ?? null;

  if (els.policyDepartmentSelect) {
    els.policyDepartmentSelect.value = String(item.department_id ?? "");
  }
  if (els.policyRegionSelect) {
    els.policyRegionSelect.value = item.region_id ? String(item.region_id) : "";
  }

  const checkedBoxes = new Set([item.alert_type]);
  document.querySelectorAll('input[type="checkbox"][value]').forEach((checkbox) => {
    checkbox.checked = checkedBoxes.has(checkbox.value);
  });
}

function updateManualEntryFormFromItem(item) {
  editingManualEntryId = item.id ?? null;

  if (els.manualDepartmentSelect) {
    els.manualDepartmentSelect.value = String(item.department_id ?? "");
  }
  if (els.manualNameInput) {
    els.manualNameInput.value = item.name ?? "";
  }
  if (els.manualPositionInput) {
    els.manualPositionInput.value = item.position ?? "";
  }
  if (els.manualPhoneInput) {
    els.manualPhoneInput.value = item.phone ?? "";
  }
  if (els.manualEmailInput) {
    els.manualEmailInput.value = item.email ?? "";
  }
  if (els.manualDutyOrderInput) {
    els.manualDutyOrderInput.value = String(item.duty_order ?? 1);
  }
}

function syncBackendUrlUI() {
  if (els.backendUrlInput) {
    els.backendUrlInput.value = API_BASE_URL;
  }
  if (els.backendUrlLabel) {
    els.backendUrlLabel.textContent = API_BASE_URL;
  }
}

function setConnectionStatus(message) {
  if (els.connectionStatusLabel) {
    els.connectionStatusLabel.textContent = message;
  }
}

function saveBackendUrl() {
  const nextUrl = els.backendUrlInput?.value?.trim();
  API_BASE_URL = nextUrl ? nextUrl.replace(/\/+$/, "") : DEFAULT_API_BASE_URL;
  localStorage.setItem(API_BASE_URL_KEY, API_BASE_URL);
  syncBackendUrlUI();
}

async function apiFetch(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers ?? {}),
    },
    ...options,
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`API 요청 실패: ${response.status} ${errorText}`);
  }

  return response.json();
}

async function loadAll() {
  const [regions, departments, employees, policies, weatherAlerts, notificationLogs, importJobs, manualEntries] = await Promise.all([
    apiFetch("/api/regions"),
    apiFetch("/api/departments"),
    apiFetch("/api/employees"),
    apiFetch("/api/policies"),
    apiFetch("/api/weather/alerts"),
    apiFetch("/api/alerts"),
    apiFetch("/api/imports/jobs"),
    apiFetch("/api/manual-entries"),
  ]);

  state.regions = regions.items ?? [];
  state.departments = departments.items ?? [];
  state.employees = employees.items ?? [];
  state.policies = policies.items ?? [];
  state.weatherAlerts = weatherAlerts.items ?? [];
  state.notificationLogs = notificationLogs.items ?? [];
  state.importJobs = importJobs.items ?? [];
  state.manualEntries = manualEntries.items ?? [];
  setConnectionStatus("연결 성공");

  if (els.regionCount) {
    els.regionCount.textContent = String(state.regions.length);
  }

  if (els.departmentCount) {
    els.departmentCount.textContent = String(state.departments.length);
  }

  if (els.employeeCount) {
    els.employeeCount.textContent = String(state.employees.length);
  }

  const selectedRegion = state.regions[0];
  const currentAlert = state.weatherAlerts[0];
  const nextDuty = state.employees[0];

  if (els.selectedRegionLabel) {
    els.selectedRegionLabel.textContent = selectedRegion ? formatRegionLabel(selectedRegion) : "지역 없음";
  }

  if (els.currentAlertLabel) {
    els.currentAlertLabel.textContent = currentAlert
      ? `${currentAlert.alert_type ?? "특보"} ${currentAlert.severity ?? ""}`.trim()
      : "특보 없음";
  }

  if (els.nextDutyLabel) {
    els.nextDutyLabel.textContent = nextDuty
      ? `${nextDuty.department_name ?? "부서"} ${nextDuty.name ?? "직원"}`
      : "대기 중";
  }

  setList(
    els.alertList,
    state.weatherAlerts,
    (item) =>
      createRecordItem(
        `${item.alert_type ?? "특보"} · ${item.severity ?? "정보"}`,
        `${item.status ?? "상태"} / ${item.collected_at ?? "수집 시각 없음"}`,
        item.issued_at ? `발효: ${item.issued_at}` : null,
      ),
    "저장된 특보가 없습니다.",
  );

  setList(
    els.dutyList,
    state.employees,
    (item) =>
      createRecordItem(
        `${item.duty_order ?? "-"}순번 · ${item.name ?? "직원"}`,
        item.department_name ? `부서: ${item.department_name}` : `부서 ID: ${item.department_id ?? "-"}`,
        [item.position, item.phone].filter(Boolean).join(" / ") || "연락처 정보 없음",
      ),
    "비상근무 대상이 없습니다.",
  );

  setList(
    els.regionList,
    state.regions,
    (item) =>
      createRecordItem(
        formatRegionLabel(item),
        `행정코드: ${item.admin_code ?? "-"}`,
        item.is_active ? "활성 지역" : "비활성 지역",
      ),
    "등록된 지역이 없습니다.",
  );

  setList(
    els.employeeList,
    state.employees,
    (item) =>
      createRecordItem(
        `${item.name ?? "직원"} · ${item.department_name ?? "부서 없음"}`,
        `순번 ${item.duty_order ?? "-"} / ${item.status ?? "-"}`,
        [item.email, item.memo].filter(Boolean).join(" / ") || "추가 정보 없음",
      ),
    "등록된 직원이 없습니다.",
  );

  setList(
    document.getElementById("manualEntryList"),
    state.manualEntries,
    (item) => {
      const article = createRecordItem(
        `${item.name ?? "수기 입력"} · ${item.department_name ?? "부서 없음"}`,
        `순번 ${item.duty_order ?? "-"} / ${item.status ?? "-"}`,
        [item.position, item.phone, item.email].filter(Boolean).join(" / ") || "추가 정보 없음",
      );
      const button = document.createElement("button");
      button.type = "button";
      button.textContent = "수정";
      button.dataset.manualEntryId = String(item.id);
      button.dataset.action = "edit-manual-entry";
      article.appendChild(button);
      return article;
    },
    "수기 입력 데이터가 없습니다.",
  );

  setList(
    els.policyList,
    state.policies,
    (item) =>
      (() => {
        const article = createRecordItem(
          `${item.department_name ?? "부서"} · ${item.alert_type ?? "특보"}`,
          item.region_sido_name ? `${item.region_sido_name} ${item.region_sigungu_name ?? ""}`.trim() : "전 지역",
          item.is_enabled ? "활성 정책" : "비활성 정책",
        );
        const button = document.createElement("button");
        button.type = "button";
        button.textContent = "수정";
        button.dataset.policyId = String(item.id);
        button.dataset.action = "edit-policy";
        article.appendChild(button);
        return article;
      })(),
    "저장된 정책이 없습니다.",
  );

  setList(
    els.historyList,
    state.notificationLogs,
    (item) =>
      createRecordItem(
        `${item.alert_type ?? "특보"} · ${item.notify_kind ?? "알림"}`,
        `${item.channel ?? "-"} / ${item.status ?? "-"}`,
        item.created_at ?? "이력 없음",
      ),
    "발송 이력이 없습니다.",
  );

  setList(
    els.importJobList,
    state.importJobs,
    (item) =>
      createRecordItem(
        `${item.file_name ?? "파일"} · ${item.file_format ?? "-"}`,
        `${item.status ?? "-"} / 성공 ${item.success_count ?? 0}건 / 실패 ${item.failure_count ?? 0}건`,
        item.failure_reason || item.finished_at || "처리 정보 없음",
      ),
    "업로드 이력이 없습니다.",
  );

  fillSelect(
    els.employeeDepartmentSelect,
    state.departments.map((department) => ({
      value: department.id,
      label: department.name ?? `부서 ${department.id}`,
    })),
    "부서 선택",
  );

  fillSelect(
    els.manualDepartmentSelect,
    state.departments.map((department) => ({
      value: department.id,
      label: department.name ?? `부서 ${department.id}`,
    })),
    "부서 선택",
  );

  fillSelect(
    els.policyDepartmentSelect,
    state.departments.map((department) => ({
      value: department.id,
      label: department.name ?? `부서 ${department.id}`,
    })),
    "부서 선택",
  );

  fillSelect(
    els.policyRegionSelect,
    [
      { value: "", label: "전체 지역" },
      ...state.regions.map((region) => ({
        value: region.id,
        label: formatRegionLabel(region),
      })),
    ],
    null,
  );

  fillSelect(
    els.alertRegionSelect,
    [
      { value: "", label: "전체 지역" },
      ...state.regions.map((region) => ({
        value: region.id,
        label: formatRegionLabel(region),
      })),
    ],
    null,
  );
}

async function handleRegionSubmit(event) {
  event.preventDefault();

  await apiFetch("/api/regions", {
    method: "POST",
    body: JSON.stringify({
      sido_name: els.regionSidoInput?.value?.trim() || "신규 시/도",
      sigungu_name: els.regionSigunguInput?.value?.trim() || "전체",
      admin_code: els.regionAdminCodeInput?.value?.trim() || null,
    }),
  });

  event.target.reset();
  await loadAll();
}

async function handleEmployeeSubmit(event) {
  event.preventDefault();

  await apiFetch("/api/employees", {
    method: "POST",
    body: JSON.stringify({
      department_id: els.employeeDepartmentSelect?.value || null,
      name: els.employeeNameInput?.value?.trim() || "신규 직원",
      position: els.employeePositionInput?.value?.trim() || null,
      phone: els.employeePhoneInput?.value?.trim() || null,
      email: els.employeeEmailInput?.value?.trim() || null,
      duty_order: Number(els.employeeDutyOrderInput?.value || 1),
      memo: els.employeeMemoInput?.value?.trim() || null,
    }),
  });

  event.target.reset();
  if (els.employeeDutyOrderInput) {
    els.employeeDutyOrderInput.value = "1";
  }
  await loadAll();
}

async function handleManualEntrySubmit(event) {
  event.preventDefault();

  const payload = {
    department_id: els.manualDepartmentSelect?.value || null,
    name: els.manualNameInput?.value?.trim() || "신규 입력",
    position: els.manualPositionInput?.value?.trim() || null,
    phone: els.manualPhoneInput?.value?.trim() || null,
    email: els.manualEmailInput?.value?.trim() || null,
    duty_order: Number(els.manualDutyOrderInput?.value || 1),
  };

  if (editingManualEntryId) {
    await apiFetch(`/api/manual-entries/${editingManualEntryId}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    });
    editingManualEntryId = null;
  } else {
    await apiFetch("/api/manual-entries", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  event.target.reset();
  if (els.manualDutyOrderInput) {
    els.manualDutyOrderInput.value = "1";
  }
  await loadAll();
}

async function handlePolicySubmit(event) {
  event.preventDefault();

  const alertTypes = Array.from(document.querySelectorAll('input[type="checkbox"][value]'))
    .filter((checkbox) => checkbox.checked)
    .map((checkbox) => checkbox.value);

  const payload = {
    department_id: Number(els.policyDepartmentSelect?.value || 0),
    region_id: els.policyRegionSelect?.value ? Number(els.policyRegionSelect.value) : null,
    alert_types: alertTypes,
    is_enabled: true,
  };

  if (editingPolicyId) {
    await apiFetch(`/api/policies/${editingPolicyId}`, {
      method: "PUT",
      body: JSON.stringify({
        department_id: payload.department_id,
        region_id: payload.region_id,
        alert_type: alertTypes[0] || "호우주의보",
        is_enabled: true,
      }),
    });
    editingPolicyId = null;
  } else {
    await apiFetch("/api/policies", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  await loadAll();
}

async function handleAlertSubmit(event) {
  event.preventDefault();

  await apiFetch("/api/alerts", {
    method: "POST",
    body: JSON.stringify({
      region_id: els.alertRegionSelect?.value ? Number(els.alertRegionSelect.value) : null,
      alert_type: els.alertTypeInput?.value?.trim() || "호우주의보",
      severity: els.alertSeverityInput?.value?.trim() || "주의보",
      notify_kind: els.alertNotifyKindSelect?.value || "immediate",
      channel: els.alertChannelSelect?.value || "sms",
      status: els.alertStatusSelect?.value || "pending",
    }),
  });

  await loadAll();
}

async function handleImportSubmit(event) {
  event.preventDefault();

  const file = els.importFileInput?.files?.[0];
  if (!file) {
    return;
  }

  const contentBase64 = await new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result ?? ""));
    reader.onerror = () => reject(reader.error);
    reader.readAsDataURL(file);
  });

  await apiFetch("/api/imports/upload", {
    method: "POST",
    body: JSON.stringify({
      file_name: file.name,
      file_format: file.name.split(".").pop()?.toLowerCase() ?? "",
      content_base64: contentBase64,
    }),
  });

  event.target.reset();
  await loadAll();
}

function bindEvents() {
  els.refreshButton?.addEventListener("click", loadAll);
  els.summaryRefreshButton?.addEventListener("click", loadAll);
  els.alertReloadButton?.addEventListener("click", loadAll);
  els.saveBackendUrlButton?.addEventListener("click", () => {
    saveBackendUrl();
    loadAll().catch((error) => {
      console.error(error);
      setConnectionStatus("연결 실패");
    });
  });
  els.regionForm?.addEventListener("submit", handleRegionSubmit);
  els.employeeForm?.addEventListener("submit", handleEmployeeSubmit);
  els.manualEntryForm?.addEventListener("submit", handleManualEntrySubmit);
  els.policyForm?.addEventListener("submit", handlePolicySubmit);
  els.alertForm?.addEventListener("submit", handleAlertSubmit);
  els.importForm?.addEventListener("submit", handleImportSubmit);
  els.policyList?.addEventListener("click", (event) => {
    const target = event.target;
    if (!(target instanceof HTMLButtonElement)) {
      return;
    }

    if (target.dataset.action === "edit-policy") {
      const policyId = Number(target.dataset.policyId);
      const policy = state.policies.find((item) => item.id === policyId);
      if (policy) {
        updatePolicyFormFromItem(policy);
      }
    }
  });
  document.getElementById("manualEntryList")?.addEventListener("click", (event) => {
    const target = event.target;
    if (!(target instanceof HTMLButtonElement)) {
      return;
    }

    if (target.dataset.action === "edit-manual-entry") {
      const manualEntryId = Number(target.dataset.manualEntryId);
      const manualEntry = state.manualEntries.find((item) => item.id === manualEntryId);
      if (manualEntry) {
        updateManualEntryFormFromItem(manualEntry);
      }
    }
  });
}

bindEvents();
syncBackendUrlUI();
loadAll().catch((error) => {
  console.error(error);
  setConnectionStatus("연결 실패");
  if (els.alertList) {
    els.alertList.innerHTML = `<div class="record-item">데이터를 불러오지 못했습니다.</div>`;
  }
});
