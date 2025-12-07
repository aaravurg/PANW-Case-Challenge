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

interface PriceIncrease {
  old_price: number;
  new_price: number;
  percent_change: number;
  detected_date: string;
}

interface SubscriptionCharge {
  date: string;
  amount: number;
}

interface Subscription {
  merchant_name: string;
  original_merchant_name: string;
  frequency: string;
  frequency_days: number;
  current_amount: number;
  average_amount: number;
  min_amount: number;
  max_amount: number;
  first_charge_date: string;
  last_charge_date: string;
  next_predicted_date: string | null;
  transaction_count: number;
  charges: SubscriptionCharge[];
  monthly_cost: number;
  annual_cost: number;
  confidence_score: number;
  interval_regularity: number;
  amount_consistency: number;
  is_gray_charge: boolean;
  has_price_increase: boolean;
  is_trial_conversion: boolean;
  needs_attention: boolean;
  price_increase: PriceIncrease | null;
  // UI state
  status?: 'active' | 'flagged' | 'dismissed';
}

interface SubscriptionSummary {
  total_subscriptions: number;
  total_monthly_cost: number;
  total_annual_cost: number;
  gray_charges_count: number;
  price_increases_count: number;
  trial_conversions_count: number;
  subscriptions: Subscription[];
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

  const [subscriptionSummary, setSubscriptionSummary] = useState<SubscriptionSummary | null>(null);
  const [subscriptions, setSubscriptions] = useState<Subscription[]>([]);
  const [loadingSubscriptions, setLoadingSubscriptions] = useState(true);

  // Fetch subscriptions from API
  useEffect(() => {
    const fetchSubscriptions = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/subscriptions');
        const data: SubscriptionSummary = await response.json();
        setSubscriptionSummary(data);
        // Add status field for UI management
        setSubscriptions(data.subscriptions.map(sub => ({ ...sub, status: 'active' as const })));
        setLoadingSubscriptions(false);
      } catch (error) {
        console.error('Error fetching subscriptions:', error);
        setLoadingSubscriptions(false);
      }
    };

    fetchSubscriptions();
  }, []);

  const suggestedQuestions = [
    "What did I spend on Uber?",
    "Show my subscriptions",
    "Compare this month to last month",
    "What's my biggest expense?",
  ];

  const handleSubscriptionAction = (merchantName: string, action: 'dismiss' | 'flag') => {
    setSubscriptions(subscriptions.map(sub =>
      sub.merchant_name === merchantName ? { ...sub, status: action === 'dismiss' ? 'dismissed' : 'flagged' } : sub
    ));
  };

  const activeSubscriptions = subscriptions.filter(s => s.status === 'active');
  const flaggedSubscriptions = subscriptions.filter(s => s.status === 'flagged');
  const totalMonthlyCost = subscriptionSummary?.total_monthly_cost || 0;

  // Helper function to get initials from merchant name
  const getInitials = (name: string) => {
    const words = name.split(' ');
    if (words.length >= 2) {
      return (words[0][0] + words[1][0]).toUpperCase();
    }
    return name.substring(0, 2).toUpperCase();
  };

  // Helper function to format date
  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'Unknown';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  };

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
    <aside className="w-96 bg-gray-50 border-l border-gray-200 p-6 overflow-y-auto">
      <h3 className="text-lg font-bold text-gray-900 mb-6 text-center">Tools & Insights</h3>

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
          <span>💳</span> Recurring Charges
        </h4>

        {loadingSubscriptions ? (
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600"></div>
          </div>
        ) : (
          <>
            {/* Summary Banner */}
            <div className="bg-gradient-to-br from-purple-50 via-pink-50 to-purple-50 rounded-xl p-5 mb-6 border-2 border-purple-200 shadow-sm">
              <div className="flex items-start justify-between mb-3">
                <div className="flex-1">
                  <p className="text-sm font-semibold text-gray-700 mb-1">Total Monthly Cost</p>
                  <p className="text-3xl font-bold text-purple-600 mb-1">
                    ${totalMonthlyCost.toFixed(2)}
                  </p>
                  <p className="text-xs text-gray-500">
                    ${(totalMonthlyCost * 12).toLocaleString()}/year
                  </p>
                </div>
                {subscriptionSummary && (
                  <div className="bg-white rounded-lg px-3 py-2 border border-purple-200">
                    <p className="text-xs text-gray-500 mb-0.5">Detected</p>
                    <p className="text-xl font-bold text-purple-600">{subscriptionSummary.total_subscriptions}</p>
                  </div>
                )}
              </div>

              {/* Status badges */}
              {subscriptionSummary && (subscriptionSummary.gray_charges_count > 0 || subscriptionSummary.price_increases_count > 0 || subscriptionSummary.trial_conversions_count > 0) && (
                <div className="flex flex-wrap gap-2 pt-3 border-t border-purple-200">
                  {subscriptionSummary.gray_charges_count > 0 && (
                    <span className="text-xs bg-amber-100 text-amber-700 px-3 py-1.5 rounded-lg font-semibold border border-amber-300">
                      ⚠️ {subscriptionSummary.gray_charges_count} Gray Charge{subscriptionSummary.gray_charges_count > 1 ? 's' : ''}
                    </span>
                  )}
                  {subscriptionSummary.price_increases_count > 0 && (
                    <span className="text-xs bg-red-100 text-red-700 px-3 py-1.5 rounded-lg font-semibold border border-red-300">
                      ↑ {subscriptionSummary.price_increases_count} Price Increase{subscriptionSummary.price_increases_count > 1 ? 's' : ''}
                    </span>
                  )}
                  {subscriptionSummary.trial_conversions_count > 0 && (
                    <span className="text-xs bg-blue-100 text-blue-700 px-3 py-1.5 rounded-lg font-semibold border border-blue-300">
                      🆕 {subscriptionSummary.trial_conversions_count} New Trial{subscriptionSummary.trial_conversions_count > 1 ? 's' : ''}
                    </span>
                  )}
                </div>
              )}

              <div className="flex items-center gap-2 mt-3 text-xs text-gray-600">
                <span className="flex items-center gap-1">
                  <div className="w-2 h-2 rounded-full bg-green-500"></div>
                  {activeSubscriptions.length} Active
                </span>
                {flaggedSubscriptions.length > 0 && (
                  <>
                    <span>•</span>
                    <span className="flex items-center gap-1">
                      <div className="w-2 h-2 rounded-full bg-red-500"></div>
                      {flaggedSubscriptions.length} To Cancel
                    </span>
                  </>
                )}
              </div>
            </div>
          </>
        )}

        {/* Active Subscriptions */}
        {!loadingSubscriptions && (
          <div className="space-y-3 mb-6">
            {activeSubscriptions.map((sub) => (
              <div
                key={sub.merchant_name}
                className={`relative bg-gray-50 rounded-xl p-4 border transition-all ${
                  sub.is_gray_charge ? 'border-amber-400 bg-amber-50/50' :
                  sub.is_trial_conversion ? 'border-blue-400 bg-blue-50/50' :
                  sub.has_price_increase ? 'border-red-300 bg-red-50/30' :
                  'border-gray-200'
                }`}
              >
                {/* Warning/Status Badges */}
                <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1/2 flex gap-1">
                  {sub.is_gray_charge && (
                    <div className="bg-amber-500 text-white text-[10px] px-2 py-0.5 rounded-full font-medium shadow-sm animate-pulse-subtle whitespace-nowrap">
                      ⚠️ Gray Charge
                    </div>
                  )}
                  {sub.is_trial_conversion && (
                    <div className="bg-blue-500 text-white text-[10px] px-2 py-0.5 rounded-full font-medium shadow-sm whitespace-nowrap">
                      🆕 New Trial
                    </div>
                  )}
                </div>

                <div className="flex items-start gap-4">
                  {/* Logo/Initials */}
                  <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-pink-500 rounded-xl flex items-center justify-center text-white font-bold text-base flex-shrink-0 shadow-md">
                    {getInitials(sub.merchant_name)}
                  </div>

                  <div className="flex-1 min-w-0">
                    {/* Name and Amount */}
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex-1 min-w-0">
                        <h5 className="font-bold text-gray-900 text-base truncate capitalize mb-1">
                          {sub.original_merchant_name}
                        </h5>
                        <div className="flex items-center gap-1.5">
                          <div className="w-full bg-gray-200 rounded-full h-1.5">
                            <div
                              className="bg-gradient-to-r from-green-500 to-emerald-500 h-1.5 rounded-full transition-all duration-500"
                              style={{ width: `${sub.confidence_score}%` }}
                            ></div>
                          </div>
                          <span className="text-xs text-gray-600 font-medium whitespace-nowrap">
                            {sub.confidence_score.toFixed(0)}%
                          </span>
                        </div>
                      </div>
                      <div className="flex items-center gap-1.5 ml-3">
                        {sub.has_price_increase && sub.price_increase && (
                          <div className="group relative">
                            <svg className="w-5 h-5 text-red-500" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M5.293 7.707a1 1 0 010-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 01-1.414 1.414L11 5.414V17a1 1 0 11-2 0V5.414L6.707 7.707a1 1 0 01-1.414 0z" clipRule="evenodd" />
                            </svg>
                            {/* Tooltip */}
                            <div className="absolute bottom-full right-0 mb-2 hidden group-hover:block w-48 bg-gray-900 text-white text-xs rounded-lg px-3 py-2 z-10 shadow-xl">
                              <div className="font-semibold mb-1">Price Increased</div>
                              <div>${sub.price_increase.old_price} → ${sub.price_increase.new_price} (+{sub.price_increase.percent_change.toFixed(1)}%)</div>
                            </div>
                          </div>
                        )}
                        <span className="font-bold text-purple-600 text-lg">${sub.monthly_cost.toFixed(2)}</span>
                        <span className="text-xs text-gray-500 font-medium">/mo</span>
                      </div>
                    </div>

                    {/* Frequency and Details */}
                    <div className="flex items-center gap-2 text-sm text-gray-600 mb-3">
                      <span className="capitalize font-medium">{sub.frequency}</span>
                      <span>•</span>
                      <span>{sub.transaction_count} charges</span>
                      <span>•</span>
                      <span className="text-xs">Next: {formatDate(sub.next_predicted_date)}</span>
                    </div>

                    {/* Actions */}
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleSubscriptionAction(sub.merchant_name, 'dismiss')}
                        className="flex-1 text-sm py-2 px-3 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors font-medium"
                      >
                        Dismiss
                      </button>
                      <button
                        onClick={() => handleSubscriptionAction(sub.merchant_name, 'flag')}
                        className="flex-1 text-sm py-2 px-3 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 transition-colors font-medium"
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* To Cancel Section */}
        {flaggedSubscriptions.length > 0 && (
          <div className="border-t border-gray-200 pt-6 mt-6">
            <div className="flex items-center justify-between mb-4">
              <h5 className="text-base font-bold text-gray-900">
                Marked for Cancellation
              </h5>
              <span className="bg-red-100 text-red-700 text-xs font-bold px-2.5 py-1 rounded-full">
                {flaggedSubscriptions.length}
              </span>
            </div>
            <div className="space-y-3">
              {flaggedSubscriptions.map((sub) => (
                <div
                  key={sub.merchant_name}
                  className="bg-red-50 rounded-xl p-4 border border-red-200"
                >
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 bg-gray-400 rounded-xl flex items-center justify-center text-white font-bold text-sm flex-shrink-0 opacity-50">
                      {getInitials(sub.merchant_name)}
                    </div>
                    <div className="flex-1">
                      <p className="font-bold text-gray-900 text-base line-through capitalize mb-1">
                        {sub.original_merchant_name}
                      </p>
                      <div className="flex items-center gap-2 text-sm text-gray-600">
                        <span className="font-semibold">${sub.monthly_cost.toFixed(2)}/mo</span>
                        <span>•</span>
                        <span className="capitalize">{sub.frequency}</span>
                      </div>
                    </div>
                    <button
                      onClick={() => setSubscriptions(subscriptions.map(s =>
                        s.merchant_name === sub.merchant_name ? { ...s, status: 'active' } : s
                      ))}
                      className="text-sm text-red-600 hover:text-red-700 font-semibold px-3 py-2 hover:bg-red-100 rounded-lg transition-colors"
                    >
                      Undo
                    </button>
                  </div>
                </div>
              ))}
              <div className="bg-green-50 border border-green-200 rounded-xl p-4 mt-4">
                <p className="text-sm font-semibold text-green-800 mb-1">
                  💰 Potential Monthly Savings
                </p>
                <p className="text-2xl font-bold text-green-600">
                  ${flaggedSubscriptions.reduce((sum, s) => sum + s.monthly_cost, 0).toFixed(2)}
                </p>
                <p className="text-xs text-green-700 mt-1">
                  ${(flaggedSubscriptions.reduce((sum, s) => sum + s.monthly_cost, 0) * 12).toFixed(2)}/year if cancelled
                </p>
              </div>
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
