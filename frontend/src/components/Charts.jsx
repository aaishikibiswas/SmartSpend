function valueMax(data) {
  return Math.max(...data.map((item) => item.value), 1);
}

function formatCurrency(value) {
  return `Rs. ${Number(value || 0).toLocaleString()}`;
}

export function BarChart({ data }) {
  const max = valueMax(data);
  return (
    <div className="chart chart--bars">
      {data.map((item) => (
        <div key={item.label} className="bar-row">
          <div className="bar-row__meta">
            <span>{item.label}</span>
            <strong>{formatCurrency(item.value)}</strong>
          </div>
          <div className="bar-row__track">
            <div className="bar-row__fill" style={{ width: `${(item.value / max) * 100}%` }} />
          </div>
        </div>
      ))}
    </div>
  );
}

export function DonutChart({ data }) {
  const colors = ["#00cc99", "#ff7a66", "#66c2ff", "#ffd166"];
  const total = data.reduce((sum, item) => sum + item.value, 0) || 1;
  let offset = 0;
  const gradient = data
    .map((item, index) => {
      const start = (offset / total) * 100;
      offset += item.value;
      const end = (offset / total) * 100;
      return `${colors[index % colors.length]} ${start}% ${end}%`;
    })
    .join(", ");

  return (
    <div className="chart chart--donut">
      <div className="donut" style={{ background: `conic-gradient(${gradient})` }}>
        <div className="donut__inner">
          <strong>{formatCurrency(total)}</strong>
          <span>Total</span>
        </div>
      </div>
      <div className="legend">
        {data.map((item, index) => (
          <div key={item.label} className="legend__row">
            <span className="legend__swatch" style={{ backgroundColor: colors[index % colors.length] }} />
            <span>{item.label}</span>
            <strong>{formatCurrency(item.value)}</strong>
          </div>
        ))}
      </div>
    </div>
  );
}

export function LineChart({ data }) {
  if (!data.length) return null;

  const width = 600;
  const height = 220;
  const max = valueMax(data);
  const step = data.length === 1 ? width : width / (data.length - 1);
  const points = data
    .map((item, index) => {
      const x = index * step;
      const y = height - (item.value / max) * (height - 30) - 10;
      return `${x},${y}`;
    })
    .join(" ");

  return (
    <div className="chart chart--line">
      <svg viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none">
        <polyline fill="none" stroke="#00cc99" strokeWidth="4" points={points} />
        {data.map((item, index) => {
          const x = index * step;
          const y = height - (item.value / max) * (height - 30) - 10;
          return <circle key={item.label} cx={x} cy={y} r="5" fill="#f6f7ef" stroke="#00cc99" strokeWidth="2" />;
        })}
      </svg>
      <div className="line-labels">
        {data.slice(-6).map((item) => (
          <span key={item.label}>{item.label}</span>
        ))}
      </div>
    </div>
  );
}
