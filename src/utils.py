import json
import requests
import pandas as pd

def prep_df(search_result):
    year_ratio = search_result['ratio']
    year_list = list(year_ratio.keys())
    ratio_list = list(year_ratio[year_list[0]].keys())

    pd_dict = {'year': year_list}
    for ratio in ratio_list:
        pd_dict[ratio] = []
        for year in year_list:
            pd_dict[ratio].append(year_ratio[year][ratio])
    df = pd.DataFrame(pd_dict)
    df = df.sort_values('year', ascending=False)
    return df


def search_data(symbol, region, api_keys):

    querystring = {'symbol': symbol, 'region': region}
    headers = api_keys

    financial_api = 'https://apidojo-yahoo-finance-v1.p.rapidapi.com/stock/v2/get-financials'

    financial_response = requests.request("GET", financial_api, headers=headers, params=querystring)

    search_result = {'symbol': symbol, 'region': region}
    if len(financial_response.text) == 0:
        search_result['status'] = 1
        return search_result
    else:
        financial_data = json.loads(financial_response.text)
        search_result['ratio'] = process_financial(financial_data)

        return search_result


def process_financial(financial_data):
    incomeStatementHistory = financial_data['incomeStatementHistory']['incomeStatementHistory']
    processed_income_statement_history = process_income_statement_history(incomeStatementHistory)

    balanceSheetHistory = financial_data['balanceSheetHistory']['balanceSheetStatements']
    processed_balance_sheet_history = process_balance_sheet_history(balanceSheetHistory)

    year_ratio = {}
    year_list = processed_income_statement_history.keys()
    for year in year_list:
        if year in processed_balance_sheet_history.keys():
            process_income_statement = processed_income_statement_history[year]
            processed_balance_sheet = processed_balance_sheet_history[year]
            ratio = calculate_ratio(process_income_statement, processed_balance_sheet)
            year_ratio[year] = ratio

    return year_ratio


def calculate_ratio(process_income_statement, processed_balance_sheet):
    return_on_equity = process_income_statement['net_income'] / processed_balance_sheet['equity']
    return_on_asset = process_income_statement['net_income'] / processed_balance_sheet['asset']
    net_margin = process_income_statement['net_income'] / process_income_statement['revenue']
    days_sales_outstanding = processed_balance_sheet['account_receivable'] / process_income_statement['revenue'] * 365
    days_payable_outstanding = processed_balance_sheet['account_payable'] / process_income_statement['cost_of_revenue'] * 365
    current_ratio = processed_balance_sheet['current_asset'] / processed_balance_sheet['current_liability']
    debt_to_equity_ratio = processed_balance_sheet['total_debt'] / processed_balance_sheet['equity']

    ratio_dict = {'return_on_equity': return_on_equity,
                  'return_on_asset': return_on_asset,
                  'net_margin': net_margin,
                  'days_sales_outstanding': days_sales_outstanding,
                  'days_payable_outstanding': days_payable_outstanding,
                  'current_ratio': current_ratio,
                  'debt_to_equity_ratio': debt_to_equity_ratio}

    if 'inventory' in processed_balance_sheet.keys():
        days_inventory = processed_balance_sheet['inventory'] / process_income_statement['cost_of_revenue'] * 365
        cash_conversion_cycle = days_sales_outstanding + days_inventory - days_payable_outstanding
        ratio_dict['days_inventory'] = days_inventory
        ratio_dict['cash_conversion_cycle'] = cash_conversion_cycle
    
    return ratio_dict


def process_income_statement_history(incomeStatementHistory):
    processed_income_statement_history = {}
    for year_income_statement in incomeStatementHistory:
        year, processed_income_statement = process_income_statement(year_income_statement)
        processed_income_statement_history[year] = processed_income_statement
    return processed_income_statement_history


def process_balance_sheet_history(balanceSheetHistory):
    processed_balance_sheet_history = {}
    for year_balance_sheet in balanceSheetHistory:
        year, processed_balance_sheet = process_balance_sheet(year_balance_sheet)
        processed_balance_sheet_history[year] = processed_balance_sheet
    return processed_balance_sheet_history


def process_income_statement(income_statement):
    year = income_statement['endDate']['fmt'].split('-')[0]
    
    net_income = income_statement['netIncome']['raw']
    gross_profit = income_statement['grossProfit']['raw']
    revenue = income_statement['totalRevenue']['raw']
    cost_of_revenue = income_statement['costOfRevenue']['raw'] # aka cost of good sold (revenue - gross profit)

    process_income_statement = {'net_income': net_income,
                                'gross_profit': gross_profit,
                                'revenue': revenue,
                                'cost_of_revenue': cost_of_revenue}
    
    return year, process_income_statement

def process_balance_sheet(balance_sheet):
    year = balance_sheet['endDate']['fmt'].split('-')[0]

    equity = balance_sheet['totalStockholderEquity']['raw']
    asset = balance_sheet['totalAssets']['raw']

    account_receivable = balance_sheet['netReceivables']['raw']
    account_payable = balance_sheet['accountsPayable']['raw']

    current_asset = balance_sheet['totalCurrentAssets']['raw']
    current_liability = balance_sheet['totalCurrentLiabilities']['raw']

    short_debt = balance_sheet['shortLongTermDebt']['raw']
    long_debt = balance_sheet['longTermDebt']['raw']
    total_debt = short_debt + long_debt

    processed_balance_sheet = {'equity': equity,
                               'asset': asset,
                               'account_receivable': account_receivable,
                               'account_payable': account_payable,
                               'current_asset': current_asset,
                               'current_liability': current_liability,
                               'short_debt': short_debt,
                               'long_debt': long_debt,
                               'total_debt': total_debt
                               }

    if 'inventory' in balance_sheet.keys():
        inventory = balance_sheet['accountsPayable']['raw']
        processed_balance_sheet['inventory'] = inventory

    return year, processed_balance_sheet



    """
    Return on Equity = Net Income / Equity (higher the better)
    Return on Asset = Net Income / Asset (higher the better)
    Net Margin = Net Income/ Revenue (higher the better)
    Days of Sales Outstanding = Average Account Receivable/ Revenue * 365 (Number of days need to collect back the money after sending invoice) (lower the better)
    Days of Payable Outstanding = Average Account Payable/ (Revenue - Gross Profit) * 365 (Number of days company takes to pay the supplier) (longer the better, but too long might means cash flow issue, best around 6 months)
    Days of Inventory = Average Inventory/ (Revenue - Gross Profit) * 365 (lower the better) (number of days takes to turn over all the inventory)
    Cash conversion cycle = Days of Sales Outstanding + Days of Inventory - Days of Payable Outstanding (lower the better, can even be negative if the company can collect money first before paying supplier)
    Current Ratio = Current asset / current liability (Do company have enough short term liquid asset to meet short term liability, higher the better)
    Debt to Equity Ratio = Total debt (current and non-current) / equity (if it is more than 1, then company have more debt than equity, lower the better, danger if more than 1)
    Price-to-Earnings Ratio (PE ratio) = Stock price/ earning per share (how many years it takes for the earning takes to achieve its valuation, lower the better, higher the 'more expensive')
    Price-to-Book Ratio = stock price/ equity per share (Use for company with large asset base like REIT and bank)

    """
