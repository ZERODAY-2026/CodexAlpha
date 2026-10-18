// Small reusable label. `tone` maps to a colour pair in App.css.
export default function StatusPill({ tone = 'neutral', icon: Icon, children, title }) {
  return (
    <span className={`pill pill--${tone}`} title={title}>
      {Icon && <Icon size={14} aria-hidden="true" />}
      {children}
    </span>
  );
}
