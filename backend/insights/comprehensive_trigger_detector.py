from typing import List, Dict
from app.models import Trigger
from spending.aggregator import DataAggregator
import numpy as np


class ComprehensiveTriggerDetector:
    """
    Stage 2: Comprehensive trigger detection across all timeframes
    Implements the complete intelligent insights detection logic
    """

    def __init__(self, aggregator: DataAggregator):
        self.aggregator = aggregator
        self.aggregations = aggregator.aggregations
        self.derived = aggregator.derived_metrics
        self.triggers = []

    def detect_all_triggers(self) -> List[Trigger]:
        """Run all detection rules and return all triggers"""
        self.triggers = []

        # Short-term insights
        self.triggers.extend(self._detect_weekly_changes())
        self.triggers.extend(self._detect_monthly_changes())

        # Medium-term insights
        self.triggers.extend(self._detect_quarterly_trends())
        self.triggers.extend(self._detect_rolling_trends())

        # Long-term insights
        self.triggers.extend(self._detect_year_over_year())
        self.triggers.extend(self._detect_all_time_records())
        self.triggers.extend(self._detect_lifetime_milestones())
        self.triggers.extend(self._detect_long_term_trends())

        # Seasonal patterns
        self.triggers.extend(self._detect_seasonal_patterns())

        # Behavioral patterns
        self.triggers.extend(self._detect_weekend_vs_weekday())
        self.triggers.extend(self._detect_merchant_loyalty())
        self.triggers.extend(self._detect_category_dominance())

        # Positive reinforcement
        self.triggers.extend(self._detect_savings_streaks())
        self.triggers.extend(self._detect_improvement_trends())

        return self.triggers

    # ==================== SHORT-TERM INSIGHTS ====================

    def _detect_weekly_changes(self) -> List[Trigger]:
        """Detect week-over-week spending changes"""
        triggers = []

        sorted_weeks = self.aggregations['by_week']['sorted_keys']
        if len(sorted_weeks) < 2:
            return triggers

        current_week = sorted_weeks[-1]
        previous_week = sorted_weeks[-2]

        current_total = self.aggregations['by_week']['totals'].get(current_week, {}).get('total_spending', 0)
        previous_total = self.aggregations['by_week']['totals'].get(previous_week, {}).get('total_spending', 0)

        if previous_total == 0:
            return triggers

        pct_change = ((current_total - previous_total) / previous_total) * 100

        # Weekly spending spike (40%+ increase)
        if pct_change > 40:
            triggers.append(Trigger(
                type="weekly_spending_spike",
                this_month=current_total,
                last_month=previous_total,
                percent_change=pct_change,
                dollar_change=current_total - previous_total,
                raw_data={'week': current_week}
            ))

        # Weekly spending win (25%+ decrease)
        if pct_change < -25:
            triggers.append(Trigger(
                type="weekly_spending_win",
                this_month=current_total,
                last_month=previous_total,
                percent_change=abs(pct_change),
                dollar_change=abs(current_total - previous_total),
                raw_data={'week': current_week}
            ))

        # Category-level weekly analysis
        current_week_categories = self.aggregations['by_week']['by_category'].get(current_week, {})
        previous_week_categories = self.aggregations['by_week']['by_category'].get(previous_week, {})

        for category, current_amount in current_week_categories.items():
            previous_amount = previous_week_categories.get(category, 0)
            if previous_amount == 0 or current_amount < 50:
                continue

            cat_pct_change = ((current_amount - previous_amount) / previous_amount) * 100

            if cat_pct_change > 50 and current_amount > 50:
                triggers.append(Trigger(
                    type="weekly_category_spike",
                    category=category,
                    this_month=current_amount,
                    last_month=previous_amount,
                    percent_change=cat_pct_change,
                    dollar_change=current_amount - previous_amount,
                    raw_data={'week': current_week}
                ))

        return triggers

    def _detect_monthly_changes(self) -> List[Trigger]:
        """Detect month-over-month and vs-average spending changes using rolling 30-day periods"""
        triggers = []

        # Get rolling 30-day period data
        rolling_data = self.aggregator.get_rolling_30day_totals()

        current_total = rolling_data['current_total']
        previous_total = rolling_data['previous_total']
        current_cats = rolling_data['current_by_category']
        previous_cats = rolling_data['previous_by_category']
        monthly_avg = self.derived.get('overall_monthly_avg', 0)

        # Format date range for display
        current_start = rolling_data['current_start'].strftime('%b %d')
        current_end = rolling_data['current_end'].strftime('%b %d, %Y')
        date_range = f"{current_start} - {current_end}"

        # Month-over-month spike (30%+ increase)
        if previous_total > 0:
            mom_pct_change = ((current_total - previous_total) / previous_total) * 100

            if mom_pct_change > 30:
                # Find category contributing most to increase
                max_contributor = None
                max_contribution = 0
                for cat, curr_amt in current_cats.items():
                    prev_amt = previous_cats.get(cat, 0)
                    contribution = curr_amt - prev_amt
                    if contribution > max_contribution:
                        max_contribution = contribution
                        max_contributor = cat

                triggers.append(Trigger(
                    type="monthly_spending_spike",
                    this_month=current_total,
                    last_month=previous_total,
                    percent_change=mom_pct_change,
                    dollar_change=current_total - previous_total,
                    category=max_contributor,
                    raw_data={
                        'date_range': date_range,
                        'top_category_contribution': max_contribution,
                        'rolling_period': True,
                        'current_start': rolling_data['current_start'].isoformat(),
                        'current_end': rolling_data['current_end'].isoformat(),
                        'previous_start': rolling_data['previous_start'].isoformat(),
                        'previous_end': rolling_data['previous_end'].isoformat()
                    }
                ))

            # Month-over-month win (20%+ decrease)
            if mom_pct_change < -20:
                triggers.append(Trigger(
                    type="monthly_spending_win",
                    this_month=current_total,
                    last_month=previous_total,
                    percent_change=abs(mom_pct_change),
                    dollar_change=abs(current_total - previous_total),
                    raw_data={
                        'date_range': date_range,
                        'rolling_period': True,
                        'current_start': rolling_data['current_start'].isoformat(),
                        'current_end': rolling_data['current_end'].isoformat(),
                        'previous_start': rolling_data['previous_start'].isoformat(),
                        'previous_end': rolling_data['previous_end'].isoformat()
                    }
                ))

        # Category-level vs average (using current rolling period)
        category_avgs = self.derived.get('category_monthly_averages', {})

        for category, current_amount in current_cats.items():
            avg_amount = category_avgs.get(category, 0)
            if avg_amount == 0 or current_amount < 100:
                continue

            pct_vs_avg = ((current_amount - avg_amount) / avg_amount) * 100

            if pct_vs_avg > 40 and current_amount > 100:
                triggers.append(Trigger(
                    type="category_above_average",
                    category=category,
                    this_month=current_amount,
                    average=avg_amount,
                    percent_change=pct_vs_avg,
                    dollar_change=current_amount - avg_amount,
                    raw_data={
                        'date_range': date_range,
                        'rolling_period': True,
                        'current_start': rolling_data['current_start'].isoformat(),
                        'current_end': rolling_data['current_end'].isoformat()
                    }
                ))

        return triggers

    # ==================== MEDIUM-TERM INSIGHTS ====================

    def _detect_quarterly_trends(self) -> List[Trigger]:
        """Detect quarter-over-quarter changes"""
        triggers = []

        sorted_quarters = self.aggregations['by_quarter']['sorted_keys']
        if len(sorted_quarters) < 2:
            return triggers

        current_quarter = sorted_quarters[-1]
        previous_quarter = sorted_quarters[-2]

        current_total = self.aggregations['by_quarter']['totals'].get(current_quarter, {}).get('total_spending', 0)
        previous_total = self.aggregations['by_quarter']['totals'].get(previous_quarter, {}).get('total_spending', 0)

        if previous_total == 0:
            return triggers

        pct_change = ((current_total - previous_total) / previous_total) * 100

        if abs(pct_change) > 20:
            triggers.append(Trigger(
                type="quarterly_trend_increase" if pct_change > 0 else "quarterly_trend_decrease",
                this_month=current_total,
                last_month=previous_total,
                percent_change=abs(pct_change),
                dollar_change=abs(current_total - previous_total),
                raw_data={'quarter': current_quarter, 'previous_quarter': previous_quarter}
            ))

        return triggers

    def _detect_rolling_trends(self) -> List[Trigger]:
        """Detect sustained trends over rolling periods"""
        triggers = []

        # 6-month rolling trend
        trend_6mo = self.aggregator.get_rolling_trend('month', window_months=6)
        if trend_6mo.get('has_data'):
            pct_change = trend_6mo['pct_change']
            slope_pct = trend_6mo['slope_pct_of_avg']

            sorted_months = self.aggregations['by_month']['sorted_keys']
            last_6_months = sorted_months[-6:] if len(sorted_months) >= 6 else sorted_months

            # Sustained 6-month trend (15%+ change)
            if abs(pct_change) > 15:
                triggers.append(Trigger(
                    type="six_month_sustained_trend",
                    this_month=trend_6mo['second_half_avg'],
                    last_month=trend_6mo['first_half_avg'],
                    percent_change=abs(pct_change),
                    dollar_change=abs(trend_6mo['second_half_avg'] - trend_6mo['first_half_avg']),
                    raw_data={
                        'trend_direction': 'increasing' if pct_change > 0 else 'decreasing',
                        'slope': trend_6mo['slope'],
                        'avg_spending': trend_6mo['avg_spending'],
                        'months': last_6_months
                    }
                ))

        # 3-month rolling trend
        trend_3mo = self.aggregator.get_rolling_trend('month', window_months=3)
        if trend_3mo.get('has_data') and abs(trend_3mo['pct_change']) > 15:
            sorted_months = self.aggregations['by_month']['sorted_keys']
            last_3_months = sorted_months[-3:] if len(sorted_months) >= 3 else sorted_months

            triggers.append(Trigger(
                type="three_month_sustained_trend",
                this_month=trend_3mo['second_half_avg'],
                last_month=trend_3mo['first_half_avg'],
                percent_change=abs(trend_3mo['pct_change']),
                raw_data={
                    'trend_direction': 'increasing' if trend_3mo['pct_change'] > 0 else 'decreasing',
                    'months': last_3_months
                }
            ))

        # Category-level rolling trends
        current_month = self.derived.get('current_month')
        sorted_months = self.aggregations['by_month']['sorted_keys']

        if len(sorted_months) >= 6:
            last_6_months = sorted_months[-6:]
            category_avgs = self.derived.get('category_monthly_averages', {})

            for category, avg in category_avgs.items():
                if avg < 50:
                    continue

                # Get category spending for last 6 months
                category_spending = []
                for month in last_6_months:
                    amount = self.aggregations['by_month']['by_category'].get(month, {}).get(category, 0)
                    category_spending.append(amount)

                if len(category_spending) >= 6:
                    x = np.arange(len(category_spending))
                    y = np.array(category_spending)
                    slope, _ = np.polyfit(x, y, 1)

                    # If slope is >10% of average, it's a significant trend
                    if abs(slope) > (avg * 0.1):
                        triggers.append(Trigger(
                            type="category_rolling_trend",
                            category=category,
                            average=avg,
                            raw_data={
                                'slope': slope,
                                'trend_direction': 'increasing' if slope > 0 else 'decreasing',
                                'slope_pct_of_avg': (slope / avg * 100) if avg > 0 else 0,
                                'months': last_6_months
                            }
                        ))

        return triggers

    # ==================== LONG-TERM INSIGHTS ====================

    def _detect_year_over_year(self) -> List[Trigger]:
        """Detect year-over-year comparisons using rolling 30-day periods"""
        triggers = []

        # Get rolling 30-day YoY data
        yoy_data = self.aggregator.get_yoy_rolling_totals()

        current_total = yoy_data['current_total']
        last_year_total = yoy_data['previous_total']
        current_cats = yoy_data['current_by_category']
        last_year_cats = yoy_data['previous_by_category']

        if last_year_total == 0:
            return triggers

        yoy_pct_change = ((current_total - last_year_total) / last_year_total) * 100

        # Format date ranges for display
        current_start = yoy_data['current_start'].strftime('%b %d, %Y')
        current_end = yoy_data['current_end'].strftime('%b %d, %Y')
        previous_start = yoy_data['previous_start'].strftime('%b %d, %Y')
        previous_end = yoy_data['previous_end'].strftime('%b %d, %Y')

        # YoY (25%+ change)
        if abs(yoy_pct_change) > 25:
            triggers.append(Trigger(
                type="year_over_year_change",
                this_month=current_total,
                last_month=last_year_total,
                percent_change=abs(yoy_pct_change),
                dollar_change=abs(current_total - last_year_total),
                raw_data={
                    'current_period': f"{current_start} - {current_end}",
                    'comparison_period': f"{previous_start} - {previous_end}",
                    'direction': 'increase' if yoy_pct_change > 0 else 'decrease',
                    'rolling_period': True,
                    'yoy_current_start': yoy_data['current_start'].isoformat(),
                    'yoy_current_end': yoy_data['current_end'].isoformat(),
                    'yoy_previous_start': yoy_data['previous_start'].isoformat(),
                    'yoy_previous_end': yoy_data['previous_end'].isoformat()
                }
            ))

        # Category-level YoY
        for category, current_amount in current_cats.items():
            last_year_amount = last_year_cats.get(category, 0)
            if last_year_amount == 0 or current_amount < 100:
                continue

            cat_yoy_pct = ((current_amount - last_year_amount) / last_year_amount) * 100

            if abs(cat_yoy_pct) > 50 and current_amount > 100:
                triggers.append(Trigger(
                    type="category_year_over_year",
                    category=category,
                    this_month=current_amount,
                    last_month=last_year_amount,
                    percent_change=abs(cat_yoy_pct),
                    dollar_change=abs(current_amount - last_year_amount),
                    raw_data={
                        'direction': 'increase' if cat_yoy_pct > 0 else 'decrease',
                        'current_period': f"{current_start} - {current_end}",
                        'comparison_period': f"{previous_start} - {previous_end}",
                        'rolling_period': True,
                        'yoy_current_start': yoy_data['current_start'].isoformat(),
                        'yoy_current_end': yoy_data['current_end'].isoformat(),
                        'yoy_previous_start': yoy_data['previous_start'].isoformat(),
                        'yoy_previous_end': yoy_data['previous_end'].isoformat()
                    }
                ))

        return triggers

    def _detect_all_time_records(self) -> List[Trigger]:
        """Detect all-time high/low spending months"""
        triggers = []

        sorted_months = self.aggregations['by_month']['sorted_keys']
        if len(sorted_months) < 3:
            return triggers

        current_month = sorted_months[-1]
        current_total = self.aggregations['by_month']['totals'].get(current_month, {}).get('total_spending', 0)

        # Get all monthly totals
        all_monthly_totals = [
            self.aggregations['by_month']['totals'].get(month, {}).get('total_spending', 0)
            for month in sorted_months
        ]

        # All-time high
        if current_total == max(all_monthly_totals):
            triggers.append(Trigger(
                type="all_time_high_spending",
                this_month=current_total,
                raw_data={
                    'month': current_month,
                    'previous_high': sorted(all_monthly_totals, reverse=True)[1] if len(all_monthly_totals) > 1 else 0
                }
            ))

        # All-time low (excluding first month which might be partial)
        if len(sorted_months) > 1:
            non_first_months = sorted_months[1:]
            non_first_totals = [
                self.aggregations['by_month']['totals'].get(month, {}).get('total_spending', 0)
                for month in non_first_months
            ]
            if current_total == min(non_first_totals) and current_total > 0:
                triggers.append(Trigger(
                    type="all_time_low_spending",
                    this_month=current_total,
                    raw_data={'month': current_month}
                ))

        # Category-level all-time highs
        current_cats = self.aggregations['by_month']['by_category'].get(current_month, {})
        for category, current_amount in current_cats.items():
            # Get all historical amounts for this category
            cat_historical = [
                self.aggregations['by_month']['by_category'].get(month, {}).get(category, 0)
                for month in sorted_months
            ]

            if current_amount == max(cat_historical) and current_amount > 100:
                triggers.append(Trigger(
                    type="category_all_time_high",
                    category=category,
                    this_month=current_amount,
                    raw_data={'month': current_month}
                ))

        return triggers

    def _detect_lifetime_milestones(self) -> List[Trigger]:
        """Detect lifetime spending milestones"""
        triggers = []

        # Total lifetime spending
        total_lifetime = sum(
            data['total_spending']
            for data in self.aggregations['by_category'].values()
        )

        milestones = [10000, 25000, 50000, 100000, 250000, 500000, 1000000]
        for milestone in milestones:
            # Check if we just crossed this milestone (current month pushed us over)
            current_month = self.derived.get('current_month')
            if current_month:
                current_month_total = self.aggregations['by_month']['totals'].get(current_month, {}).get('total_spending', 0)
                previous_lifetime = total_lifetime - current_month_total

                if previous_lifetime < milestone <= total_lifetime:
                    triggers.append(Trigger(
                        type="lifetime_spending_milestone",
                        this_month=total_lifetime,
                        raw_data={'milestone': milestone}
                    ))
                    break  # Only trigger one milestone at a time

        # Merchant milestones
        for merchant, data in self.aggregations['by_merchant'].items():
            total_spent = data['total_spending']
            merchant_milestones = [500, 1000, 2500, 5000, 10000]

            for milestone in merchant_milestones:
                if total_spent >= milestone:
                    # Check if this is recent (within last 3 months of transactions)
                    last_transaction = data.get('last_transaction')
                    if last_transaction and (self.derived['latest_transaction'] - last_transaction).days < 90:
                        triggers.append(Trigger(
                            type="merchant_lifetime_milestone",
                            merchant=merchant,
                            this_month=total_spent,
                            visit_count=data['transaction_count'],
                            raw_data={
                                'milestone_amount': milestone,
                                'milestone_type': 'spending'
                            }
                        ))
                        break  # One milestone per merchant

        return triggers

    def _detect_long_term_trends(self) -> List[Trigger]:
        """Detect long-term trends (CAGR, lifestyle inflation)"""
        triggers = []

        sorted_years = self.aggregations['by_year']['sorted_keys']

        # Calculate CAGR if 2+ years of data
        if len(sorted_years) >= 2:
            first_year = sorted_years[0]
            last_year = sorted_years[-1]

            first_year_total = self.aggregations['by_year']['totals'].get(first_year, {}).get('total_spending', 0)
            last_year_total = self.aggregations['by_year']['totals'].get(last_year, {}).get('total_spending', 0)

            years_diff = int(last_year) - int(first_year)

            if first_year_total > 0 and years_diff > 0:
                cagr = ((last_year_total / first_year_total) ** (1 / years_diff) - 1) * 100

                if abs(cagr) > 10:
                    triggers.append(Trigger(
                        type="annual_growth_rate",
                        percent_change=abs(cagr),
                        raw_data={
                            'cagr': cagr,
                            'first_year': first_year,
                            'last_year': last_year,
                            'first_year_total': first_year_total,
                            'last_year_total': last_year_total,
                            'direction': 'growth' if cagr > 0 else 'decline'
                        }
                    ))

        # Lifestyle inflation detection
        sorted_months = self.aggregations['by_month']['sorted_keys']
        if len(sorted_months) >= 12:
            first_6_months = sorted_months[:6]
            last_6_months = sorted_months[-6:]

            first_6_avg = np.mean([
                self.aggregations['by_month']['totals'].get(month, {}).get('total_spending', 0)
                for month in first_6_months
            ])

            last_6_avg = np.mean([
                self.aggregations['by_month']['totals'].get(month, {}).get('total_spending', 0)
                for month in last_6_months
            ])

            if first_6_avg > 0:
                pct_increase = ((last_6_avg - first_6_avg) / first_6_avg) * 100

                if pct_increase > 30:
                    triggers.append(Trigger(
                        type="lifestyle_inflation",
                        this_month=last_6_avg,
                        last_month=first_6_avg,
                        percent_change=pct_increase,
                        dollar_change=last_6_avg - first_6_avg,
                        raw_data={'timeframe': f'{first_6_months[0]} to {last_6_months[-1]}'}
                    ))

        return triggers

    # ==================== SEASONAL PATTERNS ====================

    def _detect_seasonal_patterns(self) -> List[Trigger]:
        """Detect recurring monthly patterns and seasonal spending"""
        triggers = []

        seasonal_data = self.aggregations['by_month_number']
        overall_avg = self.derived.get('overall_monthly_avg', 0)

        if overall_avg == 0 or len(seasonal_data) < 3:
            return triggers

        high_spend_months = []
        low_spend_months = []

        month_names = {
            1: 'January', 2: 'February', 3: 'March', 4: 'April',
            5: 'May', 6: 'June', 7: 'July', 8: 'August',
            9: 'September', 10: 'October', 11: 'November', 12: 'December'
        }

        for month_num, total_amount in seasonal_data.items():
            # Count how many years of data for this month
            count = sum(1 for m in self.aggregations['by_month']['sorted_keys'] if int(m.split('-')[1]) == month_num)
            if count == 0:
                continue

            monthly_avg_for_this_month = total_amount / count
            deviation_pct = ((monthly_avg_for_this_month - overall_avg) / overall_avg) * 100

            if deviation_pct > 20:
                high_spend_months.append((month_names[month_num], monthly_avg_for_this_month, deviation_pct))
            elif deviation_pct < -20:
                low_spend_months.append((month_names[month_num], monthly_avg_for_this_month, deviation_pct))

        # Holiday season detection (Nov-Dec)
        if 11 in seasonal_data and 12 in seasonal_data:
            q4_months = [10, 11, 12] if 10 in seasonal_data else [11, 12]
            q4_total = sum(seasonal_data.get(m, 0) for m in q4_months)
            q4_count = sum(1 for m in self.aggregations['by_month']['sorted_keys'] if int(m.split('-')[1]) in q4_months)
            q4_avg = q4_total / q4_count if q4_count > 0 else 0

            other_months_total = sum(v for k, v in seasonal_data.items() if k not in q4_months)
            other_count = sum(1 for m in self.aggregations['by_month']['sorted_keys'] if int(m.split('-')[1]) not in q4_months)
            other_avg = other_months_total / other_count if other_count > 0 else 0

            if other_avg > 0:
                q4_increase_pct = ((q4_avg - other_avg) / other_avg) * 100

                if q4_increase_pct > 20:
                    triggers.append(Trigger(
                        type="holiday_season_pattern",
                        this_month=q4_avg,
                        average=other_avg,
                        percent_change=q4_increase_pct,
                        raw_data={'season': 'Q4 (Oct-Dec)', 'description': 'holiday shopping season'}
                    ))

        # Flag individual high-spend months
        for month_name, avg_amount, deviation in high_spend_months[:2]:  # Top 2
            triggers.append(Trigger(
                type="seasonal_high_spend_month",
                this_month=avg_amount,
                average=overall_avg,
                percent_change=deviation,
                raw_data={'month': month_name}
            ))

        return triggers

    # ==================== BEHAVIORAL PATTERNS ====================

    def _detect_weekend_vs_weekday(self) -> List[Trigger]:
        """Detect weekend vs weekday spending patterns"""
        triggers = []

        day_data = self.aggregations['by_day_of_week']
        weekend_daily_avg = day_data.get('weekend_daily_avg', 0)
        weekday_daily_avg = day_data.get('weekday_daily_avg', 0)

        if weekday_daily_avg == 0:
            return triggers

        # Weekend warrior (50%+ more on weekends)
        if weekend_daily_avg > weekday_daily_avg * 1.5:
            ratio = weekend_daily_avg / weekday_daily_avg if weekday_daily_avg > 0 else 0
            triggers.append(Trigger(
                type="weekend_warrior",
                weekend_spend=weekend_daily_avg,
                weekday_spend=weekday_daily_avg,
                percent_change=ratio * 100,
                raw_data={'ratio': ratio}
            ))

        # Weekday spender
        elif weekday_daily_avg > weekend_daily_avg * 1.5:
            ratio = weekday_daily_avg / weekend_daily_avg if weekend_daily_avg > 0 else 0
            triggers.append(Trigger(
                type="weekday_spender",
                weekend_spend=weekend_daily_avg,
                weekday_spend=weekday_daily_avg,
                raw_data={'ratio': ratio}
            ))

        return triggers

    def _detect_merchant_loyalty(self) -> List[Trigger]:
        """Detect merchant loyalty patterns"""
        triggers = []

        # Top merchants by total spending
        merchant_data = self.aggregations['by_merchant']
        top_merchants = sorted(
            merchant_data.items(),
            key=lambda x: x[1]['total_spending'],
            reverse=True
        )[:5]

        for merchant, data in top_merchants:
            total_spent = data['total_spending']
            visit_count = data['transaction_count']

            # High loyalty (>10 visits or >$500 spent)
            if visit_count > 10 or total_spent > 500:
                triggers.append(Trigger(
                    type="merchant_loyalty",
                    merchant=merchant,
                    this_month=total_spent,
                    visit_count=visit_count,
                    raw_data={
                        'first_transaction': data.get('first_transaction'),
                        'last_transaction': data.get('last_transaction')
                    }
                ))

        # New merchant alert (last transaction within 30 days, first transaction within 60 days)
        for merchant, data in merchant_data.items():
            last_trans = data.get('last_transaction')
            first_trans = data.get('first_transaction')

            if last_trans and first_trans:
                days_since_last = (self.derived['latest_transaction'] - last_trans).days
                days_since_first = (self.derived['latest_transaction'] - first_trans).days

                if days_since_last <= 30 and days_since_first <= 60 and data['total_spending'] > 100:
                    triggers.append(Trigger(
                        type="new_significant_merchant",
                        merchant=merchant,
                        this_month=data['total_spending'],
                        visit_count=data['transaction_count'],
                        raw_data={'days_since_first': days_since_first}
                    ))

        return triggers

    def _detect_category_dominance(self) -> List[Trigger]:
        """Detect if any category dominates spending"""
        triggers = []

        total_spending = sum(data['total_spending'] for data in self.aggregations['by_category'].values())
        if total_spending == 0:
            return triggers

        for category, data in self.aggregations['by_category'].items():
            category_share = (data['total_spending'] / total_spending) * 100

            # Dominant category (>35% of total)
            if category_share > 35:
                triggers.append(Trigger(
                    type="category_dominance",
                    category=category,
                    this_month=data['total_spending'],
                    percent_change=category_share,
                    raw_data={'total_spending': total_spending, 'share': category_share}
                ))

        return triggers

    # ==================== POSITIVE REINFORCEMENT ====================

    def _detect_savings_streaks(self) -> List[Trigger]:
        """Detect consecutive months of below-average spending"""
        triggers = []

        sorted_months = self.aggregations['by_month']['sorted_keys']
        overall_avg = self.derived.get('overall_monthly_avg', 0)

        if overall_avg == 0 or len(sorted_months) < 3:
            return triggers

        # Check consecutive months below average
        consecutive_below = 0
        for month in sorted_months[-6:]:  # Check last 6 months
            month_total = self.aggregations['by_month']['totals'].get(month, {}).get('total_spending', 0)
            if month_total < overall_avg:
                consecutive_below += 1
            else:
                consecutive_below = 0

        if consecutive_below >= 2:
            # Calculate total saved
            last_n_months = sorted_months[-consecutive_below:]
            total_saved = sum(
                overall_avg - self.aggregations['by_month']['totals'].get(month, {}).get('total_spending', 0)
                for month in last_n_months
            )

            triggers.append(Trigger(
                type="savings_streak",
                dollar_change=total_saved,
                raw_data={'streak_length': consecutive_below, 'months': last_n_months}
            ))

        # Income-positive streak (if income data available)
        income_data = self.aggregations['by_month']['income']
        consecutive_positive = 0

        for month in sorted_months[-6:]:
            month_spending = self.aggregations['by_month']['totals'].get(month, {}).get('total_spending', 0)
            month_income = income_data.get(month, 0)

            if month_income > month_spending:
                consecutive_positive += 1
            else:
                consecutive_positive = 0

        if consecutive_positive >= 3:
            triggers.append(Trigger(
                type="income_positive_streak",
                raw_data={'streak_length': consecutive_positive}
            ))

        return triggers

    def _detect_improvement_trends(self) -> List[Trigger]:
        """Detect improving spending patterns"""
        triggers = []

        sorted_months = self.aggregations['by_month']['sorted_keys']
        if len(sorted_months) < 3:
            return triggers

        # Category improvement (3 consecutive months of decrease)
        for category in self.aggregations['by_category'].keys():
            last_3_months = sorted_months[-3:]
            category_amounts = [
                self.aggregations['by_month']['by_category'].get(month, {}).get(category, 0)
                for month in last_3_months
            ]

            if len(category_amounts) == 3 and all(category_amounts):
                if category_amounts[0] > category_amounts[1] > category_amounts[2]:
                    total_decrease = category_amounts[0] - category_amounts[2]
                    pct_decrease = ((total_decrease) / category_amounts[0] * 100) if category_amounts[0] > 0 else 0

                    if pct_decrease > 20:
                        triggers.append(Trigger(
                            type="category_improvement_trend",
                            category=category,
                            this_month=category_amounts[2],
                            last_month=category_amounts[0],
                            percent_change=pct_decrease,
                            dollar_change=total_decrease,
                            raw_data={'months': last_3_months}
                        ))

        # Overall improvement (3 consecutive months of decrease)
        last_3_totals = [
            self.aggregations['by_month']['totals'].get(month, {}).get('total_spending', 0)
            for month in sorted_months[-3:]
        ]

        if len(last_3_totals) == 3 and all(last_3_totals):
            if last_3_totals[0] > last_3_totals[1] > last_3_totals[2]:
                total_decrease = last_3_totals[0] - last_3_totals[2]
                pct_decrease = ((total_decrease) / last_3_totals[0] * 100) if last_3_totals[0] > 0 else 0

                if pct_decrease > 15:
                    triggers.append(Trigger(
                        type="overall_improvement_trend",
                        this_month=last_3_totals[2],
                        last_month=last_3_totals[0],
                        percent_change=pct_decrease,
                        dollar_change=total_decrease,
                        raw_data={'months': sorted_months[-3:]}
                    ))

        return triggers
