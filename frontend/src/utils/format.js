export function statusText(status) {
  if (status === "mastered") return "已完成";
  if (status === "waiting_for_answer") return "等待作答";
  return "讲解中";
}

