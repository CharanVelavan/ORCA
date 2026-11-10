/** Original ORCA mark: a dorsal fin and open orbital ring, drawn for small sizes. */
export function OrcaMark({ size = 30 }: { size?: number }) {
  return <svg width={size} height={size} viewBox="0 0 64 64" fill="none" aria-hidden="true" focusable="false">
    <path d="M14 21A24 24 0 0 1 53 18M56 39A24 24 0 0 1 24 55" stroke="currentColor" strokeWidth="3.5" strokeLinecap="square" />
    <path d="M8 40C14 31 23 27 30 27L33 12C38 17 40 22 40 26C48 25 54 27 57 31C53 35 48 38 42 39C34 44 25 44 19 41L9 48L12 40H8Z" fill="currentColor" />
    <path d="M23 38C30 39 37 37 43 33C38 40 29 42 23 38Z" fill="#6D001A" />
    <circle cx="45.5" cy="30" r="1.7" fill="#6D001A" />
  </svg>;
}
