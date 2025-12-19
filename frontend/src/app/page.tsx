"use client";

import { useState, useRef, useEffect, FormEvent } from 'react';
import { Sidebar } from '@/components/ui/sidebar';
import { PromptBox } from '@/components/ui/chatgpt-prompt-input';
import { BotIcon, UserIcon, AlertCircle, Loader2, CheckCircle2 } from 'lucide-react';
import { createQuotation, getAvailableJobTypes, QuoteRequest, QuoteResponse } from '@/lib/bakery-api';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  quoteData?: QuoteResponse;
}

interface FormData {
  customer_name: string;
  job_type: string;
  quantity: string;
  due_date: string;
  company_name: string;
  notes: string;
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentStep, setCurrentStep] = useState<'initial' | 'form' | 'processing' | 'complete'>('initial');
  const [formData, setFormData] = useState<FormData>({
    customer_name: '',
    job_type: '',
    quantity: '',
    due_date: '',
    company_name: 'Artisan Bakery',
    notes: ''
  });
  const [jobTypes, setJobTypes] = useState<string[]>([]);

  const promptBoxRef = useRef<HTMLTextAreaElement & { clearInput?: () => void }>(null);
  const chatContainerRef = useRef<HTMLDivElement>(null);

  // Load available job types on mount
  useEffect(() => {
    const loadJobTypes = async () => {
      try {
        const types = await getAvailableJobTypes();
        setJobTypes(types);
      } catch (error) {
        console.error('Failed to load job types:', error);
        setJobTypes(['cupcakes', 'cake', 'pastry_box']);
      }
    };
    loadJobTypes();
  }, []);

  // Auto-scroll to bottom when new messages are added
  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [messages]);

  const handleNewChat = () => {
    setMessages([]);
    setCurrentStep('initial');
    setFormData({
      customer_name: '',
      job_type: '',
      quantity: '',
      due_date: '',
      company_name: 'Artisan Bakery',
      notes: ''
    });
    setError(null);
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const form = event.currentTarget;
    const formDataObj = new FormData(form);
    const message = formDataObj.get("message") as string;
    
    if (!message?.trim() || isLoading) return;

    // Clear the form
    form.reset();
    if (promptBoxRef.current?.clearInput) {
      promptBoxRef.current.clearInput();
    }

    // Add user message
    setMessages(prev => [...prev, { role: 'user', content: message }]);

    // Handle based on current step
    if (currentStep === 'initial') {
      // User wants to create a quote
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Great! I\'ll help you create a bakery quotation. Please fill in the details below:'
      }]);
      setCurrentStep('form');
    }
  };

  const handleFormSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    
    // Validation
    if (!formData.customer_name.trim()) {
      setError('Please enter customer name');
      return;
    }
    if (!formData.job_type) {
      setError('Please select a job type');
      return;
    }
    if (!formData.quantity || parseInt(formData.quantity) <= 0) {
      setError('Please enter a valid quantity');
      return;
    }
    if (!formData.due_date) {
      setError('Please select a due date');
      return;
    }

    setError(null);
    setIsLoading(true);
    setCurrentStep('processing');

    try {
      // Create the quote request
      const request: QuoteRequest = {
        customer_name: formData.customer_name,
        job_type: formData.job_type,
        quantity: parseInt(formData.quantity),
        due_date: formData.due_date,
        company_name: formData.company_name || 'Artisan Bakery',
        notes: formData.notes || undefined
      };

      // Call the API
      const response = await createQuotation(request);

      // Add success message
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `✅ Quote generated successfully!\n\n**Quote ID:** ${response.quote_id}\n**Total:** ${response.total.toFixed(2)} ${response.currency}\n**File:** ${response.file_path}`,
        quoteData: response
      }]);

      setCurrentStep('complete');
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to create quotation';
      setError(errorMessage);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `❌ Error: ${errorMessage}\n\nPlease try again or contact support.`
      }]);
      setCurrentStep('form');
    } finally {
      setIsLoading(false);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    setFormData(prev => ({
      ...prev,
      [e.target.name]: e.target.value
    }));
  };

  return (
    <div className="flex h-screen bg-background">
      <Sidebar onNewChat={handleNewChat} currentPage="home" />
      
      <div className="flex-1 flex flex-col ml-[3.05rem]">
        {/* Error display */}
        {error && (
          <div className="bg-red-100 dark:bg-red-900 border-l-4 border-red-500 p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <AlertCircle className="h-5 w-5 text-red-600 dark:text-red-400 mr-2" />
                <p className="text-sm text-red-800 dark:text-red-200">{error}</p>
              </div>
              <button
                onClick={() => setError(null)}
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
                  <p className="text-lg font-medium">Welcome to Bakery Quotation System</p>
                  <p className="text-sm">Type a message below to create a new quotation.</p>
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
                    <p className="whitespace-pre-wrap">{message.content}</p>
                    
                    {/* Show quote details card if available */}
                    {message.quoteData && (
                      <div className="mt-4 p-4 bg-white dark:bg-gray-900 rounded-lg border-2 border-green-500">
                        <div className="flex items-center mb-2">
                          <CheckCircle2 className="w-5 h-5 text-green-500 mr-2" />
                          <h3 className="font-semibold text-green-700 dark:text-green-400">Quote Generated</h3>
                        </div>
                        <div className="space-y-1 text-sm">
                          <p><strong>Quote ID:</strong> {message.quoteData.quote_id}</p>
                          <p><strong>Total:</strong> {message.quoteData.currency} {message.quoteData.total.toFixed(2)}</p>
                          <p><strong>Created:</strong> {new Date(message.quoteData.created_at).toLocaleString()}</p>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}

            {/* Quote Form */}
            {currentStep === 'form' && !isLoading && (
              <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-lg">
                <h2 className="text-xl font-semibold mb-4">Quotation Details</h2>
                <form onSubmit={handleFormSubmit} className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium mb-1">Customer Name *</label>
                    <input
                      type="text"
                      name="customer_name"
                      value={formData.customer_name}
                      onChange={handleInputChange}
                      className="w-full px-3 py-2 border rounded-md dark:bg-gray-700 dark:border-gray-600"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-1">Job Type *</label>
                    <select
                      name="job_type"
                      value={formData.job_type}
                      onChange={handleInputChange}
                      className="w-full px-3 py-2 border rounded-md dark:bg-gray-700 dark:border-gray-600"
                      required
                    >
                      <option value="">Select a job type...</option>
                      {jobTypes.map(type => (
                        <option key={type} value={type}>{type}</option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-1">Quantity *</label>
                    <input
                      type="number"
                      name="quantity"
                      value={formData.quantity}
                      onChange={handleInputChange}
                      min="1"
                      className="w-full px-3 py-2 border rounded-md dark:bg-gray-700 dark:border-gray-600"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-1">Due Date *</label>
                    <input
                      type="date"
                      name="due_date"
                      value={formData.due_date}
                      onChange={handleInputChange}
                      min={new Date().toISOString().split('T')[0]}
                      className="w-full px-3 py-2 border rounded-md dark:bg-gray-700 dark:border-gray-600"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-1">Company Name</label>
                    <input
                      type="text"
                      name="company_name"
                      value={formData.company_name}
                      onChange={handleInputChange}
                      className="w-full px-3 py-2 border rounded-md dark:bg-gray-700 dark:border-gray-600"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-1">Notes</label>
                    <textarea
                      name="notes"
                      value={formData.notes}
                      onChange={handleInputChange}
                      rows={3}
                      className="w-full px-3 py-2 border rounded-md dark:bg-gray-700 dark:border-gray-600"
                    />
                  </div>

                  <button
                    type="submit"
                    className="w-full bg-[#23938c] text-white py-2 px-4 rounded-md hover:bg-[#1d7a74] transition-colors"
                  >
                    Generate Quote
                  </button>
                </form>
              </div>
            )}

            {/* Loading indicator */}
            {isLoading && (
              <div className="flex items-center justify-center p-4">
                <Loader2 className="h-6 w-6 animate-spin text-[#23938c] mr-2" />
                <span className="text-sm text-muted-foreground">Generating quotation...</span>
              </div>
            )}
          </div>
        </div>

        {/* Input section */}
        {currentStep !== 'form' && currentStep !== 'processing' && (
          <div className="border-t border-border dark:border-gray-600 p-4">
            <div className="max-w-4xl mx-auto">
              <form onSubmit={handleSubmit}>
                <PromptBox 
                  ref={promptBoxRef}
                  name="message"
                  placeholder="Type your message to create a new quote..."
                  disabled={isLoading}
                  onSubmit={() => {}}
                />
              </form>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
