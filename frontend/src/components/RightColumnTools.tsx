'use client';

import { useState, useEffect } from 'react';

interface InvestmentOption {
  name: string;
  risk_level: string;
  typical_returns: string;
  accessibility: string;
  best_for: string;
  description: string;
}

interface InvestmentBreakdown {
  monthly_income: number;
  take_home_income: number;
  average_monthly_spending: number;
  total_goal_commitments: number;
  investable_surplus: number;
}

interface InvestmentCapacityResponse {
  breakdown: InvestmentBreakdown;
  investment_options: InvestmentOption[];
  calculation_period: string;
  active_goals_count: number;
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
  const [investmentData, setInvestmentData] = useState<InvestmentCapacityResponse | null>(null);
  const [formData, setFormData] = useState({ income: '', isGross: true });
  const [isCalculating, setIsCalculating] = useState(false);
  const [expandedOption, setExpandedOption] = useState<number | null>(null);

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

  const calculateInvestment = async () => {
    const income = parseFloat(formData.income);
    if (isNaN(income) || income <= 0) {
      alert('Please enter a valid income amount');
      return;
    }

    setIsCalculating(true);
    try {
      const response = await fetch('http://localhost:8000/api/investment-capacity', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          monthly_income: income,
          is_gross_income: formData.isGross,
          user_id: 'default_user',
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to calculate investment capacity');
      }

      const data: InvestmentCapacityResponse = await response.json();
      setInvestmentData(data);
      setShowInvestmentModal(false);
    } catch (error) {
      console.error('Error calculating investment capacity:', error);
      alert('Failed to calculate investment capacity. Please try again.');
    } finally {
      setIsCalculating(false);
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
          <span>📊</span> Investment Capacity
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
            {/* Visual Breakdown - Waterfall */}
            <div className="space-y-3">
              {/* Monthly Income */}
              <div className="bg-gradient-to-r from-blue-50 to-blue-100 rounded-lg p-3 border border-blue-200">
                <p className="text-xs text-blue-700 font-medium">Monthly Income</p>
                <p className="text-2xl font-bold text-blue-900">
                  ${investmentData.breakdown.monthly_income.toLocaleString()}
                </p>
              </div>

              {/* Arrow down */}
              <div className="flex justify-center">
                <svg className="w-6 h-6 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 3a1 1 0 011 1v10.586l2.293-2.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 111.414-1.414L9 14.586V4a1 1 0 011-1z" clipRule="evenodd" />
                </svg>
              </div>

              {/* Take-Home Income (if different) */}
              {investmentData.breakdown.monthly_income !== investmentData.breakdown.take_home_income && (
                <>
                  <div className="bg-gradient-to-r from-green-50 to-green-100 rounded-lg p-3 border border-green-200">
                    <p className="text-xs text-green-700 font-medium">After-Tax Income (75%)</p>
                    <p className="text-2xl font-bold text-green-900">
                      ${investmentData.breakdown.take_home_income.toLocaleString()}
                    </p>
                  </div>
                  <div className="flex justify-center">
                    <svg className="w-6 h-6 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 3a1 1 0 011 1v10.586l2.293-2.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 111.414-1.414L9 14.586V4a1 1 0 011-1z" clipRule="evenodd" />
                    </svg>
                  </div>
                </>
              )}

              {/* Spending */}
              <div className="bg-gradient-to-r from-orange-50 to-orange-100 rounded-lg p-3 border border-orange-200">
                <p className="text-xs text-orange-700 font-medium">Average Monthly Spending</p>
                <p className="text-2xl font-bold text-orange-900">
                  -${investmentData.breakdown.average_monthly_spending.toLocaleString()}
                </p>
                <p className="text-xs text-orange-600 mt-1">{investmentData.calculation_period}</p>
              </div>

              {/* Arrow down */}
              {investmentData.breakdown.total_goal_commitments > 0 && (
                <>
                  <div className="flex justify-center">
                    <svg className="w-6 h-6 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 3a1 1 0 011 1v10.586l2.293-2.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 111.414-1.414L9 14.586V4a1 1 0 011-1z" clipRule="evenodd" />
                    </svg>
                  </div>

                  {/* Goal Commitments */}
                  <div className="bg-gradient-to-r from-purple-50 to-purple-100 rounded-lg p-3 border border-purple-200">
                    <p className="text-xs text-purple-700 font-medium">
                      Goal Commitments ({investmentData.active_goals_count} {investmentData.active_goals_count === 1 ? 'goal' : 'goals'})
                    </p>
                    <p className="text-2xl font-bold text-purple-900">
                      -${investmentData.breakdown.total_goal_commitments.toLocaleString()}
                    </p>
                  </div>
                </>
              )}

              {/* Arrow down */}
              <div className="flex justify-center">
                <svg className="w-6 h-6 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 3a1 1 0 011 1v10.586l2.293-2.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 111.414-1.414L9 14.586V4a1 1 0 011-1z" clipRule="evenodd" />
                </svg>
              </div>

              {/* Available to Invest */}
              <div className="bg-gradient-to-br from-teal-50 to-cyan-50 rounded-lg p-4 border-2 border-teal-300 shadow-md">
                <p className="text-sm text-teal-700 font-semibold mb-2">💰 Available to Invest</p>
                <p className="text-3xl font-bold text-teal-600">
                  ${Math.round(investmentData.breakdown.investable_surplus).toLocaleString()}
                </p>
                <p className="text-xs text-teal-600 mt-1">per month</p>
              </div>
            </div>

            {/* Learn More Button */}
            <button
              onClick={() => setShowInvestmentModal(true)}
              className="w-full bg-gradient-to-r from-teal-500 to-cyan-500 text-white py-3 rounded-lg font-medium hover:from-teal-600 hover:to-cyan-600 transition-all shadow-md"
            >
              📚 Learn Investment Options
            </button>

            <button
              onClick={() => setInvestmentData(null)}
              className="w-full text-sm text-gray-600 hover:text-gray-800 font-medium"
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
                className={`rounded-xl p-4 border transition-all ${
                  sub.is_gray_charge ? 'border-amber-400 bg-amber-50' :
                  sub.is_trial_conversion ? 'border-blue-400 bg-blue-50' :
                  sub.has_price_increase ? 'border-red-300 bg-red-50' :
                  'border-gray-200 bg-white'
                }`}
              >
                {/* Header: Logo, Name, and Price */}
                <div className="flex items-center gap-3 mb-3">
                  {/* Logo */}
                  <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-pink-500 rounded-xl flex items-center justify-center text-white font-bold text-base flex-shrink-0 shadow-md">
                    {getInitials(sub.merchant_name)}
                  </div>

                  {/* Name and Price */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-1">
                      <h5 className="font-bold text-gray-900 text-base capitalize truncate">
                        {sub.original_merchant_name}
                      </h5>
                      <div className="flex items-center gap-1 ml-2 flex-shrink-0">
                        {sub.has_price_increase && sub.price_increase && (
                          <div className="group relative">
                            <svg className="w-4 h-4 text-red-500" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M5.293 7.707a1 1 0 010-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 01-1.414 1.414L11 5.414V17a1 1 0 11-2 0V5.414L6.707 7.707a1 1 0 01-1.414 0z" clipRule="evenodd" />
                            </svg>
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

                    {/* Badges */}
                    <div className="flex items-center gap-1.5 flex-wrap">
                      {sub.is_gray_charge && (
                        <span className="bg-amber-500 text-white text-[10px] px-2 py-0.5 rounded-full font-medium">
                          ⚠️ Gray Charge
                        </span>
                      )}
                      {sub.is_trial_conversion && (
                        <span className="bg-blue-500 text-white text-[10px] px-2 py-0.5 rounded-full font-medium">
                          🆕 New Trial
                        </span>
                      )}
                      <span className="text-xs text-gray-600 capitalize">{sub.frequency}</span>
                      <span className="text-xs text-gray-400">•</span>
                      <span className="text-xs text-gray-600">{sub.transaction_count} charges</span>
                    </div>
                  </div>
                </div>

                {/* Confidence Bar */}
                <div className="mb-3">
                  <div className="flex items-center gap-2">
                    <div className="flex-1 bg-gray-200 rounded-full h-1.5">
                      <div
                        className="bg-gradient-to-r from-green-500 to-emerald-500 h-1.5 rounded-full transition-all duration-500"
                        style={{ width: `${sub.confidence_score}%` }}
                      ></div>
                    </div>
                    <span className="text-xs text-gray-600 font-medium whitespace-nowrap">
                      {sub.confidence_score.toFixed(0)}% confidence
                    </span>
                  </div>
                </div>

                {/* Next Charge Date */}
                <div className="mb-3">
                  <p className="text-xs text-gray-600">
                    Next charge: <span className="font-medium text-gray-900">{formatDate(sub.next_predicted_date)}</span>
                  </p>
                </div>

                {/* Actions */}
                <div className="flex gap-2">
                  <button
                    onClick={() => handleSubscriptionAction(sub.merchant_name, 'dismiss')}
                    className="flex-1 text-sm py-2 px-3 bg-white border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors font-medium"
                  >
                    Keep
                  </button>
                  <button
                    onClick={() => handleSubscriptionAction(sub.merchant_name, 'flag')}
                    className="flex-1 text-sm py-2 px-3 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors font-medium"
                  >
                    Mark to Cancel
                  </button>
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
              <span className="bg-red-500 text-white text-xs font-bold px-2.5 py-1 rounded-full">
                {flaggedSubscriptions.length}
              </span>
            </div>
            <div className="space-y-3">
              {flaggedSubscriptions.map((sub) => (
                <div
                  key={sub.merchant_name}
                  className="bg-red-50 rounded-xl p-4 border border-red-200"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-gray-400 rounded-xl flex items-center justify-center text-white font-bold text-sm flex-shrink-0 opacity-60">
                      {getInitials(sub.merchant_name)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-bold text-gray-700 text-base line-through capitalize mb-1">
                        {sub.original_merchant_name}
                      </p>
                      <div className="flex items-center gap-2 text-xs text-gray-600">
                        <span className="font-semibold text-red-600">${sub.monthly_cost.toFixed(2)}/mo</span>
                        <span>•</span>
                        <span className="capitalize">{sub.frequency}</span>
                      </div>
                    </div>
                    <button
                      onClick={() => setSubscriptions(subscriptions.map(s =>
                        s.merchant_name === sub.merchant_name ? { ...s, status: 'active' } : s
                      ))}
                      className="text-xs text-teal-600 hover:text-teal-700 font-semibold px-3 py-1.5 bg-white border border-teal-300 hover:bg-teal-50 rounded-lg transition-colors flex-shrink-0"
                    >
                      Undo
                    </button>
                  </div>
                </div>
              ))}
              <div className="bg-gradient-to-br from-green-50 to-emerald-50 border-2 border-green-300 rounded-xl p-4 mt-4 shadow-sm">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-semibold text-green-800 mb-1">
                      💰 Potential Savings
                    </p>
                    <p className="text-xs text-green-700">
                      ${(flaggedSubscriptions.reduce((sum, s) => sum + s.monthly_cost, 0) * 12).toFixed(2)}/year
                    </p>
                  </div>
                  <p className="text-3xl font-bold text-green-600">
                    ${flaggedSubscriptions.reduce((sum, s) => sum + s.monthly_cost, 0).toFixed(2)}<span className="text-sm font-medium text-green-700">/mo</span>
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Investment Modal */}
      {showInvestmentModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4" onClick={() => !investmentData && setShowInvestmentModal(false)}>
          <div className="bg-white rounded-2xl p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto shadow-2xl animate-slide-up" onClick={(e) => e.stopPropagation()}>
            {!investmentData ? (
              <>
                <h3 className="text-2xl font-bold text-gray-900 mb-4">Calculate Investment Capacity</h3>
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
                    <label className="block text-sm font-medium text-gray-700 mb-2">Income Type</label>
                    <div className="flex gap-4">
                      <label className="flex items-center cursor-pointer">
                        <input
                          type="radio"
                          checked={formData.isGross}
                          onChange={() => setFormData({ ...formData, isGross: true })}
                          className="mr-2"
                        />
                        <span className="text-sm">Gross (before taxes)</span>
                      </label>
                      <label className="flex items-center cursor-pointer">
                        <input
                          type="radio"
                          checked={!formData.isGross}
                          onChange={() => setFormData({ ...formData, isGross: false })}
                          className="mr-2"
                        />
                        <span className="text-sm">Net (take-home)</span>
                      </label>
                    </div>
                  </div>
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                    <p className="text-xs text-blue-700">
                      💡 We'll analyze your transaction history and active savings goals to show you exactly
                      how much you have available to invest each month.
                    </p>
                  </div>
                </div>
                <div className="flex gap-3 mt-6">
                  <button
                    onClick={() => setShowInvestmentModal(false)}
                    className="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors font-medium"
                    disabled={isCalculating}
                  >
                    Cancel
                  </button>
                  <button
                    onClick={calculateInvestment}
                    disabled={!formData.income || isCalculating}
                    className="flex-1 px-4 py-2 bg-teal-500 text-white rounded-lg hover:bg-teal-600 transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {isCalculating ? 'Calculating...' : 'Calculate'}
                  </button>
                </div>
              </>
            ) : (
              <>
                <div className="flex justify-between items-center mb-6">
                  <h3 className="text-2xl font-bold text-gray-900">Investment Options for Beginners</h3>
                  <button
                    onClick={() => setShowInvestmentModal(false)}
                    className="text-gray-400 hover:text-gray-600 transition-colors"
                  >
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>

                <div className="bg-gradient-to-r from-teal-50 to-cyan-50 rounded-lg p-4 border border-teal-200 mb-6">
                  <p className="text-sm text-teal-700 mb-2">You have <strong>${Math.round(investmentData.breakdown.investable_surplus).toLocaleString()}/month</strong> available to invest</p>
                  <p className="text-xs text-teal-600">
                    Here are beginner-friendly options for putting that money to work:
                  </p>
                </div>

                <div className="space-y-4">
                  {investmentData.investment_options.map((option, index) => (
                    <div key={index} className="border border-gray-200 rounded-lg overflow-hidden">
                      <button
                        onClick={() => setExpandedOption(expandedOption === index ? null : index)}
                        className="w-full p-4 bg-white hover:bg-gray-50 transition-colors text-left"
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <h4 className="font-bold text-gray-900 mb-2">{option.name}</h4>
                            <div className="flex flex-wrap gap-2 mb-2">
                              <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded-full font-medium">
                                {option.risk_level}
                              </span>
                              <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded-full font-medium">
                                {option.typical_returns}
                              </span>
                            </div>
                            <p className="text-sm text-gray-600">
                              <strong>Access:</strong> {option.accessibility}
                            </p>
                          </div>
                          <svg
                            className={`w-5 h-5 text-gray-400 transition-transform ${expandedOption === index ? 'transform rotate-180' : ''}`}
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                          </svg>
                        </div>
                      </button>

                      {expandedOption === index && (
                        <div className="px-4 pb-4 bg-gray-50 border-t border-gray-200 animate-slide-down">
                          <div className="pt-4 space-y-3">
                            <div>
                              <p className="text-xs font-semibold text-gray-700 mb-1">Best For:</p>
                              <p className="text-sm text-gray-600">{option.best_for}</p>
                            </div>
                            <div>
                              <p className="text-xs font-semibold text-gray-700 mb-1">What It Is:</p>
                              <p className="text-sm text-gray-600 leading-relaxed">{option.description}</p>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>

                <div className="mt-6 bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                  <p className="text-xs text-yellow-800 mb-2">
                    <strong>⚠️ Not Financial Advice:</strong>
                  </p>
                  <p className="text-xs text-yellow-700">
                    This information is educational only. Do your own research and consider consulting
                    a financial advisor before making investment decisions. Your financial situation is unique.
                  </p>
                </div>
              </>
            )}
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

        @keyframes slide-down {
          from {
            opacity: 0;
            max-height: 0;
          }
          to {
            opacity: 1;
            max-height: 500px;
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

        .animate-slide-down {
          animation: slide-down 0.3s ease-out;
        }
      `}</style>
    </aside>
  );
}
