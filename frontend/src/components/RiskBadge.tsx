import { riskColor, riskLabel } from '../utils/formatters';

interface Props {
  score: number;
}

export function RiskBadge({ score }: Props) {
  const color = riskColor(score);
  const label = riskLabel(score);

  return (
    <span
      className="text-xs px-2 py-0.5 rounded-full font-medium"
      style={{
        backgroundColor: `${color}20`,
        color,
      }}
    >
      {label} ({score.toFixed(1)})
    </span>
  );
}
