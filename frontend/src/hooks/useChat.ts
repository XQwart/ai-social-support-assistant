import { useState, useCallback } from 'react';
import type { Chat, Message } from '@/types';
import { sendMessage as apiSendMessage } from '@/api/chatApi';
import { v4 as uuidv4 } from 'uuid';

const DEMO_CHATS: Chat[] = [
  {
    id: '1',
    title: 'Льготы для многодетных семей',
    messages: [],
    createdAt: Date.now() - 1800000,
    updatedAt: Date.now() - 1800000,
  },
  {
    id: '2',
    title: 'Субсидия на оплату ЖКХ',
    messages: [],
    createdAt: Date.now() - 3600000,
    updatedAt: Date.now() - 3600000,
  },
  {
    id: '3',
    title: 'Оформление материнского капитала',
    messages: [],
    createdAt: Date.now() - 86400000,
    updatedAt: Date.now() - 86400000,
  },
  {
    id: '4',
    title: 'Пенсия по инвалидности',
    messages: [],
    createdAt: Date.now() - 86400000,
    updatedAt: Date.now() - 86400000,
  },
  {
    id: '5',
    title: 'Пособие по безработице',
    messages: [],
    createdAt: Date.now() - 172800000,
    updatedAt: Date.now() - 172800000,
  },
  {
    id: '6',
    title: 'Выплаты при рождении ребёнка',
    messages: [],
    createdAt: Date.now() - 259200000,
    updatedAt: Date.now() - 259200000,
  },
];

export function useChat() {
  const [chats, setChats] = useState<Chat[]>(DEMO_CHATS);
  const [activeChatId, setActiveChatId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const activeChat = chats.find((c) => c.id === activeChatId) || null;

  const createNewChat = useCallback((initialMessage?: string) => {
    const newChat: Chat = {
      id: uuidv4(),
      title: initialMessage ? initialMessage.slice(0, 60) : 'Новый чат',
      messages: [],
      createdAt: Date.now(),
      updatedAt: Date.now(),
    };
    setChats((prev) => [newChat, ...prev]);
    setActiveChatId(newChat.id);
    return newChat.id;
  }, []);

  const sendMessage = useCallback(
    async (content: string) => {
      let chatId = activeChatId;

      if (!chatId) {
        chatId = createNewChat(content);
      }

      const userMsg: Message = {
        id: uuidv4(),
        role: 'user',
        content,
        timestamp: Date.now(),
      };

      setChats((prev) =>
        prev.map((c) =>
          c.id === chatId
            ? {
                ...c,
                title: c.messages.length === 0 ? content.slice(0, 60) : c.title,
                messages: [...c.messages, userMsg],
                updatedAt: Date.now(),
              }
            : c
        )
      );

      setIsLoading(true);

      try {
        const reply = await apiSendMessage(chatId, content);
        setChats((prev) =>
          prev.map((c) =>
            c.id === chatId
              ? { ...c, messages: [...c.messages, reply], updatedAt: Date.now() }
              : c
          )
        );
      } catch {
        const errMsg: Message = {
          id: uuidv4(),
          role: 'assistant',
          content: 'Произошла ошибка. Попробуйте ещё раз.',
          timestamp: Date.now(),
        };
        setChats((prev) =>
          prev.map((c) =>
            c.id === chatId
              ? { ...c, messages: [...c.messages, errMsg], updatedAt: Date.now() }
              : c
          )
        );
      } finally {
        setIsLoading(false);
      }
    },
    [activeChatId, createNewChat]
  );

  const selectChat = useCallback((id: string) => setActiveChatId(id), []);
  const goHome = useCallback(() => setActiveChatId(null), []);
  const deleteChatById = useCallback(
    (id: string) => {
      setChats((prev) => prev.filter((c) => c.id !== id));
      if (activeChatId === id) setActiveChatId(null);
    },
    [activeChatId]
  );

  return {
    chats,
    activeChat,
    activeChatId,
    isLoading,
    sendMessage,
    createNewChat,
    selectChat,
    goHome,
    deleteChat: deleteChatById,
  };
}
