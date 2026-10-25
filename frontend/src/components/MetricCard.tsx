type Props = {
  label: string;
  value: string;
  note?: string;
};

/** One figure in a stat strip: plain-language label, big value, short note. */
export default function MetricCard({label, value, note}: Props) {
  return (
    <div className='stat'>
      <p className='stat-label'>{label}</p>
      <p className='stat-value'>{value}</p>
      {note && <p className='stat-note'>{note}</p>}
    </div>
  );
}
