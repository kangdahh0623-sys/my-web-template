type StatBarProps = { label: string; value: number; max: number; unit?: string };
function StatBar({ label, value, max, unit }: StatBarProps) {
  const v = Number(value) || 0;
  const m = Math.max(1, Number(max) || 1);
  const pct = Math.max(0, Math.min(100, Math.round((v / m) * 100)));
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-sm text-gray-700">
        <span>{label}</span>
        <span>{v.toFixed(1)} / {m} {unit ?? ""}</span>
      </div>
      <div className="h-2 w-full rounded bg-gray-200">
        <div className="h-2 rounded bg-blue-600" style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}
