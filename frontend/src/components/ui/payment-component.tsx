import React, { useState } from 'react';
import { CreditCard, Smartphone, Building2, CheckCircle, Loader2 } from 'lucide-react';

interface PaymentComponentProps {
  totalAmount: number;
  currency?: string;
  onPaymentConfirm: (method: string) => void;
}

export function PaymentComponent({ 
  totalAmount, 
  currency = "AED",
  onPaymentConfirm 
}: PaymentComponentProps) {
  const [selectedMethod, setSelectedMethod] = useState<string>('');
  const [paymentStatus, setPaymentStatus] = useState<'idle' | 'processing' | 'success'>('idle');

  const paymentMethods = [
    {
      id: 'apple-pay',
      name: 'Apple Pay',
      icon: <Smartphone className="w-5 h-5" />,
      description: 'Pay with Touch ID or Face ID'
    },
    {
      id: 'credit-card',
      name: 'Credit/Debit Card',
      icon: <CreditCard className="w-5 h-5" />,
      description: 'Visa, Mastercard, American Express'
    },
    {
      id: 'bank-transfer',
      name: 'Bank Transfer',
      icon: <Building2 className="w-5 h-5" />,
      description: 'Direct bank transfer'
    }
  ];

  const handlePayment = async () => {
    if (!selectedMethod) return;
    
    setPaymentStatus('processing');
    
    // Simulate payment processing
    setTimeout(() => {
      setPaymentStatus('success');
      onPaymentConfirm(selectedMethod);
    }, 2000);
  };

  if (paymentStatus === 'success') {
    return (
      <div className="mt-4 p-6 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
        <div className="flex items-center space-x-3">
          <CheckCircle className="w-8 h-8 text-green-500" />
          <div>
            <h3 className="text-lg font-semibold text-green-800 dark:text-green-200">
              Payment Successful!
            </h3>
            <p className="text-sm text-green-600 dark:text-green-400">
              {currency} {totalAmount.toLocaleString()} paid via {paymentMethods.find(m => m.id === selectedMethod)?.name}
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="mt-4 p-4 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-sm">
      {/* Payment Summary */}
      <div className="mb-4 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
        <div className="flex justify-between items-center">
          <span className="text-sm font-medium text-blue-800 dark:text-blue-200">
            Total Amount:
          </span>
          <span className="text-lg font-bold text-blue-900 dark:text-blue-100">
            {currency} {totalAmount.toLocaleString()}
          </span>
        </div>
      </div>

      {/* Payment Methods */}
      <div className="space-y-3 mb-4">
        <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300">
          Choose Payment Method:
        </h4>
        
        {paymentMethods.map((method) => (
          <div
            key={method.id}
            className={`p-3 border rounded-lg cursor-pointer transition-all ${
              selectedMethod === method.id
                ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                : 'border-gray-200 dark:border-gray-600 hover:border-gray-300 dark:hover:border-gray-500'
            }`}
            onClick={() => setSelectedMethod(method.id)}
          >
            <div className="flex items-center space-x-3">
              <div className={`p-2 rounded-full ${
                selectedMethod === method.id
                  ? 'bg-blue-100 dark:bg-blue-800 text-blue-600 dark:text-blue-300'
                  : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400'
              }`}>
                {method.icon}
              </div>
              <div className="flex-1">
                <div className="flex items-center">
                  <span className="font-medium text-gray-900 dark:text-gray-100">
                    {method.name}
                  </span>
                  {selectedMethod === method.id && (
                    <CheckCircle className="w-4 h-4 text-blue-500 ml-2" />
                  )}
                </div>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  {method.description}
                </p>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Pay Button */}
      <button
        onClick={handlePayment}
        disabled={!selectedMethod || paymentStatus === 'processing'}
        className={`w-full py-3 px-4 rounded-lg font-medium transition-all ${
          selectedMethod && paymentStatus !== 'processing'
            ? 'bg-blue-600 hover:bg-blue-700 text-white'
            : 'bg-gray-300 dark:bg-gray-600 text-gray-500 dark:text-gray-400 cursor-not-allowed'
        }`}
      >
        {paymentStatus === 'processing' ? (
          <div className="flex items-center justify-center">
            <Loader2 className="w-4 h-4 animate-spin mr-2" />
            Processing Payment...
          </div>
        ) : (
          `Pay ${currency} ${totalAmount.toLocaleString()}`
        )}
      </button>
    </div>
  );
} 