interface ContextMenuPosition {
  x: number;
  y: number;
}

interface EventContextMenuProps {
  isOpen: boolean;
  position: ContextMenuPosition;
  onEdit: () => void;
  onDelete: () => void;
  onClose: () => void;
}

export default function EventContextMenu({ isOpen, position, onEdit, onDelete, onClose }: EventContextMenuProps) {
  if (!isOpen) return null;

  return (
    <>
      <div style={{ position: 'fixed', inset: 0, zIndex: 999 }} onClick={onClose} />
      <div style={{ position: 'fixed', left: position.x, top: position.y, background: 'var(--color-surface)', borderRadius: 'var(--radius-md)', boxShadow: 'var(--shadow-lg)', border: '1px solid var(--color-border)', padding: 'var(--space-1)', zIndex: 1000, minWidth: '160px' }}>
        <button onClick={onEdit} style={{ display: 'block', width: '100%', padding: 'var(--space-2) var(--space-4)', background: 'transparent', textAlign: 'left', borderRadius: 'var(--radius-sm)', fontSize: 'var(--font-size-sm)' }} onMouseEnter={(e) => (e.currentTarget.style.background = 'var(--color-surface-hover)')} onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}>编辑事件</button>
        <button onClick={onDelete} style={{ display: 'block', width: '100%', padding: 'var(--space-2) var(--space-4)', background: 'transparent', textAlign: 'left', borderRadius: 'var(--radius-sm)', fontSize: 'var(--font-size-sm)', color: 'var(--color-error)' }} onMouseEnter={(e) => (e.currentTarget.style.background = 'var(--color-surface-hover)')} onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}>删除事件</button>
      </div>
    </>
  );
}
