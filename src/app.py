import streamlit as st
import SessionState

import json
import requests

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from utils import search_data, prep_df

ss = SessionState.get(api_keys=None, search_result=None, search_button=False, )

st.title('Stocks checking tool')

if ss.api_keys is None:
    uploaded_file = st.file_uploader("Upload Rapid API keys", type=['txt'])
    if uploaded_file is not None:
        api_keys = json.load(uploaded_file)
    else:
        api_keys = None

    if api_keys is not None:
        if not isinstance(api_keys, dict):
            ss.api_keys = None
        elif 'x-rapidapi-key' not in api_keys.keys():
            ss.api_keys = None
        elif 'x-rapidapi-host' not in api_keys.keys():
            ss.api_keys = None
        else:
            ss.api_keys = api_keys

        if ss.api_keys is None:
            st.error('Error in reading keys file')
        else:
            st.success('API Keys loaded')
            st.button('OK')

symbol = st.text_input('Symbol', value='AJBU')
region = st.text_input('Region', value='SI')

if (region == 'US') and (symbol.endswith('.US')):
    symbol = symbol[:-3]
elif (region != 'US') and (not symbol.endswith(f'.{region}')):
     symbol += f'.{region}'

if st.button('Search'):
    if ss.api_keys is None:
        st.error('Please load API keys first')
    else:
        ss.search_button = True

if ss.search_button:
    if ss.search_result is not None:
        if (ss.search_result['symbol'] == symbol) and (ss.search_result['region'] == region):
            st.info('Fetching result from cache')
        else:
            ss.search_result = search_data(symbol, region, ss.api_keys)
    else:
        ss.search_result = search_data(symbol, region, ss.api_keys)
    ss.search_button = False

if ss.search_result is not None:
    df = prep_df(ss.search_result)
    st.write(df.style.format({'return_on_equity': '{:.3f}',
                              'return_on_asset': '{:.3f}',
                              'net_margin': '{:.3f}',
                              'current_ratio': '{:.2f}',
                              'debt_to_equity_ratio': '{:.3f}'}))

    year = df['year'][0]
    return_on_equity = df['return_on_equity'][0] * 100
    return_on_asset = df['return_on_asset'][0] * 100
    net_margin = df['net_margin'][0] * 100
    days_sales_outstanding = df['days_sales_outstanding'][0]
    days_payable_outstanding = df['days_payable_outstanding'][0]
    current_ratio = df['current_ratio'][0] * 100
    debt_to_equity_ratio = df['debt_to_equity_ratio'][0] * 100

    if 'days_inventory' in df.columns:
        days_inventory = df['days_inventory'][0]
        cash_conversion_cycle = df['cash_conversion_cycle'][0]
    else:
        days_inventory = None
        cash_conversion_cycle = None

    st.header(f'Year: {year} \n')

    st.subheader('Return on Equity')
    st.write(f'Return on Equity: {"{:.2f}".format(return_on_equity)}%')
    st.write('Return on Equity is a measure of how profitable a company is based on how much equity is being invested in.')
    st.write('ROE = Net Income / Equity')
    st.write('Higher = Better')
    
    st.subheader('Return on Asset')
    st.write(f'Return on Asset: {"{:.2f}".format(return_on_asset)}%')
    st.write('Return on Asset is a measure of how profitable a company is based on how much assets have been invested to generate that profit.')
    st.write('ROA = Net Income / Total Assets')
    st.write('Higher = Better')

    st.subheader('Net Margin')
    st.write(f'Net Margin: {"{:.2f}".format(net_margin)}%')
    st.write('Net Margin is a measure of how much the company is earning from selling its product and services.')
    st.write('Net Margin = Net Income / Revenue')
    st.write('Higher = Better')
    
    st.subheader('Days of Sales Outstanding')
    st.write(f'Days of Sales Outstanding: {"{:.1f}".format(days_sales_outstanding)} Days')
    st.write('Number of days need to collect back the money after sending invoice')
    st.write('Average Account Receivable/ Revenue * 365')
    st.write('Shorter = Better')
    
    st.subheader('Days of Payable Outstanding')
    st.write(f'Days of Payable Outstanding: {"{:.1f}".format(days_payable_outstanding)} Days')
    st.write('Number of days company takes to pay the supplier')
    st.write('Average Account Payable/ (Revenue - Gross Profit) * 365')
    st.write('Longer = Better, but too long might means cash flow issue, best around 6 months')
    
    if days_inventory is not None:
        st.subheader('Days of Inventory')
        st.write(f'Days of Inventory: {"{:.2f}".format(days_inventory)} Days')
        st.write('Number of days takes to turn over all the inventory')
        st.write('Average Inventory/ (Revenue - Gross Profit) * 365')
        st.write('Shorter = Better')
    
    if cash_conversion_cycle is not None:
        st.subheader('Cash conversion cycle')
        st.write(f'Return on equity: {"{:.2f}".format(cash_conversion_cycle)} Days')
        st.write('The time it takes for a company to convert its investments in inventory and other resources into cash flows from sales')
        st.write('Days of Sales Outstanding + Days of Inventory - Days of Payable Outstanding')
        st.write('Shorter = Better, can even be negative')
    
    st.subheader('Current Ratio')
    st.write(f'Current Ratio: {"{:.2f}".format(current_ratio)}%')
    st.write('Do company have enough liquid and short term asset to meet short term liability')
    st.write('Current Ratio = Current asset / current liability')
    st.write('Higher = Better, Danger if less than 100%')

    st.subheader('Debt to Equity Ratio')
    st.write(f'Debt to Equity Ratio: {"{:.2f}".format(debt_to_equity_ratio)}%')
    st.write('If it is more than 100%, then company have more debt than equity')
    st.write('Debt to Equity Ratio = Total debt (current and non-current) / equity')
    st.write('Lower = Better, Danger if more than 100%')