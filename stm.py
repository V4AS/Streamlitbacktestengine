import streamlit as st
import vectorbt as vbt
import pandas_ta as ta
import plotly.graph_objects as go

def load_data(asset, start_date, end_date, timeframe):
    data = vbt.YFData.download(asset, start=start_date, end=end_date, interval=timeframe)
    return data

indicator_functions = {
    'EMA': lambda df, length, source: ta.ema(df[source.lower()], length=length),
    'SMA': lambda df, length, source: ta.sma(df[source.lower()], length=length),
    'MACD': lambda df, fast, slow, signal, source: ta.macd(df[source.lower()], fast=fast, slow=slow, signal=signal),
    'RSI': lambda df, length, source: ta.rsi(df[source.lower()], length=length),
    'Bollinger Bands': lambda df, length, source, stdev: ta.bbands(df[source.lower()], length=length, std=stdev),
    'ATR': lambda df, length: ta.atr(df['high'], df['low'], df['close'], length=length)
}

st.title('Backtest Your Trading Strategy')
st.sidebar.header('Input Parameters')

asset = st.sidebar.text_input('Asset', value='AAPL')
start_date = st.sidebar.text_input('Start Date (YYYY-MM-DD)', value='2020-01-01')
end_date = st.sidebar.text_input('End Date (YYYY-MM-DD)', value='2024-06-30')
timeframe = st.sidebar.selectbox('Timeframe', ['1m', '2m', '5m', '15m', '30m', '60m', '90m', '1h', '1d', '5d', '1wk', '1mo', '3mo'])

data = load_data(asset, start_date, end_date, timeframe)
dff = data.get()
dff.columns = dff.columns.str.lower()
df = data.get('close')

st.subheader(asset + ' Data Preview')
st.write(dff[['open', 'high', 'low', 'close', 'volume']].tail(10))

# Create the initial candlestick chart
fig = go.Figure()

# Add candlestick trace
fig.add_trace(go.Candlestick(
    x=dff.index,
    open=dff['open'],
    high=dff['high'],
    low=dff['low'],
    close=dff['close'],
    name='Candlestick'
))

fig.update_layout(title=f"{asset} Candlestick Chart", xaxis_title="Date", yaxis_title="Price", xaxis_rangeslider_visible=False)
chart_placeholder = st.plotly_chart(fig, use_container_width=True)

if not df.empty:
    st.sidebar.header('Indicators Selection')
    indicators = ['EMA', 'SMA', 'MACD', 'RSI', 'Bollinger Bands', 'ATR']
    selected_indicators = st.sidebar.multiselect('Select Indicators', indicators)

    params = {}
    if selected_indicators:
        st.sidebar.header('Configure Indicators')
        for indicator in selected_indicators:
            with st.sidebar.expander(f'{indicator} Parameters'):
                if indicator == 'EMA' or indicator == 'SMA':
                    params[indicator] = {
                        'length': st.number_input(f'{indicator} Length', min_value=1, max_value=100, value=20, key=f'{indicator}_length'),
                        'source': st.selectbox(f'{indicator} Source', ['open', 'high', 'low', 'close'], key=f'{indicator}_source')
                    }
                elif indicator == 'MACD':
                    params[indicator] = {
                        'fast': st.number_input('MACD Fast Length', min_value=1, max_value=100, value=12, key='MACD_fast'),
                        'slow': st.number_input('MACD Slow Length', min_value=1, max_value=100, value=26, key='MACD_slow'),
                        'signal': st.number_input('MACD Signal Smoothing', min_value=1, max_value=100, value=9, key='MACD_signal'),
                        'source': st.selectbox('MACD Source', ['open', 'high', 'low', 'close'], key='MACD_source')
                    }
                elif indicator == 'RSI':
                    params[indicator] = {
                        'length': st.number_input('RSI Length', min_value=1, max_value=100, value=14, key='RSI_length'),
                        'source': st.selectbox('RSI Source', ['open', 'high', 'low', 'close'], key='RSI_source')
                    }
                elif indicator == 'Bollinger Bands':
                    params[indicator] = {
                        'length': st.number_input('Bollinger Bands Length', min_value=1, max_value=100, value=20, key='BB_length'),
                        'source': st.selectbox('Bollinger Bands Source', ['open', 'high', 'low', 'close'], key='BB_source'),
                        'stdev': st.number_input('Bollinger Bands Stdev', min_value=1, max_value=10, value=2, key='BB_stdev')
                    }
                elif indicator == 'ATR':
                    params[indicator] = {
                        'length': st.number_input('ATR Length', min_value=1, max_value=100, value=14, key='ATR_length')
                    }

        calculated_indicators = {}
        for indicator in selected_indicators:
            if indicator in indicator_functions:
                calculated_indicators[indicator] = indicator_functions[indicator](dff, **params[indicator])

        # Add indicators to the chart
        for indicator, values in calculated_indicators.items():
            if indicator == 'MACD':
                fig.add_trace(go.Scatter(
                    x=dff.index,
                    y=values['MACD_12_26_9'],
                    mode='lines',
                    name=f"{indicator} Line"
                ))
                fig.add_trace(go.Scatter(
                    x=dff.index,
                    y=values['MACDs_12_26_9'],
                    mode='lines',
                    name=f"{indicator} Signal"
                ))
            elif indicator == 'Bollinger Bands':
                fig.add_trace(go.Scatter(
                    x=dff.index,
                    y=values['BBM_20_2.0'],
                    mode='lines',
                    name=f"{indicator} Middle Band"
                ))
                fig.add_trace(go.Scatter(
                    x=dff.index,
                    y=values['BBU_20_2.0'],
                    mode='lines',
                    name=f"{indicator} Upper Band"
                ))
                fig.add_trace(go.Scatter(
                    x=dff.index,
                    y=values['BBL_20_2.0'],
                    mode='lines',
                    name=f"{indicator} Lower Band"
                ))
            else:
                fig.add_trace(go.Scatter(
                    x=dff.index,
                    y=values,
                    mode='lines',
                    name=f"{indicator} Line"
                ))

        fig.update_layout(title=f"{asset} Candlestick Chart with Indicators", xaxis_title="Date", yaxis_title="Price", xaxis_rangeslider_visible=False)
        chart_placeholder.plotly_chart(fig, use_container_width=True)

    st.sidebar.header('Backtest Configuration')
    initial_cash = st.sidebar.number_input('Initial Cash ($)', min_value=100, value=1000)
    trade_amount = st.sidebar.number_input('Position Size (%)', min_value=0.1, value=0.1)
    if st.sidebar.button('Set Entry and Exit Conditions'):
        st.session_state.show_conditions_window = True

if st.session_state.get('show_conditions_window', False):
    st.subheader("Entry and Exit Conditions")
    direction = st.radio("Backtest Direction", ['Long Only', 'Short Only', 'Both'], key='direction')
    conditions = ['Above', 'Below', 'Cross Over', 'Cross Under']
    against_options = ['open', 'high', 'low', 'close'] + selected_indicators

    if direction in ['Long Only', 'Both']:
        st.subheader('Long Conditions')
        long_entry_condition = st.selectbox('Long Entry Condition', conditions, key='long_entry_condition')
        long_entry_target = st.selectbox('Long Entry Target', against_options, key='long_entry_target')
        long_entry_against = st.selectbox('Long Entry Against', against_options, key='long_entry_against')

        long_exit_condition = st.selectbox('Long Exit Condition', conditions, key='long_exit_condition')
        long_exit_target = st.selectbox('Long Exit Target', against_options, key='long_exit_target')
        long_exit_against = st.selectbox('Long Exit Against', against_options, key='long_exit_against')

    if direction in ['Short Only', 'Both']:
        st.subheader('Short Conditions')
        short_entry_condition = st.selectbox('Short Entry Condition', conditions, key='short_entry_condition')
        short_entry_target = st.selectbox('Short Entry Target', against_options, key='short_entry_target')
        short_entry_against = st.selectbox('Short Entry Against', against_options, key='short_entry_against')

        short_exit_condition = st.selectbox('Short Exit Condition', conditions, key='short_exit_condition')
        short_exit_target = st.selectbox('Short Exit Target', against_options, key='short_exit_target')
        short_exit_against = st.selectbox('Short Exit Against', against_options, key='short_exit_against')

    entry_conditions = {
        'long': (long_entry_condition, long_entry_target, long_entry_against) if direction in ['Long Only', 'Both'] else None,
        'short': (short_entry_condition, short_entry_target, short_entry_against) if direction in ['Short Only', 'Both'] else None
    }
    exit_conditions = {
        'long': (long_exit_condition, long_exit_target, long_exit_against) if direction in ['Long Only', 'Both'] else None,
        'short': (short_exit_condition, short_exit_target, short_exit_against) if direction in ['Short Only', 'Both'] else None
    }

    if st.button('Run Backtest'):
        # Ensure the calculated indicators are added to the DataFrame
        for indicator, values in calculated_indicators.items():
            dff[indicator] = values

        entries = df.copy()
        exits = df.copy()

        if direction in ['Long Only', 'Both']:
            entries['long_entry'] = False
            exits['long_exit'] = False
            if entry_conditions['long']:
                condition, target, against = entry_conditions['long']
                if condition == 'Above':
                    entries['long_entry'] = dff[target] > dff[against]
                elif condition == 'Below':
                    entries['long_entry'] = dff[target] < dff[against]
                elif condition == 'Cross Over':
                    entries['long_entry'] = vbt.signals.crossed_above(dff[target], dff[against])
                elif condition == 'Cross Under':
                    entries['long_entry'] = vbt.signals.crossed_below(dff[target], dff[against])
            if exit_conditions['long']:
                condition, target, against = exit_conditions['long']
                if condition == 'Above':
                    exits['long_exit'] = dff[target] > dff[against]
                elif condition == 'Below':
                    exits['long_exit'] = dff[target] < dff[against]
                elif condition == 'Cross Over':
                    exits['long_exit'] = vbt.signals.crossed_above(dff[target], dff[against])
                elif condition == 'Cross Under':
                    exits['long_exit'] = vbt.signals.crossed_below(dff[target], dff[against])

        # Short entry conditions
        if direction in ['Short Only', 'Both']:
            entries['short_entry'] = False
            exits['short_exit'] = False
            if entry_conditions['short']:
                condition, target, against = entry_conditions['short']
                if condition == 'Above':
                    entries['short_entry'] = dff[target] > dff[against]
                elif condition == 'Below':
                    entries['short_entry'] = dff[target] < dff[against]
                elif condition == 'Cross Over':
                    entries['short_entry'] = vbt.signals.crossed_above(dff[target], dff[against])
                elif condition == 'Cross Under':
                    entries['short_entry'] = vbt.signals.crossed_below(dff[target], dff[against])
            if exit_conditions['short']:
                condition, target, against = exit_conditions['short']
                if condition == 'Above':
                    exits['short_exit'] = dff[target] > dff[against]
                elif condition == 'Below':
                    exits['short_exit'] = dff[target] < dff[against]
                elif condition == 'Cross Over':
                    exits['short_exit'] = vbt.signals.crossed_above(dff[target], dff[against])
                elif condition == 'Cross Under':
                    exits['short_exit'] = vbt.signals.crossed_below(dff[target], dff[against])

        portfolio = vbt.Portfolio.from_signals(
            close=df,
            entries=entries['long_entry'] if 'long_entry' in entries else entries['short_entry'],
            exits=exits['long_exit'] if 'long_exit' in exits else exits['short_exit'],
            init_cash=initial_cash,
            size=trade_amount,
            direction='both',
            freq='1d'
        )

        st.write("Portfolio Stats:")
        st.write(portfolio.stats())

        st.write("Portfolio Value Chart:")
        st.plotly_chart(portfolio.plot(), use_container_width=True)

        st.write("Trades Records:")
        st.write(portfolio.trades.records_readable)

        st.write("Drawdowns Chart:")
        st.plotly_chart(portfolio.drawdowns.plot(), use_container_width=True)
        
        st.write("Drawdowns Records:")
        st.write(portfolio.drawdowns.records_readable)