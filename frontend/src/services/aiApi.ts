import api from './api';

/** 冲突事件结构 */
export interface ConflictEvent {
  id: number;
  title: string;
  start_time: string;
  end_time: string;
  color?: string;
}

/** 空闲时段结构 */
export interface FreeSlot {
  start: string;
  end: string;
}

export const aiApi = {
  /** 检测与指定时间段冲突的事件 */
  detectConflicts: (startTime: string, endTime: string) =>
    api.post<{ code: number; data: { conflicts: ConflictEvent[] }; message: string }>(
      `/ai/detect-conflicts?start_time=${encodeURIComponent(startTime)}&end_time=${encodeURIComponent(endTime)}`,
    ),

  /** 推荐指定日期的空闲时段 */
  recommendSlot: (targetDate: string, durationMinutes = 60) =>
    api.post<{ code: number; data: { slots: FreeSlot[] }; message: string }>(
      `/ai/recommend-slot?target_date=${targetDate}&duration_minutes=${durationMinutes}`,
    ),

  /** 获取每日日程摘要 */
  getDailyBriefing: (period: 'morning' | 'evening' = 'morning') =>
    api.get<{ code: number; data: { briefing: string }; message: string }>(
      `/ai/daily-briefing?period=${period}`,
    ),
};
