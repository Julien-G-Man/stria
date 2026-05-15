'use client';

import { useState, useRef, useEffect, useCallback } from 'react';
import ReactMarkdown from 'react-markdown';
import { sendMessage } from '@/lib/api';
import type { ReadResponse, AssistantMessage, AssistantMessageWithSources } from '@/lib/types';

interface Props {
  result: ReadResponse;
  onClose: () => void;
}

const outcomeChip: Record<string, { bg: string; text: string; border: string }> = {
  positive: { bg: '#fef2f2', text: '#b91c1c', border: '#fecaca' },
  negative: { bg: '#f0fdf4', text: '#15803d', border: '#bbf7d0' },
  invalid:  { bg: '#fffbeb', text: '#b45309', border: '#fde68a' },
};

export default function AssistantDrawer({ result, onClose }: Props) {
  const [messages, setMessages] = useState<AssistantMessageWithSources[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [dragY, setDragY] = useState(0);
  const [dragging, setDragging] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const dragStartY = useRef<number | null>(null);

  const onTouchStart = useCallback((e: React.TouchEvent) => {
    dragStartY.current = e.touches[0].clientY;
    setDragging(true);
  }, []);

  const onTouchMove = useCallback((e: React.TouchEvent) => {
    if (dragStartY.current === null) return;
    const delta = e.touches[0].clientY - dragStartY.current;
    if (delta > 0) setDragY(delta);
  }, []);

  const onTouchEnd = useCallback(() => {
    if (dragY > 100) {
      onClose();
    } else {
      setDragY(0);
    }
    setDragging(false);
    dragStartY.current = null;
  }, [dragY, onClose]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const send = async () => {
    const text = input.trim();
    if (!text || loading) return;
    setMessages((prev) => [...prev, { role: 'user', content: text }]);
    setInput('');
    setLoading(true);
    const history: AssistantMessage[] = messages.map(({ role, content }) => ({ role, content }));
    try {
      const resp = await sendMessage({ message: text, scan_context: result, history });
      setMessages((prev) => [...prev, { role: 'assistant', content: resp.message, sources: resp.sources }]);
    } catch {
      setMessages((prev) => [...prev, { role: 'assistant', content: 'Could not reach the server. Please try again.' }]);
    } finally {
      setLoading(false);
    }
  };

  const chip = outcomeChip[result.result.outcome] ?? { bg: '#f9fafb', text: '#374151', border: '#e5e7eb' };
  const typeLabel = result.cassette_type.charAt(0).toUpperCase() + result.cassette_type.slice(1);

  return (
    <div className="fixed inset-0 z-50 flex items-end">
      {/* Backdrop */}
      <div
        className="absolute inset-0"
        style={{ backgroundColor: 'rgba(0,0,0,0.45)' }}
        onClick={onClose}
      />

      {/* Drawer */}
      <div
        className="relative w-full flex flex-col rounded-t-3xl overflow-hidden"
        style={{
          height: '82vh',
          backgroundColor: '#ffffff',
          maxWidth: '100vw',
          boxSizing: 'border-box',
          transform: `translateY(${dragY}px)`,
          transition: dragging ? 'none' : 'transform 0.3s ease',
        }}
      >
        {/* Drag handle */}
        <div
          className="flex justify-center pt-3 pb-2 flex-shrink-0 cursor-grab active:cursor-grabbing"
          onTouchStart={onTouchStart}
          onTouchMove={onTouchMove}
          onTouchEnd={onTouchEnd}
        >
          <div className="w-10 h-1 rounded-full bg-gray-200" />
        </div>

        {/* Context chip */}
        <div className="mx-4 mb-4 flex-shrink-0">
          <div
            className="inline-flex items-center gap-2 px-3 py-2 rounded-xl text-xs font-semibold"
            style={{ backgroundColor: chip.bg, color: chip.text, border: `1px solid ${chip.border}` }}
          >
            <span className="capitalize">{typeLabel}</span>
            <span style={{ color: 'rgba(0,0,0,0.2)' }}>·</span>
            <span className="capitalize">{result.result.outcome}</span>
            {result.result.lines.test_line_intensity === 'faint' && (
              <><span style={{ color: 'rgba(0,0,0,0.2)' }}>·</span><span>Faint T line</span></>
            )}
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-4 pb-2 space-y-3 min-h-0">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full gap-3 py-8">
              <div className="w-12 h-12 rounded-2xl flex items-center justify-center" style={{ backgroundColor: '#eff6ff' }}>
                <svg width="22" height="22" fill="none" viewBox="0 0 24 24">
                  <path d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
                    stroke="#1A56A0" strokeWidth="1.5" strokeLinecap="round" />
                </svg>
              </div>
              <p className="text-sm text-gray-400 text-center max-w-[200px] leading-relaxed">
                Ask anything about this result
              </p>
              {/* Starter suggestions */}
              <div className="flex flex-col gap-2 w-full mt-2">
                {['What does this result mean?', 'What should I do next?', 'Is this result reliable?'].map((s) => (
                  <button
                    key={s}
                    onClick={() => { setInput(s); inputRef.current?.focus(); }}
                    className="text-sm text-left px-4 py-2.5 rounded-xl border border-gray-200 text-gray-600 hover:border-blue-300 hover:bg-blue-50 transition-colors"
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((m, i) => {
            const isUser = m.role === 'user';
            return (
              <div key={i} className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
                <div
                  className="max-w-[82%] rounded-2xl px-4 py-3 text-sm leading-relaxed"
                  style={
                    isUser
                      ? { backgroundColor: '#0a1e46', color: '#ffffff', borderBottomRightRadius: '4px' }
                      : { backgroundColor: '#f3f4f6', color: '#111827', borderBottomLeftRadius: '4px' }
                  }
                >
                  {isUser ? (
                    <p>{m.content}</p>
                  ) : (
                    <ReactMarkdown
                      components={{
                        p: ({ children }) => <p className="mb-1 last:mb-0">{children}</p>,
                        strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
                        ul: ({ children }) => <ul className="list-disc pl-4 mb-1 space-y-0.5">{children}</ul>,
                        ol: ({ children }) => <ol className="list-decimal pl-4 mb-1 space-y-0.5">{children}</ol>,
                        li: ({ children }) => <li>{children}</li>,
                        code: ({ children }) => <code className="px-1 py-0.5 rounded text-xs" style={{ backgroundColor: 'rgba(0,0,0,0.08)' }}>{children}</code>,
                      }}
                    >
                      {m.content}
                    </ReactMarkdown>
                  )}
                  {!isUser && m.sources && m.sources.length > 0 && (
                    <p className="text-xs mt-2 pt-1.5" style={{ color: '#9ca3af', borderTop: '1px solid #e5e7eb' }}>
                      {m.sources.join(' · ')}
                    </p>
                  )}
                </div>
              </div>
            );
          })}

          {loading && (
            <div className="flex justify-start">
              <div className="px-4 py-3 rounded-2xl text-sm" style={{ backgroundColor: '#f3f4f6', borderBottomLeftRadius: '4px' }}>
                <span className="flex gap-1">
                  {[0, 1, 2].map((i) => (
                    <span
                      key={i}
                      className="w-1.5 h-1.5 rounded-full bg-gray-400 animate-bounce"
                      style={{ animationDelay: `${i * 0.15}s` }}
                    />
                  ))}
                </span>
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {/* Input bar */}
        <div className="flex-shrink-0 px-4 pb-8 pt-3 flex gap-2" style={{ borderTop: '1px solid #f3f4f6', minWidth: 0 }}>
          <input
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && send()}
            placeholder="Ask about this result…"
            className="flex-1 rounded-2xl px-4 py-3 text-sm outline-none min-w-0"
            style={{ backgroundColor: '#f9fafb', border: '1.5px solid #e5e7eb', width: '100%' }}
          />
          <button
            onClick={send}
            disabled={!input.trim() || loading}
            className="w-11 h-11 rounded-2xl flex items-center justify-center transition-opacity disabled:opacity-40 self-end"
            style={{ backgroundColor: '#0a1e46' }}
            aria-label="Send"
          >
            <svg width="16" height="16" fill="none" viewBox="0 0 24 24">
              <path d="M22 2L11 13M22 2L15 22l-4-9-9-4 20-7z" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
}
