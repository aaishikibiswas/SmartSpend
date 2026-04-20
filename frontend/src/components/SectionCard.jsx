export default function SectionCard({ title, subtitle, children, className = "" }) {
  return (
    <section className={`section-card ${className}`.trim()}>
      {(title || subtitle) && (
        <div className="section-card__head">
          {title ? <h3>{title}</h3> : null}
          {subtitle ? <p>{subtitle}</p> : null}
        </div>
      )}
      {children}
    </section>
  );
}
