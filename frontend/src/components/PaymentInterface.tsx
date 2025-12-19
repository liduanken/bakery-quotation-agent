'use client';

import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { CreditCard, Smartphone, Building2, CheckCircle, Loader2 } from 'lucide-react';

interface PaymentInterface {
  type: 'payment_request';
  amount: number;
  currency: string;
  description: string;
  application_id: string;
  payment_methods: string[];
}

interface PaymentInterfaceProps {
  paymentData: PaymentInterface;
  onPaymentConfirm: (method: string) => void;
}

export function PaymentInterface({ paymentData, onPaymentConfirm }: PaymentInterfaceProps) {
  const [selectedMethod, setSelectedMethod] = useState<string>('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [isCompleted, setIsCompleted] = useState(false);

  const handlePayment = async () => {
    if (!selectedMethod) return;
    
    setIsProcessing(true);
    
    // Simulate payment processing
    setTimeout(() => {
      setIsProcessing(false);
      setIsCompleted(true);
      onPaymentConfirm(selectedMethod);
    }, 2000);
  };

  const getPaymentIcon = (method: string) => {
    switch (method.toLowerCase()) {
      case 'apple pay':
        return <Smartphone className="w-5 h-5" />;
      case 'card payment':
        return <CreditCard className="w-5 h-5" />;
      case 'online banking':
        return <Building2 className="w-5 h-5" />;
      default:
        return <CreditCard className="w-5 h-5" />;
    }
  };

  if (isCompleted) {
    return (
      <Card className="w-full max-w-md mx-auto border-green-200 bg-green-50">
        <CardContent className="p-6 text-center">
          <CheckCircle className="w-12 h-12 text-green-600 mx-auto mb-4" />
          <div className="mb-2">
            <h3 className="text-lg font-semibold text-green-800">Payment Successful!</h3>
            <h3 className="text-sm font-semibold text-green-700" dir="rtl">تم الدفع بنجاح!</h3>
          </div>
          <p className="text-green-700">
            {paymentData.currency} {paymentData.amount.toLocaleString()} processed via {selectedMethod}
          </p>
          <div className="mt-2">
            <Badge variant="outline" className="border-green-300 text-green-700">
              Application ID: {paymentData.application_id}
            </Badge>
            <Badge variant="outline" className="mt-1 border-green-300 text-green-700" dir="rtl">
              رقم الطلب: {paymentData.application_id}
            </Badge>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="w-full max-w-md mx-auto border-blue-200 bg-blue-50">
      <CardHeader className="text-center">
        <div>
          <CardTitle className="text-xl text-blue-900">💳 Payment Required</CardTitle>
          <CardTitle className="text-lg text-blue-800" dir="rtl">💳 الدفع مطلوب</CardTitle>
        </div>
        <CardDescription className="text-blue-700">
          {paymentData.description}
        </CardDescription>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {/* Amount Display */}
        <div className="text-center p-4 bg-white rounded-lg border">
          <div className="text-2xl font-bold text-gray-900">
            {paymentData.currency} {paymentData.amount.toLocaleString()}
          </div>
          <div className="text-sm text-gray-600">
            <div>Application ID: {paymentData.application_id}</div>
            <div dir="rtl">رقم الطلب: {paymentData.application_id}</div>
          </div>
        </div>

        {/* Payment Methods */}
        <div className="space-y-2">
          <div className="text-sm font-medium text-gray-700">
            <div>Select Payment Method:</div>
            <div dir="rtl">اختر طريقة الدفع:</div>
          </div>
          {paymentData.payment_methods.map((method) => (
            <button
              key={method}
              onClick={() => setSelectedMethod(method)}
              className={`w-full p-3 border rounded-lg flex items-center space-x-3 transition-colors ${
                selectedMethod === method
                  ? 'border-blue-500 bg-blue-100 text-blue-900'
                  : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
              }`}
            >
              {getPaymentIcon(method)}
              <span className="font-medium">{method}</span>
              {selectedMethod === method && (
                <CheckCircle className="w-5 h-5 text-blue-600 ml-auto" />
              )}
            </button>
          ))}
        </div>

        {/* Payment Button */}
        <Button
          onClick={handlePayment}
          disabled={!selectedMethod || isProcessing}
          className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-3"
        >
          {isProcessing ? (
            <div className="flex items-center justify-center">
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              <div className="flex flex-col">
                <span>Processing Payment...</span>
                <span className="text-xs" dir="rtl">جاري معالجة الدفع...</span>
              </div>
            </div>
          ) : (
            <div className="flex flex-col">
              <span>{`Pay ${paymentData.currency} ${paymentData.amount.toLocaleString()}`}</span>
              <span className="text-xs" dir="rtl">{`دفع ${paymentData.currency} ${paymentData.amount.toLocaleString()}`}</span>
            </div>
          )}
        </Button>

        <div className="text-xs text-gray-500 text-center">
          <p>Your payment is secured with industry-standard encryption</p>
          <p dir="rtl">دفعتك محمية بتشفير معياري في الصناعة</p>
        </div>
      </CardContent>
    </Card>
  );
} 