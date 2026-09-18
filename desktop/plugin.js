/**
 * 仿生大脑 · 桌面面板
 * ====================
 * 在 Hermes 桌面显示仿生大脑的实时状态。
 * 数据源：插件后端 /api/plugins/bio-brain/status
 *
 * 严格遵循 desktop-plugin SDK：
 *   - 只用 jsx() 调用（文件不编译，无 JSX 语法）
 *   - 只 import @hermes/plugin-sdk / react / react/jsx-runtime
 *   - 用主题变量，不硬编码颜色
 */
import { jsx } from 'react/jsx-runtime';
import { useState, useEffect } from 'react';

const ID = 'bio-brain';

// ---- 小组件 ----
function Row({ label, value }) {
  return jsx('div', {
    style: { display: 'flex', justifyContent: 'space-between', gap: '8px',
             padding: '3px 0', fontSize: '12px',
             borderBottom: '1px solid var(--ui-stroke-secondary)' },
    children: [
      jsx('span', { style: { color: 'var(--ui-text-quaternary)' }, children: label }),
      jsx('span', { style: { color: 'var(--ui-text-secondary)', fontWeight: 500,
                             textAlign: 'right', wordBreak: 'break-all' }, children: String(value) }),
    ],
  });
}

function Section({ title, children }) {
  return jsx('div', {
    style: { marginBottom: '14px' },
    children: [
      jsx('div', { style: { color: 'var(--ui-accent)', fontSize: '11px',
                            textTransform: 'uppercase', letterSpacing: '0.06em',
                            marginBottom: '6px', fontWeight: 600 }, children: title }),
      children,
    ],
  });
}

function BrainPanel({ ctx }) {
  const [state, setState] = useState(null);
  const [err, setErr] = useState(null);
  const [busy, setBusy] = useState(false);
  const [text, setText] = useState('');
  const [last, setLast] = useState(null);

  async function refresh() {
    try {
      const r = await ctx.rest('/status');
      if (r && r.ok) { setState(r.state); setErr(null); }
      else { setErr((r && r.error) || '未知错误'); }
    } catch (e) { setErr(String(e && e.message ? e.message : e)); }
  }

  useEffect(() => { refresh(); }, []);

  async function doThink() {
    if (!text.trim()) return;
    setBusy(true);
    try {
      const r = await ctx.rest('/think', { method: 'POST', body: { text, task_type: 'chat' } });
      if (r && r.ok) setLast(r.result);
      await refresh();
    } catch (e) { setErr(String(e)); }
    setBusy(false);
  }

  async function doSleep() {
    setBusy(true);
    try {
      const r = await ctx.rest('/sleep', { method: 'POST' });
      if (r && r.ok) setLast({ sleep: r.result.sleep });
      await refresh();
    } catch (e) { setErr(String(e)); }
    setBusy(false);
  }

  const btn = (label, fn, disabled) => jsx('button', {
    onClick: fn, disabled: disabled || busy,
    style: { padding: '5px 12px', borderRadius: '6px', cursor: 'pointer',
             fontSize: '12px', border: '1px solid var(--ui-stroke-secondary)',
             background: 'transparent', color: 'var(--ui-text-secondary)' },
    children: label,
  });

  if (err) {
    return jsx('div', { style: { padding: '12px', color: 'var(--ui-text-secondary)', fontSize: '12px' },
      children: [
        jsx('div', { style: { color: 'var(--ui-accent)', marginBottom: '6px' }, children: '仿生大脑 · 未连接' }),
        jsx('div', { children: err }),
        jsx('div', { style: { marginTop: '8px', color: 'var(--ui-text-quaternary)' },
          children: '提示：插件后端需在 config.yaml 的 plugins.enabled 中启用。' }),
      ] });
  }
  if (!state) return jsx('div', { style: { padding: '12px', fontSize: '12px',
    color: 'var(--ui-text-quaternary)' }, children: '加载中…' });

  const sm = state.self_model || {};
  const eb = state.experience_buffer || {};

  return jsx('div', { style: { padding: '12px', fontSize: '12px', overflowY: 'auto', height: '100%' },
    children: [
      jsx(Section, { title: '神经组织', children: [
        jsx(Row, { label: '神经元', value: state.neurons }),
        jsx(Row, { label: '神经束', value: state.tracts }),
        jsx(Row, { label: '神经组', value: state.groups }),
        jsx(Row, { label: '神经库', value: state.libraries }),
        jsx(Row, { label: '当前活跃', value: state.active }),
        jsx(Row, { label: '思考步数', value: state.ticks }),
      ]}),

      jsx(Section, { title: '分级驻留', children:
        Object.entries(state.tiers || {}).map(([k, v]) =>
          jsx(Row, { key: k, label: k, value: v }))
      }),

      jsx(Section, { title: '自我认知', children: [
        jsx(Row, { label: '擅长', value: (sm['擅长'] || []).join(', ') || '—' }),
        jsx(Row, { label: '不擅长', value: (sm['不擅长'] || []).join(', ') || '—' }),
        jsx(Row, { label: '成功率', value: sm['整体成功率'] }),
        jsx(Row, { label: '经历数', value: sm['经历数'] }),
      ]}),

      jsx(Section, { title: '学习状态', children: [
        jsx(Row, { label: '经验缓冲', value: eb.size }),
        jsx(Row, { label: '拒收(不可靠)', value: (eb.rejected || {}).unreliable || 0 }),
        jsx(Row, { label: 'REM候选', value: state.candidates }),
        jsx(Row, { label: '集体层', value: state.collective_entries }),
        jsx(Row, { label: '新生神经元', value: state.newborns }),
        jsx(Row, { label: '鲁棒等级', value: state.robustness }),
      ]}),

      jsx(Section, { title: '交互', children:
        jsx('div', { style: { display: 'flex', flexDirection: 'column', gap: '6px' },
          children: [
            jsx('input', {
              value: text, placeholder: '输入文本让它思考…',
              onChange: (e) => setText(e.target.value),
              style: { padding: '6px 8px', borderRadius: '6px', fontSize: '12px',
                       background: 'transparent', color: 'var(--ui-text-secondary)',
                       border: '1px solid var(--ui-stroke-secondary)' },
            }),
            jsx('div', { style: { display: 'flex', gap: '6px' },
              children: [ btn('思考', doThink, !text.trim()), btn('睡眠巩固', doSleep), btn('刷新', refresh) ] }),
            last ? jsx('pre', { style: { marginTop: '6px', padding: '8px', fontSize: '11px',
              color: 'var(--ui-text-quaternary)', overflowX: 'auto',
              border: '1px solid var(--ui-stroke-secondary)', borderRadius: '6px' },
              children: JSON.stringify(last, null, 1) }) : null,
          ] })
      }),
    ] });
}

export default {
  id: ID,
  name: '仿生大脑',
  register(ctx) {
    ctx.register({
      id: ID + '-pane',
      area: 'panes',
      title: '仿生大脑',
      data: { placement: 'right' },
      render: () => jsx(BrainPanel, { ctx }),
    });
    return () => {};
  },
};
