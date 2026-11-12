import { useState } from 'react';
import {
  Area, AreaChart, Bar, BarChart, CartesianGrid, Cell, ComposedChart,
  Legend, Line, Pie, PieChart, ResponsiveContainer, Tooltip as ChartTooltip,
  XAxis, YAxis,
} from 'recharts';
import { formatCompactMoney, formatMoney } from '../utils';
import type { Budget } from '../types';

const axisColor = '#9098ac';
const gridColor = '#eef0f5';

function MoneyTooltip({ active, payload, label }: { active?: boolean; payload?: Array<{ name?: string; value?: number; color?: string; payload?: { category?: string } }>; label?: string }) {
  if (!active || !payload?.length) return null;
  return <div className="chart-tooltip"><span>{label}</span>{payload.map((item, index) => <div className="chart-tooltip-row" key={`${item.name}-${index}`}><i style={{ background: item.color ?? '#3f5ce8' }} /><span>{item.name ?? item.payload?.category}</span><b>{formatMoney(Number(item.value ?? 0))}</b></div>)}</div>;
}

function ChartFrame({ children, className = '' }: { children: React.ReactNode; className?: string }) {
  return <div className={`chart-frame ${className}`}>{children}</div>;
}

export function CategoryDonut({ data }: { data: Array<{ category: string; amount: number; percent: number; color?: string }> }) {
  const total = data.reduce((sum, item) => sum + item.amount, 0);
  return <div className="donut-wrap">
    <ChartFrame className="donut-chart"><ResponsiveContainer width="100%" height="100%"><PieChart><Pie data={data} dataKey="amount" nameKey="category" innerRadius="68%" outerRadius="88%" paddingAngle={3} stroke="none">{data.map((item, index) => <Cell key={`${item.category}-${index}`} fill={item.color ?? '#bac0d0'} />)}</Pie><ChartTooltip content={<MoneyTooltip />} /></PieChart></ResponsiveContainer><div className="donut-center"><strong>{formatCompactMoney(total)}</strong><span>spent</span></div></ChartFrame>
    <div className="donut-legend">{data.slice(0, 5).map((item) => <div className="legend-row" key={item.category}><i style={{ background: item.color ?? '#bac0d0' }} /><span>{item.category}</span><b>{item.percent.toFixed(0)}%</b></div>)}{data.length > 5 && <div className="legend-more">+ {data.length - 5} more categories</div>}</div>
  </div>;
}

export function MonthlyCashflow({ data }: { data: Array<{ month: string; income: number; expenses: number }> }) {
  return <ChartFrame><ResponsiveContainer width="100%" height="100%"><BarChart data={data} margin={{ top: 10, right: 4, left: -16, bottom: 0 }} barGap={5} barCategoryGap="33%"><CartesianGrid vertical={false} stroke={gridColor} /><XAxis dataKey="month" tickLine={false} axisLine={false} tick={{ fill: axisColor, fontSize: 11 }} dy={8} /><YAxis tickLine={false} axisLine={false} tick={{ fill: axisColor, fontSize: 10 }} tickFormatter={(value: number) => formatCompactMoney(value)} /><ChartTooltip content={<MoneyTooltip />} cursor={{ fill: '#f6f7fb' }} /><Bar dataKey="income" name="Income" fill="#2faa81" radius={[5, 5, 0, 0]} maxBarSize={18} /><Bar dataKey="expenses" name="Expenses" fill="#5870e6" radius={[5, 5, 0, 0]} maxBarSize={18} /></BarChart></ResponsiveContainer></ChartFrame>;
}

export function DailySpendingChart({ data }: { data: Array<{ day: string; spend: number; cumulative: number }> }) {
  const [cumulative, setCumulative] = useState(false);
  return <><div className="chart-toggle"><button type="button" className={!cumulative ? 'chart-toggle-active' : ''} onClick={() => setCumulative(false)}>Daily</button><button type="button" className={cumulative ? 'chart-toggle-active' : ''} onClick={() => setCumulative(true)}>Cumulative</button></div><ChartFrame><ResponsiveContainer width="100%" height="100%"><AreaChart data={data} margin={{ top: 10, right: 6, left: -18, bottom: 0 }}><defs><linearGradient id="dailySpendFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#5870e6" stopOpacity={0.2} /><stop offset="100%" stopColor="#5870e6" stopOpacity={0.01} /></linearGradient></defs><CartesianGrid vertical={false} stroke={gridColor} /><XAxis dataKey="day" tickLine={false} axisLine={false} tick={{ fill: axisColor, fontSize: 10 }} interval={3} tickFormatter={(value: string) => `${value}`} /><YAxis tickLine={false} axisLine={false} tick={{ fill: axisColor, fontSize: 10 }} tickFormatter={(value: number) => formatCompactMoney(value)} /><ChartTooltip content={<MoneyTooltip />} /><Area type="monotone" dataKey={cumulative ? 'cumulative' : 'spend'} name={cumulative ? 'Cumulative spend' : 'Daily spend'} stroke="#5870e6" strokeWidth={2.5} fill="url(#dailySpendFill)" activeDot={{ r: 4, strokeWidth: 0 }} /></AreaChart></ResponsiveContainer></ChartFrame></>;
}

export function BudgetComparison({ data }: { data: Array<{ category: string; budget: number; spent: number }> }) {
  const visible = data.filter((item) => item.budget > 0 || item.spent > 0).sort((a, b) => a.spent - b.spent);
  if (!visible.length) return <div className="chart-empty">Set category limits to compare spending against plan.</div>;
  return <ChartFrame className="budget-chart"><ResponsiveContainer width="100%" height="100%"><BarChart data={visible} layout="vertical" margin={{ top: 4, right: 30, left: 4, bottom: 0 }} barGap={3} barCategoryGap="24%"><CartesianGrid horizontal={false} stroke={gridColor} /><XAxis type="number" tickLine={false} axisLine={false} tick={{ fill: axisColor, fontSize: 10 }} tickFormatter={(value: number) => formatCompactMoney(value)} /><YAxis type="category" dataKey="category" width={118} tickLine={false} axisLine={false} tick={{ fill: '#5e667b', fontSize: 10 }} /><ChartTooltip content={<MoneyTooltip />} /><Legend iconType="circle" iconSize={7} wrapperStyle={{ fontSize: 10, color: axisColor }} /><Bar dataKey="budget" name="Limit" fill="#d9deeb" radius={[0, 4, 4, 0]} maxBarSize={11} /><Bar dataKey="spent" name="Spent" fill="#5870e6" radius={[0, 4, 4, 0]} maxBarSize={11} /></BarChart></ResponsiveContainer></ChartFrame>;
}

export function IncomeExpenseLine({ data }: { data: Array<{ month: string; income: number; expenses: number; balance: number }> }) {
  return <ChartFrame><ResponsiveContainer width="100%" height="100%"><ComposedChart data={data} margin={{ top: 12, right: 5, left: -15, bottom: 0 }}><CartesianGrid vertical={false} stroke={gridColor} /><XAxis dataKey="month" tickLine={false} axisLine={false} tick={{ fill: axisColor, fontSize: 11 }} dy={8} /><YAxis tickLine={false} axisLine={false} tick={{ fill: axisColor, fontSize: 10 }} tickFormatter={(value: number) => formatCompactMoney(value)} /><ChartTooltip content={<MoneyTooltip />} /><Legend iconType="circle" iconSize={7} wrapperStyle={{ fontSize: 11, color: axisColor }} /><Bar dataKey="income" name="Income" fill="#36aa83" radius={[4, 4, 0, 0]} maxBarSize={18} /><Bar dataKey="expenses" name="Expenses" fill="#6579e4" radius={[4, 4, 0, 0]} maxBarSize={18} /><Line type="monotone" dataKey="balance" name="Net balance" stroke="#bf9d52" strokeWidth={2} dot={{ r: 2.5, fill: '#bf9d52', strokeWidth: 0 }} /></ComposedChart></ResponsiveContainer></ChartFrame>;
}

export function BudgetStatusSummary({ budget, spent }: { budget: Budget; spent: number }) {
  const percent = budget.amount > 0 ? (spent / budget.amount) * 100 : 0;
  return <div className="budget-summary-visual"><div className="budget-summary-caption"><span>Budget utilization</span><strong>{percent.toFixed(0)}%</strong></div><div className="budget-summary-track"><i style={{ width: `${Math.min(percent, 100)}%` }} /></div></div>;
}
