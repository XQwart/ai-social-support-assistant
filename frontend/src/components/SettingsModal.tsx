interface SettingsModalProps {
    isOpen: boolean;
    onClose: () => void;
  }
  
  export default function SettingsModal({ isOpen, onClose }: SettingsModalProps) {
    if (!isOpen) return null;
  
    return (
      <div className="fixed inset-0 z-[60] flex items-center justify-center">
        {/* Overlay */}
        <div className="absolute inset-0 bg-black/20" onClick={onClose} />
  
        {/* Modal */}
        <div
          className="relative z-10 w-full max-w-md rounded-2xl p-6 shadow-xl fade-in-up"
          style={{
            background: 'rgba(255,255,255,0.85)',
            backdropFilter: 'blur(24px)',
            WebkitBackdropFilter: 'blur(24px)',
            border: '1px solid rgba(255,255,255,0.5)',
          }}
        >
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-bold text-gray-800">Настройки</h3>
            <button
              onClick={onClose}
              className="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-black/5 transition-colors cursor-pointer"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="18" y1="6" x2="6" y2="18" />
                <line x1="6" y1="6" x2="18" y2="18" />
              </svg>
            </button>
          </div>
  
          <div className="space-y-4">
            {/* Placeholder settings */}
            <div className="p-4 rounded-xl bg-white/50 border border-white/40">
              <div className="text-sm font-medium text-gray-700 mb-1">Модель ИИ</div>
              <div className="text-xs text-gray-400">Настройка будет доступна после подключения бэкенда</div>
            </div>
  
            <div className="p-4 rounded-xl bg-white/50 border border-white/40">
              <div className="text-sm font-medium text-gray-700 mb-1">Регион</div>
              <div className="text-xs text-gray-400">Для более точных рекомендаций по вашему региону</div>
            </div>
  
            <div className="p-4 rounded-xl bg-white/50 border border-white/40">
              <div className="text-sm font-medium text-gray-700 mb-1">Уведомления</div>
              <div className="text-xs text-gray-400">Настройка уведомлений о новых мерах поддержки</div>
            </div>
          </div>
  
          <button
            onClick={onClose}
            className="w-full mt-6 py-3 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-medium text-sm transition-colors cursor-pointer"
          >
            Готово
          </button>
        </div>
      </div>
    );
  }
  