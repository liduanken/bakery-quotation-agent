/**
 * Integration Test Page
 * Use this page to test all backend API integrations
 */
"use client";

import { useState } from 'react';
import { backendApi } from '@/lib/backend-api';
import { Sidebar } from '@/components/ui/sidebar';

interface TestResult {
  endpoint: string;
  success: boolean;
  data?: any;
  error?: string;
  duration: number;
}

export default function IntegrationTest() {
  const [results, setResults] = useState<TestResult[]>([]);
  const [isRunning, setIsRunning] = useState(false);

  const runTest = async (testName: string, testFn: () => Promise<any>) => {
    const startTime = Date.now();
    try {
      const result = await testFn();
      const duration = Date.now() - startTime;
      
      setResults(prev => [...prev, {
        endpoint: testName,
        success: true,
        data: result,
        duration
      }]);
    } catch (error) {
      const duration = Date.now() - startTime;
      setResults(prev => [...prev, {
        endpoint: testName,
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
        duration
      }]);
    }
  };

  const runAllTests = async () => {
    setIsRunning(true);
    setResults([]);

    // Test 1: Health Check
    await runTest('Health Check', () => backendApi.healthCheck());

    // Test 2: Trade Name List
    await runTest('Trade Name List', () => 
      backendApi.getTradeNameList({
        header: {
          requestId: 'test_123',
          timestamp: new Date().toISOString(),
          channel: 'web'
        },
        body: {
          data: {
            identityNumber: '784-1990-1234567-8'
          }
        }
      })
    );

    // Test 3: Trade Name Check
    await runTest('Trade Name Check', () =>
      backendApi.checkTradeNameAvailability({
        header: {
          requestId: 'test_124',
          timestamp: new Date().toISOString(),
          channel: 'web'
        },
        body: {
          data: {
            tradeLicenseNo: 'TEST COMPANY LLC'
          }
        }
      })
    );

    // Test 4: Business Activities
    await runTest('Business Activities', () => backendApi.getBusinessActivities());

    // Test 5: Transliteration
    await runTest('Transliteration', () =>
      backendApi.transliterate({
        input_name: 'Test Company',
        input_language: 'en',
        target_language: 'ar'
      })
    );

    // Test 6: Yamli Suggestions
    await runTest('Yamli Suggestions', () => 
      backendApi.getYamliSuggestions('تجربة')
    );

    setIsRunning(false);
  };

  return (
    <div className="flex h-screen bg-background">
      <Sidebar currentPage="home" />
      
      <div className="flex-1 flex flex-col ml-[3.05rem] p-6">
        <div className="max-w-6xl mx-auto">
          <h1 className="text-3xl font-bold mb-6">Backend Integration Test</h1>
          
          <div className="mb-6">
            <button
              onClick={runAllTests}
              disabled={isRunning}
              className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              {isRunning ? 'Running Tests...' : 'Run All Tests'}
            </button>
          </div>

          <div className="space-y-4">
            {results.map((result, index) => (
              <div
                key={index}
                className={`p-4 rounded-lg border ${
                  result.success 
                    ? 'border-green-200 bg-green-50 dark:border-green-800 dark:bg-green-900/20'
                    : 'border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-900/20'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-semibold">{result.endpoint}</h3>
                  <div className="flex items-center space-x-2">
                    <span className={`px-2 py-1 rounded text-sm ${
                      result.success 
                        ? 'bg-green-100 text-green-800 dark:bg-green-800 dark:text-green-100'
                        : 'bg-red-100 text-red-800 dark:bg-red-800 dark:text-red-100'
                    }`}>
                      {result.success ? 'PASS' : 'FAIL'}
                    </span>
                    <span className="text-sm text-gray-500">{result.duration}ms</span>
                  </div>
                </div>
                
                {result.error && (
                  <div className="text-red-600 dark:text-red-400 text-sm mb-2">
                    Error: {result.error}
                  </div>
                )}
                
                {result.data && (
                  <details className="text-sm">
                    <summary className="cursor-pointer text-gray-600 dark:text-gray-400">
                      View Response Data
                    </summary>
                    <pre className="mt-2 p-2 bg-gray-100 dark:bg-gray-800 rounded overflow-auto text-xs">
                      {JSON.stringify(result.data, null, 2)}
                    </pre>
                  </details>
                )}
              </div>
            ))}
          </div>

          <div className="mt-8 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
            <h3 className="font-semibold mb-2">Integration Status</h3>
            <div className="text-sm text-gray-600 dark:text-gray-400">
              <p>• Backend URL: {process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'}</p>
              <p>• Total Tests: {results.length}</p>
              <p>• Passed: {results.filter(r => r.success).length}</p>
              <p>• Failed: {results.filter(r => !r.success).length}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
