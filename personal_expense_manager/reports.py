"""
Reports Module for Personal Expenses & Smart Budget Management System
---------------------------------------------------------------------
Academic Demonstration Concepts:
- File handling and binary streaming in memory (io.StringIO, io.BytesIO)
- CSV serialization with Python's csv module and Pandas
- Dynamic PDF generation with ReportLab (flowables, styles, tables)
- XML entity escaping for secure, robust PDF document compilation
- Multi-page table layout and pagination styling
- Publication-ready financial typography and color palettes
"""

import io
import csv
import html
import re
import calendar
from datetime import datetime, date
from typing import List, Dict, Any, Optional
import pandas as pd

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

from database import (
    get_expenses_by_month,
    get_income_by_month,
    get_unified_transactions
)
from expense_manager import get_category_wise_spending, get_monthly_expense_total
from income_manager import get_monthly_income_total, get_monthly_financial_summary
from budget_manager import get_overall_budget_summary, get_category_budgets_table


# ---------------------------------------------------------------------------
# TEXT SANITIZATION UTILITIES FOR PDF
# ---------------------------------------------------------------------------

def clean_pdf_text(text: Any, max_len: Optional[int] = None) -> str:
    """
    Sanitize text strings for ReportLab Platypus Paragraphs:
    1. Replaces Unicode Rupee symbol with 'Rs. ' to prevent font rendering boxes.
    2. Strips out non-ASCII symbols and emoji glyphs unhandled by Type 1 PostScript fonts.
    3. Escapes XML/HTML entities (&, <, >) to prevent paraparser syntax errors.
    4. Safely truncates length if specified.
    """
    if text is None:
        return ""
    s = str(text)
    # Replace Rupee symbol with Rs.
    s = s.replace("₹", "Rs. ")
    # Remove emoji characters and non-standard symbols
    s = re.sub(r'[\U00010000-\U0010ffff]', '', s)
    s = re.sub(r'[\u2600-\u27bf]', '', s)  # Dingbats / miscellaneous symbols
    s = "".join(ch for ch in s if ord(ch) < 1000 or ch in ("\n", "\t"))
    s = s.strip()
    if max_len and len(s) > max_len:
        s = s[:max_len] + "..."
    # Always escape HTML / XML tags so paraparser will never fail
    return html.escape(s)


# ---------------------------------------------------------------------------
# CSV EXPORT (FEATURE 12)
# ---------------------------------------------------------------------------

def generate_csv_report(
    transactions: List[Dict[str, Any]],
    year: Optional[int] = None,
    month: Optional[int] = None,
    db_path: Optional[str] = None
) -> str:
    """
    Generate CSV string representation of the monthly report.
    Includes:
    - Executive Financial Summary (Income, Expenses, Net Balance, Budget Limit, Utilization)
    - Category-wise Spending Breakdown
    - Detailed Transaction Ledger
    """
    output = io.StringIO()
    writer = csv.writer(output)

    # If period is supplied, include complete Executive Summary & Category Breakdown
    if year is not None and month is not None:
        month_name = calendar.month_name[month]
        summary = get_monthly_financial_summary(year, month, db_path=db_path)
        overall_budget = get_overall_budget_summary(year, month, db_path=db_path)
        cat_df = get_category_wise_spending(year, month, db_path=db_path)

        # Header section
        writer.writerow(["PERSONAL EXPENSES & SMART BUDGET MANAGEMENT SYSTEM"])
        writer.writerow([f"Monthly Financial Report - {month_name} {year}"])
        writer.writerow([f"Generated On: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"])
        writer.writerow([])

        # Section 1: Financial Summary
        writer.writerow(["--- EXECUTIVE FINANCIAL SUMMARY ---"])
        writer.writerow(["Metric", "Amount (INR)", "Status / Notes"])
        writer.writerow(["Total Income Recorded", f"{summary['income']:.2f}", "Total Inflow"])
        writer.writerow(["Total Expenses Incurred", f"{summary['expenses']:.2f}", "Total Outflow"])
        writer.writerow(["Remaining Balance (Savings)", f"{summary['balance']:.2f}", f"{summary['savings_pct']}% savings rate" if not summary["is_deficit"] else "DEFICIT"])
        writer.writerow(["Allocated Monthly Budget", f"{overall_budget['budget_amount']:.2f}" if overall_budget["has_budget"] else "Not Set", overall_budget["label"]])
        writer.writerow(["Budget Utilization", f"{overall_budget['utilization']:.1f}%" if overall_budget["has_budget"] else "N/A", overall_budget["tier"].upper()])
        writer.writerow([])

        # Section 2: Category Breakdown
        writer.writerow(["--- CATEGORY-WISE SPENDING BREAKDOWN ---"])
        writer.writerow(["Category", "Transactions Count", "Total Spent (INR)", "Percentage Share (%)"])
        if not cat_df.empty:
            for _, row in cat_df.iterrows():
                writer.writerow([
                    row["category"],
                    row["count"],
                    f"{row['total_amount']:.2f}",
                    f"{row['percentage']:.1f}%"
                ])
        else:
            writer.writerow(["No expense categories recorded for this month.", "", "", ""])
        writer.writerow([])

        # Section 3: Detailed Transactions Header
        writer.writerow(["--- DETAILED TRANSACTION LOG ---"])

    # Transaction Columns Header
    writer.writerow([
        "Transaction ID",
        "Transaction Name",
        "Type",
        "Category / Source",
        "Amount (INR)",
        "Date",
        "Payment Method",
        "Description",
        "Sample Data"
    ])

    for tx in transactions:
        writer.writerow([
            tx.get("id", ""),
            tx.get("name", ""),
            tx.get("type", ""),
            tx.get("category_or_source", ""),
            f"{float(tx.get('amount', 0)):.2f}",
            tx.get("date", ""),
            tx.get("payment_method", "N/A"),
            tx.get("description", ""),
            "Yes" if tx.get("is_sample", 0) else "No"
        ])

    return output.getvalue()


# ---------------------------------------------------------------------------
# PDF REPORT GENERATION (FEATURE 12)
# ---------------------------------------------------------------------------

def generate_pdf_report(year: int, month: int, db_path: Optional[str] = None) -> bytes:
    """
    Generate a complete, professionally formatted PDF report for the selected month.
    Includes:
    - Executive Financial Overview (Income, Expenses, Net Savings, Budget)
    - Category-wise Spending Breakdown Table
    - Chronological Transaction Log (Full multi-page table)
    Returns raw PDF bytes for Streamlit st.download_button.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    # Custom typography styles
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#1E3A8A"),
        alignment=TA_LEFT
    )

    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#64748B"),
        alignment=TA_LEFT
    )

    section_heading = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=17,
        textColor=colors.HexColor("#0F172A"),
        spaceBefore=12,
        spaceAfter=6
    )

    cell_style = ParagraphStyle(
        "CellNormal",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#1E293B")
    )

    cell_header = ParagraphStyle(
        "CellHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=12,
        textColor=colors.white
    )

    story = []

    # Title & Metadata
    month_name = calendar.month_name[month]
    now_str = datetime.now().strftime("%d %B %Y, %I:%M %p")

    story.append(Paragraph("Personal Expenses &amp; Smart Budget Management System", title_style))
    story.append(Paragraph(f"Monthly Financial Summary Report &bull; <b>{month_name} {year}</b> &bull; Generated: {now_str}", subtitle_style))
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#1E3A8A"), spaceAfter=15))

    # SECTION 1: EXECUTIVE FINANCIAL SUMMARY
    summary = get_monthly_financial_summary(year, month, db_path=db_path)
    overall_budget = get_overall_budget_summary(year, month, db_path=db_path)

    story.append(Paragraph("1. Executive Financial Summary", section_heading))

    budget_status_clean = clean_pdf_text(overall_budget.get("message", ""))
    summary_data = [
        [
            Paragraph("<b>Metric</b>", cell_header),
            Paragraph("<b>Amount (INR)</b>", cell_header),
            Paragraph("<b>Status / Analysis</b>", cell_header)
        ],
        [
            Paragraph("Total Income Recorded", cell_style),
            Paragraph(f"Rs. {summary['income']:,.2f}", cell_style),
            Paragraph("Monthly Inflow", cell_style)
        ],
        [
            Paragraph("Total Expenses Incurred", cell_style),
            Paragraph(f"Rs. {summary['expenses']:,.2f}", cell_style),
            Paragraph("Monthly Outflow", cell_style)
        ],
        [
            Paragraph("Net Remaining Balance (Savings)", cell_style),
            Paragraph(f"Rs. {summary['balance']:,.2f}", cell_style),
            Paragraph(f"{summary['savings_pct']}% savings rate" if not summary["is_deficit"] else "DEFICIT (Expenses exceed Income)", cell_style)
        ],
        [
            Paragraph("Allocated Monthly Budget", cell_style),
            Paragraph(f"Rs. {overall_budget['budget_amount']:,.2f}" if overall_budget["has_budget"] else "Not Set", cell_style),
            Paragraph(clean_pdf_text(overall_budget["label"]), cell_style)
        ],
        [
            Paragraph("Budget Utilization", cell_style),
            Paragraph(f"{overall_budget['utilization']:.1f}%" if overall_budget["has_budget"] else "N/A", cell_style),
            Paragraph(budget_status_clean, cell_style)
        ]
    ]

    summary_table = Table(summary_data, colWidths=[180, 140, 200])
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E3A8A")),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 15))

    # SECTION 2: CATEGORY-WISE EXPENDITURE
    story.append(Paragraph("2. Category-wise Spending Breakdown", section_heading))
    cat_df = get_category_wise_spending(year, month, db_path=db_path)

    if not cat_df.empty:
        cat_table_data = [
            [
                Paragraph("<b>Category</b>", cell_header),
                Paragraph("<b>Transactions</b>", cell_header),
                Paragraph("<b>Total Spent (INR)</b>", cell_header),
                Paragraph("<b>Share of Total</b>", cell_header)
            ]
        ]
        for _, row in cat_df.iterrows():
            cat_table_data.append([
                Paragraph(clean_pdf_text(row['category']), cell_style),
                Paragraph(str(row["count"]), cell_style),
                Paragraph(f"Rs. {row['total_amount']:,.2f}", cell_style),
                Paragraph(f"{row['percentage']:.1f}%", cell_style)
            ])

        cat_table = Table(cat_table_data, colWidths=[160, 100, 130, 130])
        cat_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E3A8A")),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(cat_table)
    else:
        story.append(Paragraph("<i>No expense records recorded for this period.</i>", cell_style))

    story.append(Spacer(1, 15))

    # SECTION 3: TRANSACTION LOG (FULL MULTI-PAGE TABLE)
    story.append(Paragraph("3. Transaction Activity Log", section_heading))

    start_date = f"{year:04d}-{month:02d}-01"
    end_date = f"{year:04d}-{month:02d}-{calendar.monthrange(year, month)[1]:02d}"
    transactions = get_unified_transactions(start_date=start_date, end_date=end_date, db_path=db_path)

    if transactions:
        tx_table_data = [
            [
                Paragraph("<b>Date</b>", cell_header),
                Paragraph("<b>Name / Source</b>", cell_header),
                Paragraph("<b>Type</b>", cell_header),
                Paragraph("<b>Category</b>", cell_header),
                Paragraph("<b>Method</b>", cell_header),
                Paragraph("<b>Amount (INR)</b>", cell_header)
            ]
        ]

        for tx in transactions:
            amt_prefix = "+" if tx["type"] == "Income" else "-"
            amt_str = f"{amt_prefix} Rs. {float(tx['amount']):,.2f}"
            tx_table_data.append([
                Paragraph(clean_pdf_text(tx.get("date", "")), cell_style),
                Paragraph(clean_pdf_text(tx.get("name", ""), max_len=30), cell_style),
                Paragraph(clean_pdf_text(tx.get("type", "")), cell_style),
                Paragraph(clean_pdf_text(tx.get("category_or_source", ""), max_len=24), cell_style),
                Paragraph(clean_pdf_text(tx.get("payment_method", "N/A"), max_len=18), cell_style),
                Paragraph(amt_str, cell_style)
            ])

        tx_table = Table(tx_table_data, colWidths=[65, 125, 60, 100, 85, 85], repeatRows=1)
        tx_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E3A8A")),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        story.append(tx_table)
    else:
        story.append(Paragraph("<i>No transactions recorded for this period.</i>", cell_style))

    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#CBD5E1"), spaceAfter=10))
    story.append(Paragraph("Personal Expenses &amp; Smart Budget Management System &bull; BTech CSE Python Programming Project", subtitle_style))

    doc.build(story)
    return buffer.getvalue()
