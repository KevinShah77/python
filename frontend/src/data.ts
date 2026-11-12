import type { AppData, Budget, Expense, Income, Category, IncomeSource, PaymentMethod } from './types';

const monthKey = (year: number, monthIndex: number) => `${year}-${String(monthIndex + 1).padStart(2, '0')}`;

function shiftedPeriod(today: Date, offset: number) {
  const shifted = new Date(today.getFullYear(), today.getMonth() + offset, 1);
  return { year: shifted.getFullYear(), month: shifted.getMonth() };
}

function dateFor(today: Date, offset: number, day: number) {
  const { year, month } = shiftedPeriod(today, offset);
  const upperBound = new Date(year, month + 1, 0).getDate();
  const safeDay = Math.min(Math.max(day, 1), upperBound, offset === 0 ? today.getDate() : upperBound);
  return `${year}-${String(month + 1).padStart(2, '0')}-${String(safeDay).padStart(2, '0')}`;
}

function periodFor(today: Date, offset: number) {
  const { year, month } = shiftedPeriod(today, offset);
  return monthKey(year, month);
}

export function createSeedData(today = new Date()): AppData {
  const expenseRows: Array<[string, number, Category, number, PaymentMethod, string, number]> = [
    ['Campus canteen lunch', 180, 'Food & Dining', 2, 'UPI / GPay / PhonePe', 'Lunch with the project team', 0],
    ['Metro smartcard recharge', 900, 'Transportation', 3, 'Debit Card', 'Daily college commute', 0],
    ['Python programming book', 1150, 'Education', 4, 'UPI / GPay / PhonePe', 'Reference book for semester 5', 0],
    ['Weekly groceries & snacks', 1450, 'Food & Dining', 5, 'UPI / GPay / PhonePe', 'Hostel essentials and fruit', 0],
    ['Mobile & fiber bill', 1299, 'Bills & Utilities', 6, 'Net Banking', 'Monthly connection plan', 0],
    ['Semester exam & lab fees', 3200, 'Education', 8, 'Net Banking', 'University examination enrollment', 0],
    ['Movie night', 650, 'Entertainment', 9, 'UPI / GPay / PhonePe', 'Cinema and popcorn', 0],
    ['Pharmacy & vitamins', 480, 'Healthcare', 11, 'Cash', 'First-aid and vitamin refill', 0],
    ['Denim & everyday basics', 2499, 'Shopping', 13, 'Credit Card', 'A planned wardrobe refresh', 0],
    ['Haircut & grooming', 450, 'Personal Care', 14, 'UPI / GPay / PhonePe', 'Monthly haircut', 0],
    ['Coffee & study session', 340, 'Food & Dining', 16, 'UPI / GPay / PhonePe', 'Cafe stop with classmates', 0],
    ['Cab to the station', 420, 'Transportation', 18, 'UPI / GPay / PhonePe', 'Late-evening ride', 0],
    ['Cloud server hosting', 780, 'Bills & Utilities', 20, 'Credit Card', 'Student project hosting', 0],
    ['Weekend trip fuel share', 1600, 'Travel', 22, 'UPI / GPay / PhonePe', 'Shared ride to the hills', 0],
    ['Wireless earbuds', 1999, 'Shopping', 24, 'Debit Card', 'Replacement pair', 0],
    ['Dinner with roommates', 890, 'Food & Dining', 26, 'UPI / GPay / PhonePe', 'Celebrated project milestone', 0],
    ['Monthly meals & snacks', 2800, 'Food & Dining', 3, 'UPI / GPay / PhonePe', 'Campus dining and groceries', 1],
    ['Metro recharge', 850, 'Transportation', 4, 'Debit Card', 'Transit for the month', 1],
    ['Online certification course', 1899, 'Education', 8, 'Credit Card', 'Python specialization', 1],
    ['Shared hostel Wi-Fi', 600, 'Bills & Utilities', 10, 'Cash', 'Monthly broadband share', 1],
    ['Dental checkup', 1200, 'Healthcare', 14, 'UPI / GPay / PhonePe', 'Routine visit', 1],
    ['Running shoes', 2999, 'Shopping', 18, 'Credit Card', 'Daily training shoes', 1],
    ['Streaming subscriptions', 799, 'Entertainment', 20, 'Debit Card', 'Student streaming plan', 1],
    ['Train ticket home', 650, 'Travel', 24, 'Net Banking', 'Weekend trip home', 1],
    ['Stationery & printouts', 380, 'Education', 26, 'Cash', 'Project notes and binding', 1],
    ['Skincare essentials', 550, 'Personal Care', 28, 'UPI / GPay / PhonePe', 'Monthly essentials', 1],
    ['Monthly food & dining', 3400, 'Food & Dining', 4, 'UPI / GPay / PhonePe', 'Meals and groceries', 2],
    ['Bus passes & bicycle repair', 950, 'Transportation', 7, 'Debit Card', 'Commute and tune-up', 2],
    ['Textbooks & lab manuals', 1450, 'Education', 11, 'Cash', 'Course materials', 2],
    ['Electricity & maintenance', 800, 'Bills & Utilities', 15, 'Net Banking', 'Room utility share', 2],
    ['Festival shopping', 3500, 'Shopping', 20, 'Credit Card', 'Festive outfit and gifts', 2],
    ['Concert & campus fest', 1000, 'Entertainment', 25, 'UPI / GPay / PhonePe', 'Annual campus fest pass', 2],
  ];

  const expenses: Expense[] = expenseRows.map(([name, amount, category, day, paymentMethod, description, offset], index) => ({
    id: index + 1,
    type: 'expense',
    name,
    amount,
    category,
    date: dateFor(today, -offset, day),
    paymentMethod,
    description,
  }));

  const incomeRows: Array<[IncomeSource, string, number, number, string, number]> = [
    ['Allowance', 'Monthly allowance', 18000, 1, 'Regular monthly support', 0],
    ['Freelancing', 'Freelance design project', 12500, 10, 'Client project milestone', 0],
    ['Scholarship', 'Merit scholarship', 5000, 15, 'Academic achievement award', 0],
    ['Allowance', 'Monthly allowance', 18000, 1, 'Regular monthly support', 1],
    ['Freelancing', 'Freelance development work', 15000, 12, 'Website delivery payment', 1],
    ['Allowance', 'Monthly allowance', 18000, 1, 'Regular monthly support', 2],
    ['Scholarship', 'Peer tutoring stipend', 6000, 18, 'Tutoring support for first-years', 2],
  ];

  const income: Income[] = incomeRows.map(([source, _name, amount, day, description, offset], index) => ({
    id: index + 1,
    type: 'income',
    source,
    amount,
    date: dateFor(today, -offset, day),
    description,
  }));

  const budgetRows: Array<[string, number]> = [
    ['Overall', 25000],
    ['Food & Dining', 6000],
    ['Transportation', 2000],
    ['Shopping', 4000],
    ['Education', 5000],
    ['Healthcare', 1500],
    ['Entertainment', 2000],
    ['Bills & Utilities', 2500],
    ['Travel', 2500],
    ['Personal Care', 1000],
  ];
  const budgets: Budget[] = budgetRows.map(([category, amount], index) => ({
    id: index + 1,
    category: category as 'Overall' | Category,
    amount,
    period: periodFor(today, 0),
  }));
  budgets.push({ id: 11, category: 'Overall', amount: 22000, period: periodFor(today, -1) });
  budgets.push({ id: 12, category: 'Food & Dining', amount: 5500, period: periodFor(today, -1) });
  budgets.push({ id: 13, category: 'Transportation', amount: 1800, period: periodFor(today, -1) });
  budgets.push({ id: 14, category: 'Education', amount: 4000, period: periodFor(today, -1) });
  budgets.push({ id: 15, category: 'Shopping', amount: 3500, period: periodFor(today, -1) });

  const futureDate1 = new Date(today.getFullYear(), today.getMonth() + 6, 15).toISOString().slice(0, 10);
  const futureDate2 = new Date(today.getFullYear(), today.getMonth() + 1, 28).toISOString().slice(0, 10);
  const futureDate3 = new Date(today.getFullYear(), today.getMonth() + 3, 10).toISOString().slice(0, 10);

  const savings_goals: AppData['savings_goals'] = [
    {
      id: 1,
      user_id: 'default_user',
      goal_name: 'Emergency Fund',
      target_amount: 50000,
      current_saved_amount: 35000,
      remaining_amount: 15000,
      progress_percentage: 70.0,
      target_date: futureDate1,
      description: '3-month reserve for hostel, medical, and emergency living expenses.',
      created_date: today.toISOString().slice(0, 10),
      status: 'In Progress',
      is_sample: 1,
    },
    {
      id: 2,
      user_id: 'default_user',
      goal_name: 'New Laptop / Tech Gear',
      target_amount: 65000,
      current_saved_amount: 65000,
      remaining_amount: 0,
      progress_percentage: 100.0,
      target_date: futureDate2,
      description: 'MacBook / ThinkPad upgrade for coding and software development.',
      created_date: today.toISOString().slice(0, 10),
      status: 'Completed',
      is_sample: 1,
    },
    {
      id: 3,
      user_id: 'default_user',
      goal_name: 'Goa Vacation Trip',
      target_amount: 20000,
      current_saved_amount: 8500,
      remaining_amount: 11500,
      progress_percentage: 42.5,
      target_date: futureDate3,
      description: 'End of semester holiday trip with college friends.',
      created_date: today.toISOString().slice(0, 10),
      status: 'In Progress',
      is_sample: 1,
    },
  ];

  return { expenses, income, budgets, savings_goals };
}
