"use client";

import { useRef, useEffect } from 'react';
import { Sidebar } from '@/components/ui/sidebar';
import { PromptBox } from '@/components/ui/chatgpt-prompt-input';
import { BotIcon, UserIcon, AlertCircle, Loader2 } from 'lucide-react';
import { useChatSession } from '@/lib/useChatSession';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';
import 'highlight.js/styles/github-dark.css';

export default function Home() {
  const {
    messages,
    isLoading,
    error,
    sendMessage,
    createNewSession,
    clearError,
    isConnected,
  } = useChatSession();

  const promptBoxRef = useRef<HTMLTextAreaElement & { clearInput?: () => void }>(null);
  const chatContainerRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages are added
  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [messages]);

  const handleNewChat = () => {
    console.log('🔄 Starting new chat...');
    createNewSession();
    console.log('✅ New chat created successfully');
  };

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const form = event.currentTarget;
    const formData = new FormData(form);
    const message = formData.get("message") as string;
    
    if (!message?.trim() || isLoading) return;

    // Clear the form immediately before sending message
    form.reset();
    
    // Clear the PromptBox internal state
    if (promptBoxRef.current?.clearInput) {
      promptBoxRef.current.clearInput();
    }
    
    await sendMessage(message);
  };

  const handlePromptSubmit = async () => {
    const form = document.querySelector('form') as HTMLFormElement;
    if (form) {
      const formData = new FormData(form);
      const message = formData.get("message") as string;
      
      if (!message?.trim() || isLoading) return;

      // Clear the form immediately before sending message
      form.reset();
      
      // Clear the PromptBox internal state
      if (promptBoxRef.current?.clearInput) {
        promptBoxRef.current.clearInput();
      }
      
      await sendMessage(message);
    }
  };

  return (
    <div className="flex h-screen bg-background">
      <Sidebar onNewChat={handleNewChat} currentPage="home" />
      
      <div className="flex-1 flex flex-col ml-[3.05rem]">
        {/* Connection status */}
        {!isConnected && (
          <div className="bg-yellow-100 dark:bg-yellow-900 border-l-4 border-yellow-500 p-4">
            <div className="flex items-center">
              <AlertCircle className="h-5 w-5 text-yellow-600 dark:text-yellow-400 mr-2" />
              <div className="space-y-1">
                <p className="text-sm text-yellow-800 dark:text-yellow-200">
                  Connection to AI service lost. Attempting to reconnect...
                </p>
              </div>
            </div>
          </div>
        )}
        
        {/* Error display */}
        {error && (
          <div className="bg-red-100 dark:bg-red-900 border-l-4 border-red-500 p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <AlertCircle className="h-5 w-5 text-red-600 dark:text-red-400 mr-2" />
                <p className="text-sm text-red-800 dark:text-red-200">{error}</p>
              </div>
              <button
                onClick={clearError}
                className="text-red-600 dark:text-red-400 hover:text-red-800 dark:hover:text-red-200"
              >
                ×
              </button>
            </div>
          </div>
        )}

        {/* Chat messages */}
        <div ref={chatContainerRef} className="flex-1 overflow-y-auto p-4 space-y-4">
          <div className="max-w-4xl mx-auto space-y-6">
            {messages.length === 0 && (
              <div className="text-center text-gray-500 dark:text-gray-400 mt-8">
                <div className="w-24 h-24 mx-auto mb-4 text-[#23938c]">
                  <svg viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm-1-13h2v6h-2zm0 8h2v2h-2z"/>
                  </svg>
                </div>
                <div className="space-y-2">
                  <p className="text-lg font-medium">Welcome to Bakery Quotation Assistant</p>
                  <p className="text-sm">Start your bakery quotation by typing a message below.</p>
                  <p className="text-xs text-gray-400 mt-4">
                    I'll guide you through the process of creating a professional quotation.
                  </p>
                </div>
              </div>
            )}
            
            {messages.map((message, index) => (
              <div key={index} className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`flex items-start space-x-3 max-w-3xl ${message.role === 'user' ? 'flex-row-reverse space-x-reverse' : ''}`}>
                  <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
                    message.role === 'user' 
                      ? 'bg-[#23938c] text-white' 
                      : 'bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-300'
                  }`}>
                    {message.role === 'user' ? <UserIcon className="w-4 h-4" /> : <BotIcon className="w-4 h-4" />}
                  </div>
                  <div className={`flex-1 px-4 py-3 rounded-lg ${
                    message.role === 'user'
                      ? 'bg-[#23938c] text-white'
                      : 'bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100'
                  }`}>
                    {message.role === 'user' ? (
                      <p className="whitespace-pre-wrap">{message.content}</p>
                    ) : (
                      <div className="prose prose-sm max-w-none dark:prose-invert">
                        <ReactMarkdown 
                          remarkPlugins={[remarkGfm]}
                          rehypePlugins={[rehypeHighlight]}
                        >
                          {message.content}
                        </ReactMarkdown>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Input section */}
        <div className="border-t border-border dark:border-gray-600 p-4">
          <div className="max-w-4xl mx-auto">
            {isLoading && (
              <div className="flex items-center justify-center mb-4 p-2">
                <Loader2 className="h-5 w-5 animate-spin mr-2" />
                <span className="text-sm text-muted-foreground">AI is thinking...</span>
              </div>
            )}
            <form onSubmit={handleSubmit}>
              <PromptBox 
                ref={promptBoxRef}
                name="message"
                placeholder={isLoading ? "Please wait..." : "Type your message to create a quotation..."}
                disabled={isLoading}
                onSubmit={handlePromptSubmit}
              />
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}
