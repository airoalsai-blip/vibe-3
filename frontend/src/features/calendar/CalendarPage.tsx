import { FormEvent, useEffect, useMemo, useState } from "react";
import { api, type Schedule, type ScheduleInput, type TeamMember, type TeamMemberInput } from "../../lib/api";

type ViewMode = "week" | "month";

const scheduleTypes = ["근무", "휴가", "출장", "교육", "기타"];

const emptyMemberForm: TeamMemberInput = {
  name: "",
  email: "",
  department: "",
  position: "",
  phone: "",
  role: "member",
};

const emptyScheduleForm: ScheduleInput = {
  owner_id: 0,
  type: "근무",
  title: "",
  description: "",
  location: "",
  start_at: "",
  end_at: "",
};

function toDateInput(date: Date): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function addDays(date: Date, days: number): Date {
  const next = new Date(date);
  next.setDate(next.getDate() + days);
  return next;
}

function startOfWeek(date: Date): Date {
  const next = new Date(date);
  const day = next.getDay();
  const diff = day === 0 ? -6 : 1 - day;
  next.setDate(next.getDate() + diff);
  next.setHours(0, 0, 0, 0);
  return next;
}

function startOfMonth(date: Date): Date {
  return new Date(date.getFullYear(), date.getMonth(), 1);
}

function endOfMonth(date: Date): Date {
  return new Date(date.getFullYear(), date.getMonth() + 1, 0);
}

function formatDateTime(value: string): string {
  return new Intl.DateTimeFormat("ko-KR", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

function formatTime(value: string): string {
  return new Intl.DateTimeFormat("ko-KR", {
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

function dateKey(value: string): string {
  return value.slice(0, 10);
}

function compactInput<T extends Record<string, unknown>>(input: T): T {
  return Object.fromEntries(
    Object.entries(input).map(([key, value]) => [key, typeof value === "string" ? value.trim() : value]),
  ) as T;
}

export function CalendarPage() {
  const [adminPin, setAdminPin] = useState("1234");
  const [viewMode, setViewMode] = useState<ViewMode>("week");
  const [anchorDate, setAnchorDate] = useState(toDateInput(new Date()));
  const [members, setMembers] = useState<TeamMember[]>([]);
  const [schedules, setSchedules] = useState<Schedule[]>([]);
  const [memberForm, setMemberForm] = useState<TeamMemberInput>(emptyMemberForm);
  const [scheduleForm, setScheduleForm] = useState<ScheduleInput>(emptyScheduleForm);
  const [editingMemberId, setEditingMemberId] = useState<number | null>(null);
  const [editingScheduleId, setEditingScheduleId] = useState<number | null>(null);
  const [selectedDate, setSelectedDate] = useState(toDateInput(new Date()));
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const dateRange = useMemo(() => {
    const anchor = new Date(`${anchorDate}T00:00:00`);
    if (viewMode === "week") {
      const from = startOfWeek(anchor);
      return { from: toDateInput(from), to: toDateInput(addDays(from, 6)) };
    }
    return { from: toDateInput(startOfMonth(anchor)), to: toDateInput(endOfMonth(anchor)) };
  }, [anchorDate, viewMode]);

  async function loadData() {
    setIsLoading(true);
    setError(null);
    try {
      const [memberResult, scheduleResult] = await Promise.all([
        api.teamMembers(),
        api.schedules(dateRange.from, dateRange.to),
      ]);
      setMembers(memberResult.items);
      setSchedules(scheduleResult.items);
    } catch (currentError) {
      setError(currentError instanceof Error ? currentError.message : "데이터를 불러오지 못했습니다.");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, [dateRange.from, dateRange.to]);

  const weekDays = useMemo(() => {
    const from = new Date(`${dateRange.from}T00:00:00`);
    return Array.from({ length: 7 }, (_, index) => toDateInput(addDays(from, index)));
  }, [dateRange.from]);

  const monthDays = useMemo(() => {
    const monthStart = startOfMonth(new Date(`${anchorDate}T00:00:00`));
    const gridStart = startOfWeek(monthStart);
    return Array.from({ length: 42 }, (_, index) => toDateInput(addDays(gridStart, index)));
  }, [anchorDate]);

  const schedulesByDate = useMemo(() => {
    return schedules.reduce<Record<string, Schedule[]>>((accumulator, schedule) => {
      const key = dateKey(schedule.start_at);
      accumulator[key] = [...(accumulator[key] ?? []), schedule];
      return accumulator;
    }, {});
  }, [schedules]);

  const weeklySchedules = useMemo(() => {
    return schedules.filter((schedule) => weekDays.includes(dateKey(schedule.start_at)));
  }, [schedules, weekDays]);

  const selectedDateSchedules = schedulesByDate[selectedDate] ?? [];

  async function handleMemberSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    try {
      if (editingMemberId) {
        await api.updateTeamMember(editingMemberId, compactInput(memberForm), adminPin);
      } else {
        await api.createTeamMember(compactInput(memberForm), adminPin);
      }
      setMemberForm(emptyMemberForm);
      setEditingMemberId(null);
      await loadData();
    } catch (currentError) {
      setError(currentError instanceof Error ? currentError.message : "팀원 저장에 실패했습니다.");
    }
  }

  async function handleScheduleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    try {
      if (editingScheduleId) {
        await api.updateSchedule(editingScheduleId, compactInput(scheduleForm), adminPin);
      } else {
        await api.createSchedule(compactInput(scheduleForm), adminPin);
      }
      setScheduleForm({ ...emptyScheduleForm, owner_id: members[0]?.id ?? 0 });
      setEditingScheduleId(null);
      await loadData();
    } catch (currentError) {
      setError(currentError instanceof Error ? currentError.message : "일정 저장에 실패했습니다.");
    }
  }

  function editMember(member: TeamMember) {
    setEditingMemberId(member.id);
    setMemberForm({
      name: member.name,
      email: member.email ?? "",
      department: member.department ?? "",
      position: member.position ?? "",
      phone: member.phone ?? "",
      role: member.role,
    });
  }

  function editSchedule(schedule: Schedule) {
    setEditingScheduleId(schedule.id);
    setScheduleForm({
      owner_id: schedule.owner_id,
      type: schedule.type,
      title: schedule.title,
      description: schedule.description ?? "",
      location: schedule.location ?? "",
      start_at: schedule.start_at.slice(0, 16),
      end_at: schedule.end_at.slice(0, 16),
    });
  }

  async function deleteMember(id: number) {
    setError(null);
    try {
      await api.deleteTeamMember(id, adminPin);
      await loadData();
    } catch (currentError) {
      setError(currentError instanceof Error ? currentError.message : "팀원 삭제에 실패했습니다.");
    }
  }

  async function deleteSchedule(id: number) {
    setError(null);
    try {
      await api.deleteSchedule(id, adminPin);
      await loadData();
    } catch (currentError) {
      setError(currentError instanceof Error ? currentError.message : "일정 삭제에 실패했습니다.");
    }
  }

  useEffect(() => {
    if (members.length > 0 && scheduleForm.owner_id === 0) {
      setScheduleForm((current) => ({ ...current, owner_id: members[0].id }));
    }
  }, [members, scheduleForm.owner_id]);

  return (
    <section className="workspace-section calendar-workspace">
      <div className="section-header">
        <div>
          <h2>팀원 일정 관리</h2>
          <p>팀원을 등록하고 휴가, 근무, 출장 일정을 주간 표와 월간 캘린더로 확인합니다.</p>
        </div>
        <label className="pin-field">
          관리자 PIN
          <input value={adminPin} onChange={(event) => setAdminPin(event.target.value)} type="password" />
        </label>
      </div>

      {error ? <div className="inline-alert">{error}</div> : null}

      <div className="calendar-layout">
        <aside className="calendar-sidebar">
          <form className="stack-form" onSubmit={handleMemberSubmit}>
            <h3>{editingMemberId ? "팀원 수정" : "팀원 등록"}</h3>
            <label>
              이름
              <input
                required
                value={memberForm.name}
                onChange={(event) => setMemberForm({ ...memberForm, name: event.target.value })}
              />
            </label>
            <label>
              이메일
              <input
                type="email"
                value={memberForm.email}
                onChange={(event) => setMemberForm({ ...memberForm, email: event.target.value })}
              />
            </label>
            <label>
              부서
              <input
                value={memberForm.department}
                onChange={(event) => setMemberForm({ ...memberForm, department: event.target.value })}
              />
            </label>
            <label>
              직위
              <input
                value={memberForm.position}
                onChange={(event) => setMemberForm({ ...memberForm, position: event.target.value })}
              />
            </label>
            <label>
              연락처
              <input
                value={memberForm.phone}
                onChange={(event) => setMemberForm({ ...memberForm, phone: event.target.value })}
              />
            </label>
            <div className="button-row">
              <button type="submit">{editingMemberId ? "수정" : "등록"}</button>
              {editingMemberId ? (
                <button
                  type="button"
                  onClick={() => {
                    setEditingMemberId(null);
                    setMemberForm(emptyMemberForm);
                  }}
                >
                  취소
                </button>
              ) : null}
            </div>
          </form>

          <div className="member-list">
            <h3>팀원 목록</h3>
            {members.length === 0 ? <p>등록된 팀원이 없습니다.</p> : null}
            {members.map((member) => (
              <article className="list-card" key={member.id}>
                <strong>{member.name}</strong>
                <span>{[member.department, member.position].filter(Boolean).join(" / ") || "소속 정보 없음"}</span>
                <div className="button-row">
                  <button type="button" onClick={() => editMember(member)}>
                    수정
                  </button>
                  <button type="button" onClick={() => deleteMember(member.id)}>
                    삭제
                  </button>
                </div>
              </article>
            ))}
          </div>
        </aside>

        <div className="calendar-main">
          <form className="schedule-form" onSubmit={handleScheduleSubmit}>
            <h3>{editingScheduleId ? "일정 수정" : "일정 등록"}</h3>
            <div className="form-grid">
              <label>
                팀원
                <select
                  required
                  value={scheduleForm.owner_id}
                  onChange={(event) => setScheduleForm({ ...scheduleForm, owner_id: Number(event.target.value) })}
                >
                  <option value={0}>팀원 선택</option>
                  {members.map((member) => (
                    <option key={member.id} value={member.id}>
                      {member.name}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                유형
                <select
                  value={scheduleForm.type}
                  onChange={(event) => setScheduleForm({ ...scheduleForm, type: event.target.value })}
                >
                  {scheduleTypes.map((type) => (
                    <option key={type}>{type}</option>
                  ))}
                </select>
              </label>
              <label>
                제목
                <input
                  required
                  value={scheduleForm.title}
                  onChange={(event) => setScheduleForm({ ...scheduleForm, title: event.target.value })}
                />
              </label>
              <label>
                장소
                <input
                  value={scheduleForm.location}
                  onChange={(event) => setScheduleForm({ ...scheduleForm, location: event.target.value })}
                />
              </label>
              <label>
                시작
                <input
                  required
                  type="datetime-local"
                  value={scheduleForm.start_at}
                  onChange={(event) => setScheduleForm({ ...scheduleForm, start_at: event.target.value })}
                />
              </label>
              <label>
                종료
                <input
                  required
                  type="datetime-local"
                  value={scheduleForm.end_at}
                  onChange={(event) => setScheduleForm({ ...scheduleForm, end_at: event.target.value })}
                />
              </label>
              <label className="wide-field">
                설명
                <textarea
                  value={scheduleForm.description}
                  onChange={(event) => setScheduleForm({ ...scheduleForm, description: event.target.value })}
                />
              </label>
            </div>
            <div className="button-row">
              <button type="submit">{editingScheduleId ? "수정" : "등록"}</button>
              {editingScheduleId ? (
                <button
                  type="button"
                  onClick={() => {
                    setEditingScheduleId(null);
                    setScheduleForm({ ...emptyScheduleForm, owner_id: members[0]?.id ?? 0 });
                  }}
                >
                  취소
                </button>
              ) : null}
            </div>
          </form>

          <div className="calendar-toolbar">
            <div className="segmented-control">
              <button className={viewMode === "week" ? "is-active" : ""} onClick={() => setViewMode("week")} type="button">
                주간 보기
              </button>
              <button className={viewMode === "month" ? "is-active" : ""} onClick={() => setViewMode("month")} type="button">
                월간 보기
              </button>
            </div>
            <input type="date" value={anchorDate} onChange={(event) => setAnchorDate(event.target.value)} />
          </div>

          {isLoading ? <p>일정 데이터를 불러오는 중입니다.</p> : null}

          {viewMode === "week" ? (
            <div className="table-wrap">
              <table className="schedule-table">
                <thead>
                  <tr>
                    <th>일자</th>
                    <th>시간</th>
                    <th>팀원</th>
                    <th>유형</th>
                    <th>일정</th>
                    <th>장소</th>
                    <th>관리</th>
                  </tr>
                </thead>
                <tbody>
                  {weeklySchedules.length === 0 ? (
                    <tr>
                      <td colSpan={7}>이번 주 등록된 일정이 없습니다.</td>
                    </tr>
                  ) : (
                    weeklySchedules.map((schedule) => (
                      <tr key={schedule.id}>
                        <td>{dateKey(schedule.start_at)}</td>
                        <td>
                          {formatTime(schedule.start_at)} - {formatTime(schedule.end_at)}
                        </td>
                        <td>{schedule.owner_name ?? "미지정"}</td>
                        <td>{schedule.type}</td>
                        <td>{schedule.title}</td>
                        <td>{schedule.location ?? "-"}</td>
                        <td>
                          <div className="table-actions">
                            <button type="button" onClick={() => editSchedule(schedule)}>
                              수정
                            </button>
                            <button type="button" onClick={() => deleteSchedule(schedule.id)}>
                              삭제
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="month-view">
              <div className="month-grid month-weekdays">
                {["월", "화", "수", "목", "금", "토", "일"].map((day) => (
                  <strong key={day}>{day}</strong>
                ))}
              </div>
              <div className="month-grid">
                {monthDays.map((day) => {
                  const daySchedules = schedulesByDate[day] ?? [];
                  const isOutside = new Date(`${day}T00:00:00`).getMonth() !== new Date(`${anchorDate}T00:00:00`).getMonth();
                  return (
                    <button
                      className={`calendar-day${isOutside ? " is-muted" : ""}${selectedDate === day ? " is-selected" : ""}`}
                      key={day}
                      onClick={() => setSelectedDate(day)}
                      type="button"
                    >
                      <span>{Number(day.slice(8, 10))}</span>
                      {daySchedules.slice(0, 3).map((schedule) => (
                        <small key={schedule.id}>
                          {schedule.type} · {schedule.owner_name ?? schedule.title}
                        </small>
                      ))}
                      {daySchedules.length > 3 ? <em>+{daySchedules.length - 3}</em> : null}
                    </button>
                  );
                })}
              </div>
              <div className="selected-day-panel">
                <h3>{selectedDate} 일정</h3>
                {selectedDateSchedules.length === 0 ? <p>선택한 날짜에 등록된 일정이 없습니다.</p> : null}
                {selectedDateSchedules.map((schedule) => (
                  <article className="list-card" key={schedule.id}>
                    <strong>{schedule.title}</strong>
                    <span>
                      {schedule.owner_name ?? "미지정"} / {schedule.type} / {formatDateTime(schedule.start_at)}
                    </span>
                    <div className="button-row">
                      <button type="button" onClick={() => editSchedule(schedule)}>
                        수정
                      </button>
                      <button type="button" onClick={() => deleteSchedule(schedule.id)}>
                        삭제
                      </button>
                    </div>
                  </article>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
