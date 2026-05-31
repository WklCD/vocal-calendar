import { useState, useRef } from 'react';
import { exportImportApi } from '../services/exportImportApi';

interface ExportImportMenuProps {
  onImportSuccess?: () => void;
}

export default function ExportImportMenu({ onImportSuccess }: ExportImportMenuProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [importing, setImporting] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleExport = async (format: 'ical' | 'json' | 'csv') => {
    try {
      const response = await exportImportApi.exportEvents(format);
      const blob = new Blob([response.data], {
        type: format === 'ical' ? 'text/calendar' : format === 'csv' ? 'text/csv' : 'application/json',
      });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `events.${format === 'ical' ? 'ics' : format}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      setMessage({ type: 'success', text: '导出成功！' });
      setTimeout(() => setMessage(null), 3000);
    } catch (error) {
      console.error('Export error:', error);
      setMessage({ type: 'error', text: '导出失败，请重试' });
      setTimeout(() => setMessage(null), 3000);
    }
  };

  const handleBackup = async () => {
    try {
      const response = await exportImportApi.exportBackup();
      const blob = new Blob([response.data], { type: 'application/json' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      const timestamp = new Date().toISOString().slice(0, 10);
      link.download = `vocal-calendar-backup-${timestamp}.json`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      setMessage({ type: 'success', text: '备份成功！' });
      setTimeout(() => setMessage(null), 3000);
    } catch (error) {
      console.error('Backup error:', error);
      setMessage({ type: 'error', text: '备份失败，请重试' });
      setTimeout(() => setMessage(null), 3000);
    }
  };

  const handleImport = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const format = file.name.endsWith('.ics') ? 'ical' :
                   file.name.endsWith('.json') ? 'json' :
                   file.name.endsWith('.csv') ? 'csv' : null;

    if (!format) {
      setMessage({ type: 'error', text: '不支持的文件格式' });
      setTimeout(() => setMessage(null), 3000);
      return;
    }

    setImporting(true);
    try {
      const result = await exportImportApi.importEvents(file, format);
      setMessage({
        type: 'success',
        text: `成功导入 ${result.imported_count || result.data?.imported_count || 0} 个事件`
      });
      setTimeout(() => setMessage(null), 3000);
      if (onImportSuccess) {
        onImportSuccess();
      }
    } catch (error: any) {
      console.error('Import error:', error);
      setMessage({
        type: 'error',
        text: error.response?.data?.detail || '导入失败，请检查文件格式'
      });
      setTimeout(() => setMessage(null), 3000);
    } finally {
      setImporting(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handleRestore = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    if (!file.name.endsWith('.json')) {
      setMessage({ type: 'error', text: '请选择 JSON 格式的备份文件' });
      setTimeout(() => setMessage(null), 3000);
      return;
    }

    setImporting(true);
    try {
      const result = await exportImportApi.importBackup(file);
      setMessage({
        type: 'success',
        text: `恢复成功：${result.imported_events} 个事件，${result.imported_categories} 个分类`
      });
      setTimeout(() => setMessage(null), 3000);
      if (onImportSuccess) {
        onImportSuccess();
      }
    } catch (error: any) {
      console.error('Restore error:', error);
      setMessage({
        type: 'error',
        text: error.response?.data?.detail || '恢复失败，请检查备份文件'
      });
      setTimeout(() => setMessage(null), 3000);
    } finally {
      setImporting(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  return (
    <div style={{ position: 'relative', display: 'inline-block' }}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        style={{
          padding: '8px 16px',
          background: '#f5f5f5',
          border: '1px solid #ddd',
          borderRadius: '6px',
          cursor: 'pointer',
          fontSize: '14px',
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
        }}
      >
        📥📤 导入/导出
      </button>

      {isOpen && (
        <div
          style={{
            position: 'absolute',
            top: '100%',
            right: 0,
            marginTop: '8px',
            background: 'white',
            border: '1px solid #ddd',
            borderRadius: '8px',
            boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
            minWidth: '250px',
            zIndex: 1000,
            padding: '8px 0',
          }}
        >
          <div style={{ padding: '8px 16px', borderBottom: '1px solid #eee' }}>
            <h4 style={{ margin: '0 0 8px 0', fontSize: '14px', color: '#333' }}>导出事件</h4>
            <button
              onClick={() => handleExport('ical')}
              style={menuButtonStyle}
            >
              📅 导出为 iCal (.ics)
            </button>
            <button
              onClick={() => handleExport('json')}
              style={menuButtonStyle}
            >
              📄 导出为 JSON
            </button>
            <button
              onClick={() => handleExport('csv')}
              style={menuButtonStyle}
            >
              📊 导出为 CSV
            </button>
          </div>

          <div style={{ padding: '8px 16px', borderBottom: '1px solid #eee' }}>
            <h4 style={{ margin: '0 0 8px 0', fontSize: '14px', color: '#333' }}>导入事件</h4>
            <input
              ref={fileInputRef}
              type="file"
              accept=".ics,.json,.csv"
              onChange={handleImport}
              style={{ display: 'none' }}
              id="import-events"
            />
            <button
              onClick={() => document.getElementById('import-events')?.click()}
              disabled={importing}
              style={menuButtonStyle}
            >
              {importing ? '导入中...' : '📂 导入事件文件'}
            </button>
          </div>

          <div style={{ padding: '8px 16px' }}>
            <h4 style={{ margin: '0 0 8px 0', fontSize: '14px', color: '#333' }}>数据备份</h4>
            <button
              onClick={handleBackup}
              style={menuButtonStyle}
            >
              💾 创建完整备份
            </button>
            <input
              type="file"
              accept=".json"
              onChange={handleRestore}
              style={{ display: 'none' }}
              id="restore-backup"
            />
            <button
              onClick={() => document.getElementById('restore-backup')?.click()}
              disabled={importing}
              style={menuButtonStyle}
            >
              {importing ? '恢复中...' : '🔄 从备份恢复'}
            </button>
          </div>
        </div>
      )}

      {message && (
        <div
          style={{
            position: 'fixed',
            top: '20px',
            right: '20px',
            padding: '12px 24px',
            background: message.type === 'success' ? '#4caf50' : '#f44336',
            color: 'white',
            borderRadius: '8px',
            boxShadow: '0 4px 12px rgba(0,0,0,0.2)',
            zIndex: 9999,
            fontSize: '14px',
          }}
        >
          {message.text}
        </div>
      )}
    </div>
  );
}

const menuButtonStyle: React.CSSProperties = {
  width: '100%',
  padding: '8px 12px',
  marginBottom: '4px',
  background: 'transparent',
  border: 'none',
  borderRadius: '4px',
  cursor: 'pointer',
  textAlign: 'left',
  fontSize: '14px',
  transition: 'background 0.2s',
};

export function useExportImport() {
  return { ExportImportMenu };
}
