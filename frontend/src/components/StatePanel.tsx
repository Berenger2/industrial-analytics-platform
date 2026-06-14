type StatePanelProps = {
  title: string;
  message: string;
  type?: "empty" | "error";
};

export function StatePanel({
  title,
  message,
  type = "empty",
}: StatePanelProps) {
  return (
    <div className={`state-panel state-panel--${type}`} role="status">
      <strong>{title}</strong>
      <span>{message}</span>
    </div>
  );
}
