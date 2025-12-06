'use client';

import { useState, useEffect } from 'react';

interface Transaction {
  transaction_id: string;
  date: string;
  amount: number;
  merchant_name: string;
  category: string[];
  payment_channel: string;
  pending: boolean;
}

interface TransactionPreviewProps {
  onContinue: () => void;
  showContinueButton?: boolean;
}

export default function TransactionPreview({ onContinue, showContinueButton = true }: TransactionPreviewProps) {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [animatedStats, setAnimatedStats] = useState({
    totalTransactions: 0,
    totalSpending: 0,
    uniqueMerchants: 0,
  });

  // Fetch and parse CSV data
  useEffect(() => {
    const fetchTransactions = async () => {
      try {
        const response = await fetch(`/sample_transactions_1000_sorted.csv?t=${Date.now()}`);
        const text = await response.text();
        const lines = text.trim().split('\n');
        const headers = lines[0].split(',');

        const parsedTransactions = lines.slice(1).map((line) => {
          // More robust CSV parsing
          const regex = /,(?=(?:[^"]*"[^"]*")*[^"]*$)/;
          const values = line.split(regex).map(val => {
            // Remove outer quotes and unescape inner quotes
            if (val.startsWith('"') && val.endsWith('"')) {
              return val.slice(1, -1).replace(/""/g, '"');
            }
            return val;
          });

          return {
            transaction_id: values[0],
            date: values[1],
            amount: parseFloat(values[2]),
            merchant_name: values[3],
            category: JSON.parse(values[4]),
            payment_channel: values[5],
            pending: values[6] === 'True',
          };
        });

        setTransactions(parsedTransactions);
        setLoading(false);
      } catch (error) {
        console.error('Error loading transactions:', error);
        setLoading(false);
      }
    };

    fetchTransactions();
  }, []);

  // Calculate statistics
  const totalTransactions = transactions.length;
  const totalSpending = Math.abs(
    transactions.reduce((sum, tx) => sum + (tx.amount < 0 ? tx.amount : 0), 0)
  );
  const uniqueMerchants = new Set(transactions.map((tx) => tx.merchant_name)).size;
  const dateRange = transactions.length > 0
    ? `${new Date(transactions[transactions.length - 1].date).toLocaleDateString()} - ${new Date(transactions[0].date).toLocaleDateString()}`
    : '';

  // Counting animation
  useEffect(() => {
    if (!loading && transactions.length > 0) {
      const duration = 1500; // 1.5 seconds
      const steps = 60;
      const increment = duration / steps;

      let currentStep = 0;
      const timer = setInterval(() => {
        currentStep++;
        const progress = currentStep / steps;

        setAnimatedStats({
          totalTransactions: Math.floor(totalTransactions * progress),
          totalSpending: totalSpending * progress,
          uniqueMerchants: Math.floor(uniqueMerchants * progress),
        });

        if (currentStep >= steps) {
          clearInterval(timer);
          setAnimatedStats({
            totalTransactions,
            totalSpending,
            uniqueMerchants,
          });
        }
      }, increment);

      return () => clearInterval(timer);
    }
  }, [loading, transactions, totalTransactions, totalSpending, uniqueMerchants]);

  // Generate color for merchant badge
  const getInitialColor = (name: string) => {
    const colors = [
      'bg-red-500',
      'bg-blue-500',
      'bg-green-500',
      'bg-yellow-500',
      'bg-purple-500',
      'bg-pink-500',
      'bg-indigo-500',
      'bg-teal-500',
    ];
    const index = name.charCodeAt(0) % colors.length;
    return colors[index];
  };

  // Format currency
  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(Math.abs(amount));
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-16">
        <div className="relative w-16 h-16">
          <div className="absolute inset-0 border-4 border-white/20 rounded-full"></div>
          <div className="absolute inset-0 border-4 border-transparent border-t-teal-400 rounded-full animate-spin"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="animate-expand h-[80vh] flex flex-col">
      {/* Header */}
      <div className="text-center mb-6">
        <h2 className="text-3xl font-bold text-white mb-2">We found your transactions</h2>
        <p className="text-white/70">
          Review the data below, then continue to your personalized dashboard.
        </p>
      </div>

      {/* Summary Banner */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6 bg-white/5 rounded-xl p-4 border border-white/10">
        <div className="text-center">
          <p className="text-white/60 text-sm mb-1">Total Transactions</p>
          <p className="text-2xl font-bold text-white">{animatedStats.totalTransactions.toLocaleString()}</p>
        </div>
        <div className="text-center">
          <p className="text-white/60 text-sm mb-1">Date Range</p>
          <p className="text-sm font-semibold text-white">{dateRange}</p>
        </div>
        <div className="text-center">
          <p className="text-white/60 text-sm mb-1">Total Spending</p>
          <p className="text-2xl font-bold text-white">
            ${animatedStats.totalSpending.toLocaleString(undefined, { maximumFractionDigits: 0 })}
          </p>
        </div>
        <div className="text-center">
          <p className="text-white/60 text-sm mb-1">Unique Merchants</p>
          <p className="text-2xl font-bold text-white">{animatedStats.uniqueMerchants.toLocaleString()}</p>
        </div>
      </div>

      {/* Transaction Table */}
      <div className="flex-1 relative overflow-hidden rounded-xl border border-white/10 bg-white/5">
        {/* Fade overlay top */}
        <div className="absolute top-12 left-0 right-0 h-8 bg-gradient-to-b from-slate-900/50 to-transparent z-10 pointer-events-none"></div>

        {/* Fade overlay bottom */}
        <div className="absolute bottom-0 left-0 right-0 h-8 bg-gradient-to-t from-slate-900/50 to-transparent z-10 pointer-events-none"></div>

        <div className="overflow-y-auto h-full custom-scrollbar">
          <table className="w-full">
            <thead className="sticky top-0 bg-slate-800/90 backdrop-blur-sm z-20">
              <tr className="border-b border-white/10">
                <th className="text-left py-3 px-4 text-white/80 font-semibold text-sm">Date</th>
                <th className="text-left py-3 px-4 text-white/80 font-semibold text-sm">Merchant</th>
                <th className="text-left py-3 px-4 text-white/80 font-semibold text-sm">Category</th>
                <th className="text-right py-3 px-4 text-white/80 font-semibold text-sm">Amount</th>
              </tr>
            </thead>
            <tbody>
              {transactions.map((tx, index) => (
                <tr
                  key={tx.transaction_id}
                  className="border-b border-white/5 hover:bg-white/5 transition-colors"
                >
                  <td className="py-3 px-4 text-white/90 text-sm">
                    {new Date(tx.date).toLocaleDateString('en-US', {
                      month: 'short',
                      day: 'numeric',
                      year: 'numeric',
                    })}
                  </td>
                  <td className="py-3 px-4">
                    <div className="flex items-center gap-3">
                      {/* Merchant Badge */}
                      <div
                        className={`w-8 h-8 rounded-full ${getInitialColor(tx.merchant_name)} flex items-center justify-center text-white font-bold text-xs flex-shrink-0`}
                      >
                        {tx.merchant_name.charAt(0).toUpperCase()}
                      </div>
                      <span className="text-white/90 text-sm truncate">{tx.merchant_name}</span>
                    </div>
                  </td>
                  <td className="py-3 px-4">
                    <span className="inline-block px-3 py-1 bg-teal-500/20 text-teal-300 rounded-full text-xs font-medium border border-teal-400/30">
                      {tx.category[0]}
                    </span>
                  </td>
                  <td className={`py-3 px-4 text-right text-sm font-semibold ${tx.amount >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                    {tx.amount >= 0 ? '+' : '-'}{formatCurrency(tx.amount)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Continue Button */}
      {showContinueButton && (
        <button
          onClick={onContinue}
          className="mt-6 w-full bg-gradient-to-r from-teal-500 to-cyan-500 text-white py-4 rounded-xl font-semibold text-lg shadow-lg hover:shadow-teal-500/50 hover:scale-[1.02] transition-all duration-200"
        >
          Continue to Dashboard
        </button>
      )}

      <style jsx>{`
        @keyframes expand {
          from {
            opacity: 0;
            transform: scale(0.95);
          }
          to {
            opacity: 1;
            transform: scale(1);
          }
        }

        .animate-expand {
          animation: expand 0.5s ease-out;
        }

        .custom-scrollbar::-webkit-scrollbar {
          width: 8px;
        }

        .custom-scrollbar::-webkit-scrollbar-track {
          background: rgba(255, 255, 255, 0.05);
        }

        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: rgba(255, 255, 255, 0.2);
          border-radius: 4px;
        }

        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: rgba(255, 255, 255, 0.3);
        }
      `}</style>
    </div>
  );
}
