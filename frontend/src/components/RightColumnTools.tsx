'use client';

import { useState, useEffect } from 'react';

interface InvestmentData {
  income: number;
  state: string;
  zipCode: string;
  afterTaxIncome: number;
  recommendedInvestment: number;
  surplusPercentage: number;
  riskLevel: 'conservative' | 'moderate' | 'aggressive';
}

interface ChatMessage {
  id: string;
  sender: 'user' | 'ai';
  content: string;
  type?: 'text' | 'card';
  cardData?: any;
}

interface Subscription {
  id: string;
  name: string;
  logo?: string;
  initials: string;
  amount: number;
  frequency: 'monthly' | 'annual';
  nextCharge: string;
  isGrayCharge?: boolean;
  priceIncrease?: { old: number; new: number };
  status: 'active' | 'flagged' | 'dismissed';
}

export default function RightColumnTools() {
  const [showInvestmentModal, setShowInvestmentModal] = useState(false);
  const [investmentData, setInvestmentData] = useState<InvestmentData | null>(null);
  const [formData, setFormData] = useState({ income: '', state: '', zipCode: '' });
  const [gaugeProgress, setGaugeProgress] = useState(0);

  const [chatOpen, setChatOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: '1',
      sender: 'ai',
      content: "Hi! I'm your financial coach. Ask me anything about your spending, subscriptions, or transactions!",
      type: 'text',
    },
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);

  const [subscriptions, setSubscriptions] = useState<Subscription[]>([
    {
      id: '1',
      name: 'Netflix',
      initials: 'NF',
      amount: 22.99,
      frequency: 'monthly',
      nextCharge: 'Dec 15, 2025',
      priceIncrease: { old: 15.99, new: 22.99 },
      status: 'active',
    },
    {
      id: '2',
      name: 'Spotify Premium',
      initials: 'SP',
      amount: 10.99,
      frequency: 'monthly',
      nextCharge: 'Dec 8, 2025',
      status: 'active',
    },
    {
      id: '3',
      name: 'Adobe Creative Cloud',
      initials: 'AD',
      amount: 54.99,
      frequency: 'monthly',
      nextCharge: 'Dec 20, 2025',
      isGrayCharge: true,
      status: 'active',
    },
    {
      id: '4',
      name: 'Amazon Prime',
      initials: 'AM',
      amount: 14.99,
      frequency: 'monthly',
      nextCharge: 'Dec 12, 2025',
      status: 'active',
    },
    {
      id: '5',
      name: 'NYT Digital',
      initials: 'NY',
      amount: 17.00,
      frequency: 'monthly',
      nextCharge: 'Dec 18, 2025',
      status: 'active',
    },
    {
      id: '6',
      name: 'Gym Membership',
      initials: 'GM',
      amount: 45.00,
      frequency: 'monthly',
      nextCharge: 'Dec 1, 2025',
      isGrayCharge: true,
      status: 'active',
    },
  ]);

  const suggestedQuestions = [
    "What did I spend on Uber?",
    "Show my subscriptions",
    "Compare this month to last month",
    "What's my biggest expense?",
  ];

  const handleSubscriptionAction = (id: string, action: 'dismiss' | 'flag') => {
    setSubscriptions(subscriptions.map(sub =>
      sub.id === id ? { ...sub, status: action === 'dismiss' ? 'dismissed' : 'flagged' } : sub
    ));
  };

  const activeSubscriptions = subscriptions.filter(s => s.status === 'active');
  const flaggedSubscriptions = subscriptions.filter(s => s.status === 'flagged');
  const totalMonthlyCost = activeSubscriptions.reduce((sum, sub) => {
    const monthlyAmount = sub.frequency === 'annual' ? sub.amount / 12 : sub.amount;
    return sum + monthlyAmount;
  }, 0);

  // Animate gauge on data load
  useEffect(() => {
    if (investmentData && gaugeProgress < investmentData.surplusPercentage) {
      const timer = setTimeout(() => {
        setGaugeProgress((prev) => Math.min(prev + 2, investmentData.surplusPercentage));
      }, 20);
      return () => clearTimeout(timer);
    }
  }, [gaugeProgress, investmentData]);

  const calculateInvestment = () => {
    const income = parseFloat(formData.income);
    // Mock tax calculation (simplified)
    const taxRate = 0.25; // 25% effective tax rate
    const afterTax = income * (1 - taxRate);
    const monthlySpending = 4870; // From spending breakdown
    const surplus = afterTax - monthlySpending;
    const recommended = surplus * 0.7; // 70% of surplus
    const percentage = (recommended / surplus) * 100;

    const riskLevel: 'conservative' | 'moderate' | 'aggressive' =
      percentage < 50 ? 'conservative' : percentage < 75 ? 'moderate' : 'aggressive';

    const data: InvestmentData = {
      income,
      state: formData.state,
      zipCode: formData.zipCode,
      afterTaxIncome: afterTax,
      recommendedInvestment: recommended,
      surplusPercentage: percentage,
      riskLevel,
    };

    setInvestmentData(data);
    setShowInvestmentModal(false);
    setGaugeProgress(0);
  };

  const getGaugeColor = (level: string) => {
    switch (level) {
      case 'conservative':
        return '#10b981'; // green
      case 'moderate':
        return '#f59e0b'; // amber
      case 'aggressive':
        return '#ef4444'; // coral/red
      default:
        return '#6b7280';
    }
  };

  const handleSendMessage = (question?: string) => {
    const messageText = question || inputValue;
    if (!messageText.trim()) return;

    // Add user message
    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      sender: 'user',
      content: messageText,
      type: 'text',
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputValue('');
    setIsTyping(true);

    // Simulate AI response
    setTimeout(() => {
      const aiResponse = generateAIResponse(messageText);
      setMessages((prev) => [...prev, aiResponse]);
      setIsTyping(false);
    }, 1500);
  };

  const generateAIResponse = (question: string): ChatMessage => {
    const lowerQ = question.toLowerCase();

    if (lowerQ.includes('uber')) {
      return {
        id: Date.now().toString(),
        sender: 'ai',
        content: "Based on your transaction data, you spent $247 on Uber rides this month. That's 15% more than last month.",
        type: 'card',
        cardData: {
          type: 'spending',
          category: 'Uber',
          amount: 247,
          change: '+15%',
          transactions: 12,
        },
      };
    }

    if (lowerQ.includes('subscription')) {
      return {
        id: Date.now().toString(),
        sender: 'ai',
        content: "You have 5 active subscriptions totaling $87.95/month:",
        type: 'card',
        cardData: {
          type: 'subscriptions',
          subscriptions: [
            { name: 'Netflix', amount: 22.99 },
            { name: 'Spotify', amount: 10.99 },
            { name: 'Amazon Prime', amount: 14.99 },
            { name: 'NYT Digital', amount: 17.00 },
            { name: 'iCloud Storage', amount: 2.99 },
          ],
        },
      };
    }

    if (lowerQ.includes('compare') || lowerQ.includes('last month')) {
      return {
        id: Date.now().toString(),
        sender: 'ai',
        content: "Here's how this month compares to last month:",
        type: 'card',
        cardData: {
          type: 'comparison',
          thisMonth: 4870,
          lastMonth: 5240,
          change: -7.1,
        },
      };
    }

    if (lowerQ.includes('biggest expense') || lowerQ.includes('most')) {
      return {
        id: Date.now().toString(),
        sender: 'ai',
        content: "Your biggest expense this month was Housing at $1,850, which is 38% of your total spending.",
        type: 'text',
      };
    }

    return {
      id: Date.now().toString(),
      sender: 'ai',
      content: "I can help you analyze your spending, subscriptions, and transactions. Try asking about specific categories or comparing time periods!",
      type: 'text',
    };
  };

  const renderMessageCard = (cardData: any) => {
    if (cardData.type === 'spending') {
      return (
        <div className="bg-teal-50 rounded-lg p-4 border border-teal-200 mt-2">
          <div className="flex items-center justify-between mb-2">
            <span className="font-semibold text-gray-900">{cardData.category}</span>
            <span className={`text-sm font-medium ${cardData.change.startsWith('+') ? 'text-red-600' : 'text-green-600'}`}>
              {cardData.change}
            </span>
          </div>
          <div className="text-2xl font-bold text-teal-600">${cardData.amount}</div>
          <div className="text-sm text-gray-600 mt-1">{cardData.transactions} transactions</div>
        </div>
      );
    }

    if (cardData.type === 'subscriptions') {
      return (
        <div className="bg-purple-50 rounded-lg p-4 border border-purple-200 mt-2 space-y-2">
          {cardData.subscriptions.map((sub: any, index: number) => (
            <div key={index} className="flex items-center justify-between">
              <span className="text-gray-900">{sub.name}</span>
              <span className="font-semibold text-purple-600">${sub.amount}</span>
            </div>
          ))}
          <div className="pt-2 border-t border-purple-300 flex items-center justify-between">
            <span className="font-semibold text-gray-900">Total</span>
            <span className="font-bold text-purple-600">
              ${cardData.subscriptions.reduce((sum: number, s: any) => sum + s.amount, 0).toFixed(2)}
            </span>
          </div>
        </div>
      );
    }

    if (cardData.type === 'comparison') {
      return (
        <div className="bg-blue-50 rounded-lg p-4 border border-blue-200 mt-2">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <div className="text-sm text-gray-600">This Month</div>
              <div className="text-xl font-bold text-gray-900">${cardData.thisMonth.toLocaleString()}</div>
            </div>
            <div>
              <div className="text-sm text-gray-600">Last Month</div>
              <div className="text-xl font-bold text-gray-900">${cardData.lastMonth.toLocaleString()}</div>
            </div>
          </div>
          <div className="mt-3 pt-3 border-t border-blue-300">
            <span className={`text-lg font-semibold ${cardData.change < 0 ? 'text-green-600' : 'text-red-600'}`}>
              {cardData.change > 0 ? '+' : ''}{cardData.change.toFixed(1)}% {cardData.change < 0 ? 'saved' : 'more'}
            </span>
          </div>
        </div>
      );
    }

    return null;
  };

  return (
    <aside className="w-80 bg-gray-50 border-l border-gray-200 p-6 overflow-y-auto">
      <h3 className="text-lg font-bold text-gray-900 mb-4 text-center">Tools & Insights</h3>

      {/* Investment Capacity Predictor */}
      <div className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm mb-6">
        <h4 className="font-bold text-gray-900 mb-4 flex items-center gap-2">
          <span>📊</span> Investment Predictor
        </h4>

        {!investmentData ? (
          <button
            onClick={() => setShowInvestmentModal(true)}
            className="w-full bg-teal-500 text-white py-3 rounded-lg font-medium hover:bg-teal-600 transition-colors"
          >
            Calculate Capacity
          </button>
        ) : (
          <div className="space-y-4">
            {/* After-tax income */}
            <div>
              <p className="text-xs text-gray-600 mb-1">After-Tax Income</p>
              <p className="text-lg font-semibold text-gray-900">
                ${investmentData.afterTaxIncome.toLocaleString()}
              </p>
            </div>

            {/* Spending Volatility Waveform */}
            <div>
              <p className="text-xs text-gray-600 mb-2">Spending Volatility</p>
              <svg width="100%" height="30" viewBox="0 0 200 30">
                <path
                  d="M0,15 Q25,5 50,15 T100,15 T150,15 T200,15"
                  stroke="#14b8a6"
                  strokeWidth="2"
                  fill="none"
                  className="animate-pulse"
                />
              </svg>
            </div>

            {/* Recommended Investment */}
            <div className="bg-gradient-to-br from-teal-50 to-cyan-50 rounded-lg p-4 border border-teal-200">
              <p className="text-sm text-gray-700 mb-2">Recommended Safe Investment</p>
              <p className="text-3xl font-bold text-teal-600">
                ${Math.round(investmentData.recommendedInvestment).toLocaleString()}
              </p>
              <p className="text-xs text-gray-600 mt-1">per month</p>
            </div>

            {/* Circular Gauge */}
            <div className="flex flex-col items-center">
              <div className="relative w-32 h-32">
                <svg className="transform -rotate-90" width="128" height="128">
                  <circle
                    cx="64"
                    cy="64"
                    r="56"
                    stroke="#e5e7eb"
                    strokeWidth="8"
                    fill="none"
                  />
                  <circle
                    cx="64"
                    cy="64"
                    r="56"
                    stroke={getGaugeColor(investmentData.riskLevel)}
                    strokeWidth="8"
                    fill="none"
                    strokeDasharray={`${2 * Math.PI * 56}`}
                    strokeDashoffset={`${2 * Math.PI * 56 * (1 - gaugeProgress / 100)}`}
                    className="transition-all duration-300"
                    strokeLinecap="round"
                  />
                </svg>
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                  <span className="text-2xl font-bold text-gray-900">{Math.round(gaugeProgress)}%</span>
                  <span className="text-xs text-gray-600">of surplus</span>
                </div>
              </div>
              <p className="text-sm font-medium text-gray-700 mt-3 capitalize">
                {investmentData.riskLevel} Risk
              </p>
            </div>

            <button
              onClick={() => setInvestmentData(null)}
              className="w-full text-sm text-teal-600 hover:text-teal-700 font-medium"
            >
              Recalculate
            </button>
          </div>
        )}
      </div>

      {/* Subscription Manager */}
      <div className="bg-white rounded-xl p-4 border border-gray-200 shadow-sm">
        <h4 className="font-bold text-gray-900 mb-3 flex items-center gap-2">
          <span>💳</span> Subscriptions
        </h4>

        {/* Summary Banner */}
        <div className="bg-gradient-to-r from-purple-50 to-pink-50 rounded-lg p-3 mb-4 border border-purple-200">
          <p className="text-xs text-gray-600 mb-1">Total Monthly Cost</p>
          <p className="text-2xl font-bold text-purple-600">
            ${totalMonthlyCost.toFixed(2)}
          </p>
          <p className="text-xs text-gray-500 mt-1">
            {activeSubscriptions.length} active subscription{activeSubscriptions.length !== 1 ? 's' : ''}
          </p>
        </div>

        {/* Active Subscriptions */}
        <div className="space-y-2 mb-4 max-h-96 overflow-y-auto">
          {activeSubscriptions.map((sub) => (
            <div
              key={sub.id}
              className={`relative bg-gray-50 rounded-lg p-3 border transition-all ${
                sub.isGrayCharge ? 'border-amber-400 bg-amber-50/50' : 'border-gray-200'
              }`}
            >
              {/* Warning Badge */}
              {sub.isGrayCharge && (
                <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-amber-500 text-white text-[10px] px-2 py-0.5 rounded-full font-medium shadow-sm animate-pulse-subtle whitespace-nowrap">
                  ⚠️ Gray
                </div>
              )}

              <div className="flex items-start gap-3">
                {/* Logo/Initials */}
                <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-pink-500 rounded-lg flex items-center justify-center text-white font-bold text-sm flex-shrink-0">
                  {sub.initials}
                </div>

                <div className="flex-1 min-w-0">
                  {/* Name and Amount */}
                  <div className="flex items-start justify-between mb-1">
                    <h5 className="font-semibold text-gray-900 text-sm truncate">{sub.name}</h5>
                    <div className="flex items-center gap-1">
                      {sub.priceIncrease && (
                        <div className="group relative">
                          <svg className="w-4 h-4 text-red-500" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M5.293 7.707a1 1 0 010-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 01-1.414 1.414L11 5.414V17a1 1 0 11-2 0V5.414L6.707 7.707a1 1 0 01-1.414 0z" clipRule="evenodd" />
                          </svg>
                          {/* Tooltip */}
                          <div className="absolute bottom-full right-0 mb-2 hidden group-hover:block w-32 bg-gray-900 text-white text-xs rounded px-2 py-1 z-10">
                            Was ${sub.priceIncrease.old}, now ${sub.priceIncrease.new}
                          </div>
                        </div>
                      )}
                      <span className="font-bold text-gray-900 text-sm">${sub.amount}</span>
                    </div>
                  </div>

                  {/* Frequency and Next Charge */}
                  <div className="flex items-center gap-2 text-xs text-gray-600 mb-2">
                    <span className="capitalize">{sub.frequency}</span>
                    <span>•</span>
                    <span>Next: {sub.nextCharge}</span>
                  </div>

                  {/* Actions */}
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleSubscriptionAction(sub.id, 'dismiss')}
                      className="flex-1 text-xs py-1 px-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300 transition-colors"
                    >
                      Dismiss
                    </button>
                    <button
                      onClick={() => handleSubscriptionAction(sub.id, 'flag')}
                      className="flex-1 text-xs py-1 px-2 bg-red-100 text-red-700 rounded hover:bg-red-200 transition-colors"
                    >
                      Flag for Cancellation
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* To Cancel Section */}
        {flaggedSubscriptions.length > 0 && (
          <div className="border-t border-gray-200 pt-4">
            <h5 className="text-sm font-semibold text-gray-900 mb-3">
              To Cancel ({flaggedSubscriptions.length})
            </h5>
            <div className="space-y-2">
              {flaggedSubscriptions.map((sub) => (
                <div
                  key={sub.id}
                  className="bg-red-50 rounded-lg p-3 border border-red-200 opacity-75"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 bg-gray-400 rounded-lg flex items-center justify-center text-white font-bold text-xs flex-shrink-0">
                      {sub.initials}
                    </div>
                    <div className="flex-1">
                      <p className="font-semibold text-gray-900 text-sm line-through">
                        {sub.name}
                      </p>
                      <p className="text-xs text-gray-600">
                        ${sub.amount}/{sub.frequency === 'monthly' ? 'mo' : 'yr'}
                      </p>
                    </div>
                    <button
                      onClick={() => setSubscriptions(subscriptions.map(s =>
                        s.id === sub.id ? { ...s, status: 'active' } : s
                      ))}
                      className="text-xs text-red-600 hover:text-red-700 font-medium"
                    >
                      Undo
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Investment Modal */}
      {showInvestmentModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl p-6 w-full max-w-md shadow-2xl animate-slide-up">
            <h3 className="text-2xl font-bold text-gray-900 mb-4">Investment Calculator</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Monthly Income</label>
                <input
                  type="number"
                  value={formData.income}
                  onChange={(e) => setFormData({ ...formData, income: e.target.value })}
                  placeholder="e.g., 8000"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-400"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">State</label>
                <input
                  type="text"
                  value={formData.state}
                  onChange={(e) => setFormData({ ...formData, state: e.target.value })}
                  placeholder="e.g., CA"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-400"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Zip Code</label>
                <input
                  type="text"
                  value={formData.zipCode}
                  onChange={(e) => setFormData({ ...formData, zipCode: e.target.value })}
                  placeholder="e.g., 90210"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-400"
                />
              </div>
            </div>
            <div className="flex gap-3 mt-6">
              <button
                onClick={() => setShowInvestmentModal(false)}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors font-medium"
              >
                Cancel
              </button>
              <button
                onClick={calculateInvestment}
                disabled={!formData.income || !formData.state || !formData.zipCode}
                className="flex-1 px-4 py-2 bg-teal-500 text-white rounded-lg hover:bg-teal-600 transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Calculate
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Chat Bubble */}
      {!chatOpen && (
        <button
          onClick={() => setChatOpen(true)}
          className="fixed bottom-6 right-6 bg-gradient-to-r from-teal-500 to-cyan-500 text-white p-4 rounded-full shadow-2xl hover:scale-110 transition-transform animate-bounce-subtle z-40"
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
          </svg>
        </button>
      )}

      {/* Chat Drawer */}
      {chatOpen && (
        <div className="fixed inset-y-0 right-0 w-96 bg-white shadow-2xl z-50 flex flex-col animate-slide-in-right">
          {/* Header */}
          <div className="bg-gradient-to-r from-teal-500 to-cyan-500 text-white p-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-white/20 rounded-full flex items-center justify-center">
                🤖
              </div>
              <div>
                <h3 className="font-bold">Financial Coach</h3>
                <p className="text-xs text-white/80">Ask me anything!</p>
              </div>
            </div>
            <button
              onClick={() => setChatOpen(false)}
              className="text-white hover:bg-white/20 rounded-full p-2 transition-colors"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                    message.sender === 'user'
                      ? 'bg-teal-500 text-white'
                      : 'bg-gray-200 text-gray-900'
                  }`}
                >
                  <p className="text-sm">{message.content}</p>
                  {message.type === 'card' && message.cardData && renderMessageCard(message.cardData)}
                </div>
              </div>
            ))}

            {isTyping && (
              <div className="flex justify-start">
                <div className="bg-gray-200 rounded-2xl px-4 py-3">
                  <div className="flex gap-1">
                    <div className="w-2 h-2 bg-gray-600 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                    <div className="w-2 h-2 bg-gray-600 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                    <div className="w-2 h-2 bg-gray-600 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Suggested Questions */}
          <div className="px-4 py-2 border-t border-gray-200 overflow-x-auto">
            <div className="flex gap-2">
              {suggestedQuestions.map((question, index) => (
                <button
                  key={index}
                  onClick={() => handleSendMessage(question)}
                  className="px-3 py-2 bg-teal-50 text-teal-700 rounded-full text-xs font-medium hover:bg-teal-100 transition-colors whitespace-nowrap"
                >
                  {question}
                </button>
              ))}
            </div>
          </div>

          {/* Input */}
          <div className="p-4 border-t border-gray-200">
            <div className="flex gap-2">
              <input
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                placeholder="Ask a question..."
                className="flex-1 px-4 py-2 border border-gray-300 rounded-full focus:outline-none focus:ring-2 focus:ring-teal-400"
              />
              <button
                onClick={() => handleSendMessage()}
                className="bg-teal-500 text-white p-2 rounded-full hover:bg-teal-600 transition-colors"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      )}

      <style jsx>{`
        @keyframes bounce-subtle {
          0%, 100% {
            transform: translateY(0);
          }
          50% {
            transform: translateY(-5px);
          }
        }

        @keyframes slide-in-right {
          from {
            transform: translateX(100%);
          }
          to {
            transform: translateX(0);
          }
        }

        @keyframes slide-up {
          from {
            opacity: 0;
            transform: translateY(20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        .animate-bounce-subtle {
          animation: bounce-subtle 2s ease-in-out infinite;
        }

        .animate-slide-in-right {
          animation: slide-in-right 0.4s cubic-bezier(0.68, -0.55, 0.265, 1.55);
        }

        .animate-slide-up {
          animation: slide-up 0.4s ease-out;
        }
      `}</style>
    </aside>
  );
}
