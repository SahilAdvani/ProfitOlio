# import images
import yfinance as yf
import pandas as pd
import streamlit as st

import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.title('Portfolio Management System')

if 'portfolio' not in st.session_state:
    st.session_state['portfolio'] = pd.DataFrame(columns=[
        'Stock Symbol', 'Currency', 'Quantity', 'Average Purchase Price', 
        'Date of Purchase', 'Current Price', 'Current Value', 
        'Amount Invested', 'Profit/ Loss', 'Profit/ Loss %', 
        'Current Value INR', 'Amount Invested INR'
    ])

if not st.session_state.portfolio.empty:

    total_value = st.session_state.portfolio['Current Value'].sum()
    total_investment = st.session_state.portfolio['Amount Invested'].sum()
    total_profit_loss = st.session_state.portfolio['Profit/ Loss'].sum()
    if total_investment > 0:
        total_profit_loss_percent = (total_profit_loss / total_investment) * 100
    else:
        total_profit_loss_percent = 0
else:
    total_value = 0
    total_investment = 0
    total_profit_loss = 0
    total_profit_loss_percent = 0

def fetch_usd_to_inr_exchange_rate():
    exchange_rate_info = yf.Ticker("USDINR=X")
    try:
        usd_to_inr = exchange_rate_info.history(period="1d")['Close'].iloc[-1]
    except IndexError:
        try:
            usd_to_inr = exchange_rate_info.history(period="5d")['Close'].dropna().iloc[-1]
        except IndexError:
            st.error("Failed to fetch the USD to INR exchange rate. Please try again later.")
            usd_to_inr = None
    return usd_to_inr

usd_to_inr_rate = fetch_usd_to_inr_exchange_rate()

total_value_inr = st.session_state.portfolio['Current Value INR'].sum()
total_investment_inr = st.session_state.portfolio['Amount Invested INR'].sum()

col1, col2 = st.columns(2)
col1.metric("Total Amount Invested (INR)", f"₹{total_investment_inr:,.2f}")
col2.metric("Current Portfolio Value (INR)", f"₹{total_value_inr:,.2f}")


stock_symbol = st.text_input('Stock Symbol', 'AAPL')
currency = st.selectbox('Currency', ['USD', 'INR'])
quantity = st.number_input('Quantity', min_value=0.01, step=0.01, format="%.2f")
average_price = st.number_input('Average Purchase Price', min_value=0.01)
purchase_date = st.date_input("Date of Purchase")
add_button = st.button('Add to Portfolio')

if 'portfolio' not in st.session_state:
    st.session_state.portfolio = pd.DataFrame(columns=['Stock Symbol', 'Currency', 'Quantity', 'Average Purchase Price', 'Date of Purchase', 'Current Price', 'Current Value', 'Amount Invested', 'Profit/ Loss', 'Profit/ Loss %'])


def add_stock_to_portfolio(stock_symbol, quantity, average_price, purchase_date):
    stock_info = yf.Ticker(stock_symbol)
    try:
        current_price = stock_info.history(period='1d')['Close'][-1]
    except IndexError:
        st.error("Failed to fetch current price. Please check the stock symbol.")
        return
    
    current_value_new_stock = quantity * current_price
    amount_invested_new_stock = quantity * average_price
    profit_loss_new_stock = current_value_new_stock - amount_invested_new_stock
    profit_loss_percent_new_stock = (profit_loss_new_stock / amount_invested_new_stock) * 100 if amount_invested_new_stock != 0 else 0
    

    if stock_symbol in st.session_state.portfolio['Stock Symbol'].values:

        index = st.session_state.portfolio[st.session_state.portfolio['Stock Symbol'] == stock_symbol].index[0]
        
        existing_quantity = st.session_state.portfolio.at[index, 'Quantity']
        existing_average_price = st.session_state.portfolio.at[index, 'Average Purchase Price']
        existing_amount_invested = st.session_state.portfolio.at[index, 'Amount Invested']
        
        new_quantity = existing_quantity + quantity
        new_average_price = ((existing_average_price * existing_quantity) + (average_price * quantity)) / new_quantity
        new_amount_invested = existing_amount_invested + amount_invested_new_stock
        new_current_value = new_quantity * current_price
        new_profit_loss = new_current_value - new_amount_invested
        new_profit_loss_percent = (new_profit_loss / new_amount_invested) * 100 if new_amount_invested != 0 else 0
        
        st.session_state.portfolio.at[index, 'Quantity'] = new_quantity
        st.session_state.portfolio.at[index, 'Average Purchase Price'] = new_average_price
        st.session_state.portfolio.at[index, 'Current Price'] = current_price
        st.session_state.portfolio.at[index, 'Current Value'] = new_current_value
        st.session_state.portfolio.at[index, 'Amount Invested'] = new_amount_invested
        st.session_state.portfolio.at[index, 'Profit/ Loss'] = new_profit_loss
        st.session_state.portfolio.at[index, 'Profit/ Loss %'] = new_profit_loss_percent
        
    else:

        if stock_symbol.endswith('.NS'): 
            currency = 'INR'
        else:
            currency = 'USD'  
        new_stock = pd.DataFrame([{
            'Stock Symbol': stock_symbol, 
            'Currency' : currency,
            'Quantity': quantity, 
            'Average Purchase Price': average_price,
            'Date of Purchase': purchase_date, 
            'Current Price': current_price, 
            'Current Value': current_value_new_stock,
            'Amount Invested': amount_invested_new_stock,
            'Profit/ Loss': profit_loss_new_stock,
            'Profit/ Loss %': profit_loss_percent_new_stock
        }])
        
        st.session_state.portfolio = pd.concat([st.session_state.portfolio, new_stock], ignore_index=True)

st.session_state.portfolio = st.session_state.portfolio.copy()


if add_button:
    add_stock_to_portfolio(stock_symbol, quantity, average_price, purchase_date)

usd_to_inr_rate = fetch_usd_to_inr_exchange_rate()

def adjust_currency(row):
    if row['Currency'] == 'USD':
        row['Current Value INR'] = row['Current Value'] * usd_to_inr_rate
        row['Amount Invested INR'] = row['Amount Invested'] * usd_to_inr_rate
    else:
        row['Current Value INR'] = row['Current Value']
        row['Amount Invested INR'] = row['Amount Invested']
    return row

st.session_state.portfolio = st.session_state.portfolio.apply(adjust_currency, axis=1)

def sell_stock_from_portfolio(index, sell_quantity):
    stock = st.session_state.portfolio.loc[index]
    if sell_quantity >= stock['Quantity']:
        st.session_state.portfolio = st.session_state.portfolio.drop(index)
    else:
        st.session_state.portfolio.at[index, 'Quantity'] -= sell_quantity

    st.session_state.portfolio.reset_index(drop=True, inplace=True)


for index, row in st.session_state.portfolio.iterrows():
    cols = st.columns([0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.2, 0.1])
    cols[0].write(row['Stock Symbol'])
    cols[1].write(row['Quantity'])
    sell_quantity = cols[9].number_input('Sell Qty', min_value=0.01, max_value=float(row['Quantity']), step=0.01, format="%.2f", key=f"sell_{index}")
    if cols[9].button('Sell', key=f"sell_btn_{index}"):
        sell_stock_from_portfolio(index, sell_quantity)
    if cols[10].button('Sell All', key=f"sell_all_{index}"):
        sell_stock_from_portfolio(index, row['Quantity'])

def calculate_current_value():
    stock_values = {}
    for _, row in st.session_state.portfolio.iterrows():
        symbol = row['Stock Symbol']
        quantity = row['Quantity']
        stock_info = yf.Ticker(symbol)
        try:
            current_price = (stock_info.history(period='1d')['Close'][-1])
            stock_values[symbol] = current_price * quantity
        except IndexError:
            st.error(f"Failed to fetch current price for {symbol}.")
            continue
    return stock_values

def calculate_current_value_in_inr():
    usd_to_inr_rate = fetch_usd_to_inr_exchange_rate()
    stock_values_in_inr = {}
    
    for _, row in st.session_state.portfolio.iterrows():
        symbol = row['Stock Symbol']
        quantity = row['Quantity']
        currency = row['Currency']

        stock_info = yf.Ticker(symbol)
        try:
            current_price_usd = stock_info.history(period='1d')['Close'][-1]
            if currency == 'USD':
                current_price_inr = current_price_usd * usd_to_inr_rate
            else:
                current_price_inr = current_price_usd 
            stock_values_in_inr[symbol] = current_price_inr * quantity
        except IndexError:
            st.error(f"Failed to fetch current price for {symbol}.")
            continue
    
    return stock_values_in_inr


st.write('Your Portfolio', st.session_state.portfolio)


if not st.session_state.portfolio.empty:
    total_value = st.session_state.portfolio['Current Value INR'].sum()
    total_investment = st.session_state.portfolio['Amount Invested INR'].sum()
    total_profit_loss = st.session_state.portfolio['Profit/ Loss'].sum()
    if total_investment > 0:
        total_profit_loss_percent = (total_profit_loss / total_investment) * 100
    else:
        total_profit_loss_percent = 0
else:
    total_value = 0
    total_investment = 0
    total_profit_loss = 0
    total_profit_loss_percent = 0


if not st.session_state.portfolio.empty:
    stock_values = calculate_current_value_in_inr()
    invested_amounts = st.session_state.portfolio.groupby('Stock Symbol')['Amount Invested INR'].sum()

    if stock_values and not invested_amounts.empty:
        labels_value = list(stock_values.keys())
        values_value = list(stock_values.values())
        labels_invested = invested_amounts.index.tolist()
        values_invested = invested_amounts.values.tolist()
        fig = make_subplots(rows=1, cols=2, specs=[[{'type': 'pie'}, {'type': 'pie'}]])

        fig.add_trace(
            go.Pie(labels=labels_value, values=values_value, hole=.3, title="Current Value INR"),
            row=1, col=1
        )

        fig.add_trace(
            go.Pie(labels=labels_invested, values=values_invested, hole=.3, title="Amount Invested INR"),
            row=1, col=2
        )
        fig.update_layout(
            title_text="Portfolio Distribution",
            annotations=[dict(text='Distribution by Current Value', x=0.18, y=-0.1, font_size=12, showarrow=False),
                        dict(text='Distribution by Amount Invested', x=0.82, y=-0.1, font_size=12, showarrow=False)]
        )

        st.plotly_chart(fig)
    else:
        st.write("Unable to calculate values for the stocks in your portfolio.")
else:
    st.write("Your portfolio is currently empty.")


def calculate_current_value_for_last_month_plotly(period='1mo',interval='1d'):
    for _, row in st.session_state.portfolio.iterrows():
        symbol = row['Stock Symbol']
        stock_info = yf.Ticker(symbol)
        try:
            stock_history = stock_info.history(period=period, interval=interval)
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=stock_history.index, y=stock_history['Close'], mode='lines', name=symbol))
            fig.update_layout(title=f'Stock Price Overview of {symbol}',
                            xaxis_title='Date',
                            yaxis_title='Stock Price')
            st.plotly_chart(fig)

        except Exception as e:
            st.error(f"Failed to fetch current price for {symbol}. Error: {e}")
            continue

period = st.radio('Select Period', ['1mo', '3mo', '1y','5y'], index=0, key='Stock Price Plot')

st.markdown(
    """
    <style>
    .stRadio > div[role="radiogroup"] {
        display: flex;
        flex-direction: row;
        flex-wrap: wrap;
    }

    .stRadio > div[role="radiogroup"] > label {
        flex: 1;
        margin-right: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

if period == '1mo':
    calculate_current_value_for_last_month_plotly(period,'1d')
if period == '3mo':
    calculate_current_value_for_last_month_plotly(period,'1wk')
if period == '1y':
    calculate_current_value_for_last_month_plotly(period,'1mo')
if period == '5y':
    calculate_current_value_for_last_month_plotly(period,'3mo')



def profit_loss_bar_plot(period='1d',interval='1h'):
    for _, row in st.session_state.portfolio.iterrows():
        symbol = row['Stock Symbol']
        stock_info = yf.Ticker(symbol)
        try:
            stock_history = stock_info.history(period=period, interval=interval)
            fig = go.Figure()    
            if row['Current Value'] > row['Amount Invested']:
                fig.add_trace(go.Bar(x=stock_history.index, y=abs(stock_history['Close'] - row['Amount Invested']), name='Profit', marker_color='green'))
            else:
                fig.add_trace(go.Bar(x=stock_history.index, y=abs(stock_history['Close'] - row['Amount Invested']), name='Loss', marker_color='red'))

            fig.update_layout(title=f'Profit/Loss Overview of {symbol}',
                              xaxis_title='Date',
                              yaxis_title='Profit/Loss Amount',
                              barmode='relative')

            st.plotly_chart(fig)

        except Exception as e:
            st.error(f"Failed to plot Profit Loss Overview for {symbol}. Error: {e}")


period = st.radio('Select Period', ['1d', '1wk', '1mo', '3mo', '1y','5y'], index=0, key='Profit/Loss Plot')

st.markdown(
    """
    <style>
    .stRadio > div[role="radiogroup"] {
        display: flex;
        flex-direction: row;
        flex-wrap: wrap;
    }

    .stRadio > div[role="radiogroup"] > label {
        flex: 1;
        margin-right: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True
)



if period == '1mo':
    profit_loss_bar_plot(period, '1d')
if period == '3mo':
    profit_loss_bar_plot(period, '1wk')
if period == '1y':
    profit_loss_bar_plot(period, '1mo')
if period == '5y':
    profit_loss_bar_plot(period, '3mo')
