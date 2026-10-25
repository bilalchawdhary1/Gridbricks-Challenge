type Props = {title: string; value: string; detail?: string};

export default function MetricCard({title, value, detail}: Props) {
  return (
    <article className='metric-card'>
      <p>{title}</p>
      <h2>{value}</h2>
      {detail && <span>{detail}</span>}
    </article>
  );
}
