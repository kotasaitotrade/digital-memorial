import api from "./api";

export async function autoCheck(task_key: string): Promise<void> {
  try {
    await api.post("/checklist/toggle", { task_key, is_completed: true });
  } catch {
    // silent — checklist auto-check is non-critical
  }
}
