export function scoreBand(value: number): "success" | "brand" | "warning" {
  if (value >= 0.8) {
    return "success";
  }
  if (value >= 0.6) {
    return "brand";
  }
  return "warning";
}
