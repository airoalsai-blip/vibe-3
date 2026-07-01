export type HealthStatus = {
  status: string;
  service: string;
  version: string;
};

export type DbHealthStatus = {
  status: string;
  database: string;
  checked_at: string;
  tables: string[];
};

async function request<T>(path: string): Promise<T> {
  const response = await fetch(path, {
    headers: {
      Accept: "application/json",
    },
  });

  if (!response.ok) {
    throw new Error(`${response.status} ${response.statusText}`);
  }

  return response.json() as Promise<T>;
}

export const api = {
  health: () => request<HealthStatus>("/api/health"),
  dbHealth: () => request<DbHealthStatus>("/api/db/health"),
};
