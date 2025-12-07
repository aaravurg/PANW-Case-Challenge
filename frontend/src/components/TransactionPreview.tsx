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
  const [searchQuery, setSearchQuery] = useState('');
  const [filterCategory, setFilterCategory] = useState<string>('all');

  // Fetch and parse CSV data
  useEffect(() => {
    const fetchTransactions = async () => {
      try {
        const response = await fetch(`/sample_transactions_1000_sorted.csv?t=${Date.now()}`);
        const text = await response.text();
        const lines = text.trim().split('\n');

        const parsedTransactions = lines.slice(1).map((line) => {
          // More robust CSV parsing
          const regex = /,(?=(?:[^"]*"[^"]*")*[^"]*$)/;
          const values = line.split(regex).map(val => {
            if (val.startsWith('"') && val.endsWith('"')) {
              return val.slice(1, -1).replace(/""/g, '"');
            }
            return val;
          });

          // Parse category
          let category: string[];
          try {
            category = JSON.parse(values[4]);
          } catch {
            category = [values[4]];
          }

          return {
            transaction_id: values[0],
            date: values[1],
            amount: parseFloat(values[2]),
            merchant_name: values[3],
            category,
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
  const totalIncome = transactions.reduce((sum, tx) => sum + (tx.amount > 0 ? tx.amount : 0), 0);
  const uniqueMerchants = new Set(transactions.map((tx) => tx.merchant_name)).size;

  // Get unique categories
  const allCategories = new Set<string>();
  transactions.forEach(tx => {
    if (tx.category && tx.category[0]) {
      allCategories.add(tx.category[0]);
    }
  });
  const categories = Array.from(allCategories).sort();

  // Filter transactions
  const filteredTransactions = transactions.filter(tx => {
    const matchesSearch = searchQuery === '' ||
      tx.merchant_name.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory = filterCategory === 'all' || tx.category[0] === filterCategory;
    return matchesSearch && matchesCategory;
  });

  // Generate color for category badge
  const getCategoryColor = (category: string) => {
    const colors: { [key: string]: string } = {
      'Gas': 'bg-amber-100 text-amber-800 border-amber-200',
      'Groceries': 'bg-green-100 text-green-800 border-green-200',
      'Restaurants': 'bg-orange-100 text-orange-800 border-orange-200',
      'Shopping': 'bg-purple-100 text-purple-800 border-purple-200',
      'Travel': 'bg-blue-100 text-blue-800 border-blue-200',
      'Entertainment': 'bg-pink-100 text-pink-800 border-pink-200',
      'Income': 'bg-emerald-100 text-emerald-800 border-emerald-200',
      'Cloud': 'bg-cyan-100 text-cyan-800 border-cyan-200',
      'News': 'bg-slate-100 text-slate-800 border-slate-200',
    };
    return colors[category] || 'bg-gray-100 text-gray-800 border-gray-200';
  };

  // Generate color for merchant initial
  const getMerchantColor = (name: string) => {
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
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(Math.abs(amount));
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-16">
        <div className="relative w-16 h-16">
          <div className="absolute inset-0 border-4 border-gray-200 rounded-full"></div>
          <div className="absolute inset-0 border-4 border-transparent border-t-teal-500 rounded-full animate-spin"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Statistics Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <div className="bg-gradient-to-br from-teal-50 to-teal-100 rounded-xl p-4 border border-teal-200">
          <p className="text-teal-600 text-sm font-medium mb-1">Total Transactions</p>
          <p className="text-3xl font-bold text-teal-900">{totalTransactions.toLocaleString()}</p>
        </div>
        <div className="bg-gradient-to-br from-red-50 to-red-100 rounded-xl p-4 border border-red-200">
          <p className="text-red-600 text-sm font-medium mb-1">Total Spending</p>
          <p className="text-3xl font-bold text-red-900">
            ${totalSpending.toLocaleString(undefined, { maximumFractionDigits: 0 })}
          </p>
        </div>
        <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-xl p-4 border border-green-200">
          <p className="text-green-600 text-sm font-medium mb-1">Total Income</p>
          <p className="text-3xl font-bold text-green-900">
            ${totalIncome.toLocaleString(undefined, { maximumFractionDigits: 0 })}
          </p>
        </div>
        <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-xl p-4 border border-purple-200">
          <p className="text-purple-600 text-sm font-medium mb-1">Unique Merchants</p>
          <p className="text-3xl font-bold text-purple-900">{uniqueMerchants.toLocaleString()}</p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3 mb-4">
        <div className="flex-1">
          <input
            type="text"
            placeholder="Search by merchant name..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent"
          />
        </div>
        <select
          value={filterCategory}
          onChange={(e) => setFilterCategory(e.target.value)}
          className="px-4 py-2.5 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent bg-white"
        >
          <option value="all">All Categories</option>
          {categories.map(cat => (
            <option key={cat} value={cat}>{cat}</option>
          ))}
        </select>
      </div>

      {/* Results count */}
      <div className="mb-3">
        <p className="text-sm text-gray-600">
          Showing <span className="font-semibold text-gray-900">{filteredTransactions.length}</span> of <span className="font-semibold text-gray-900">{totalTransactions}</span> transactions
        </p>
      </div>

      {/* Transaction Table */}
      <div className="flex-1 overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
        <div className="overflow-x-auto overflow-y-auto h-full">
          <table className="w-full">
            <thead className="sticky top-0 bg-gray-50 border-b border-gray-200 z-10">
              <tr>
                <th className="text-left py-3 px-4 text-gray-700 font-semibold text-sm">Date</th>
                <th className="text-left py-3 px-4 text-gray-700 font-semibold text-sm">Merchant</th>
                <th className="text-left py-3 px-4 text-gray-700 font-semibold text-sm">Category</th>
                <th className="text-left py-3 px-4 text-gray-700 font-semibold text-sm">Channel</th>
                <th className="text-right py-3 px-4 text-gray-700 font-semibold text-sm">Amount</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {filteredTransactions.length === 0 ? (
                <tr>
                  <td colSpan={5} className="py-12 text-center text-gray-500">
                    No transactions found matching your filters
                  </td>
                </tr>
              ) : (
                filteredTransactions.map((tx) => (
                  <tr
                    key={tx.transaction_id}
                    className="hover:bg-gray-50 transition-colors"
                  >
                    <td className="py-3 px-4 text-gray-900 text-sm whitespace-nowrap">
                      {new Date(tx.date).toLocaleDateString('en-US', {
                        month: 'short',
                        day: 'numeric',
                        year: 'numeric',
                      })}
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-3">
                        <div
                          className={`w-8 h-8 rounded-full ${getMerchantColor(tx.merchant_name)} flex items-center justify-center text-white font-bold text-xs flex-shrink-0`}
                        >
                          {tx.merchant_name.charAt(0).toUpperCase()}
                        </div>
                        <span className="text-gray-900 text-sm font-medium">{tx.merchant_name}</span>
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <span className={`inline-block px-2.5 py-1 rounded-full text-xs font-medium border ${getCategoryColor(tx.category[0])}`}>
                        {tx.category[0]}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <span className="text-gray-600 text-sm capitalize">{tx.payment_channel}</span>
                    </td>
                    <td className={`py-3 px-4 text-right text-sm font-semibold whitespace-nowrap ${tx.amount >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {tx.amount >= 0 ? '+' : '-'}{formatCurrency(tx.amount)}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Continue Button */}
      {showContinueButton && (
        <button
          onClick={onContinue}
          className="mt-6 w-full bg-gradient-to-r from-teal-500 to-cyan-500 text-white py-3 rounded-xl font-semibold text-base shadow-lg hover:shadow-xl hover:scale-[1.01] transition-all duration-200"
        >
          Continue to Dashboard
        </button>
      )}
    </div>
  );
}
