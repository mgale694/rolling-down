import streamlit as st
import numpy as np
import numpy_financial as npf
import plotly.graph_objects as go

st.set_page_config(layout="wide")

st.title('Rolling Down the Yield Curve')

# Initialize the yield rates
yield_rate = np.array([0.04616, 0.04385, 0.04201, 0.04187, 0.04315, 0.04244, 0.04358, 0.04406, 0.04456, 0.04460])

# Yield rate input columns
yield_rate_cols = st.columns(len(yield_rate))
for i, col in enumerate(yield_rate_cols):
    yield_rate[i] = col.number_input(f"Rate for year {i+1}:", value=yield_rate[i] * 100, key=f"rate_{i}") / 100

# Calculate 1-year forward rates
one_yr_forward_rate = [yield_rate[0]] + [
    (1 + yield_rate[i+1])**(i+2) / (1 + yield_rate[i])**(i+1) - 1 for i in range(len(yield_rate) - 1)
]

# Display forward rates
forward_rate_cols = st.columns(len(one_yr_forward_rate))
for i, col in enumerate(forward_rate_cols):
    col.write(f"1-year forward rate for year {i+1}: {one_yr_forward_rate[i] * 100:.2f}%")

# Check forward rate logic
def check_forward_rate(yield_rate, one_yr_forward_rate):
    return any(rate < forward_rate for rate, forward_rate in zip(yield_rate, one_yr_forward_rate))

if not check_forward_rate(yield_rate, one_yr_forward_rate):
    st.warning("The yield rates are greater than the 1-year forward rates. Strategy not advised.")

cols = st.columns([3, 1])
with cols[0]:
    # Plot the yield curve and forward rates
    st.subheader("Yield Curve and Forward Rates Visualization")
    years = np.arange(1, len(yield_rate) + 1)

    fig = go.Figure()
    # Add yield curve
    fig.add_trace(
        go.Scatter(
            x=years,
            y=yield_rate * 100,
            mode='lines+markers',
            name='Yield Curve',
            line=dict(color='blue'),
        )
    )
    # Add forward rates
    fig.add_trace(
        go.Scatter(
            x=years,
            y=np.array(one_yr_forward_rate) * 100,
            mode='lines+markers',
            name='1-Year Forward Rates',
            line=dict(color='green', dash='dot'),
        )
    )

    # Update layout
    fig.update_layout(
        title="Yield Curve and Forward Rates",
        xaxis_title="Year",
        yaxis_title="Rate (%)",
        legend_title="Legend",
        template="plotly_white"
    )

    st.plotly_chart(fig, use_container_width=True)
with cols[1]:
    st.subheader("User Inputs")
    # Input fields for NOTIONAL_VALUE, MATURITY, INVESTMENT_HORIZON, COUPON_PERCENTAGE
    notional_value = st.number_input("Notional Value ($):", value=100, step=10000)
    maturity = st.number_input("Maturity (years):", value=10, step=1, min_value=1)
    investment_horizon = st.number_input("Investment Horizon (years):", value=3, step=1, min_value=1)
    coupon_percentage = st.number_input("Coupon Percentage (%):", value=0.00375, step=0.0001, format="%.4f", min_value=0.0000)

with st.expander("Show Calculations"):
    st.subheader("Cash Flows")
    cash_flows = np.full(maturity, notional_value * coupon_percentage)
    cash_flows[-1] += notional_value
    cash_flows_cols = st.columns(len(cash_flows))
    for i, col in enumerate(cash_flows_cols):
        col.metric(f"Year {i+1}", f"${cash_flows[i]:,.2f}")

    st.subheader("Present Value Cash Flows")
    pv_cash_flow = [cf / (1 + yield_rate[i])**(i+1) for i, cf in enumerate(cash_flows)]
    pv_cash_flow_cols = st.columns(len(pv_cash_flow))
    for i, col in enumerate(pv_cash_flow_cols):
        col.metric(f"Year {i+1}", f"${pv_cash_flow[i]:,.2f}")

    bond_price = np.sum(pv_cash_flow)
    st.metric(f"Bond Price", f"${bond_price:,.2f}")

    st.subheader("Selling the Bond Early")
    new_cash_flows = cash_flows[investment_horizon-1:]
    new_pv_cash_flow = [cf / (1 + yield_rate[i])**(i+1) for i, cf in enumerate(new_cash_flows)]

    interest_flows = cash_flows[:investment_horizon-1]
    interest_flows_pv = [cf * (1 + yield_rate[i])**(i+1) for i, cf in enumerate(interest_flows[:-1])] + [interest_flows[-1]]

    new_pv_and_interest_cash_flow = interest_flows_pv + new_pv_cash_flow

    new_pv_and_interest_cash_flow_cols = st.columns(len(new_pv_and_interest_cash_flow))
    for i, col in enumerate(new_pv_and_interest_cash_flow_cols):
        if i < investment_horizon-2:
            col.metric(f"Year {i+1} (interest)", f"${new_pv_and_interest_cash_flow[i]:,.2f}")
        elif i == investment_horizon-2:
            col.metric(f"Year {i+1} (current)", f"${new_pv_and_interest_cash_flow[i]:,.2f}")
        else:
            col.metric(f"Year {i+1}", f"${new_pv_and_interest_cash_flow[i]:,.2f}")

    new_bond_price = np.sum(new_pv_cash_flow)
    cols = st.columns(maturity)
    cols[investment_horizon-1].metric(f"New Bond Price - year {investment_horizon}", f"${new_bond_price:,.2f}")

st.subheader("Returns")
cols = st.columns([1, 3])
with cols[0]:
    total_return_amount = new_bond_price + sum(interest_flows_pv)
    st.metric(f"Total Return Amount", f"${total_return_amount:,.2f}")

    total_return = total_return_amount / bond_price - 1
    st.metric(f"Total Return (%)", f"{total_return * 100:.2f}%")

    rate_to_maturity = npf.rate(maturity, notional_value * coupon_percentage, -bond_price, notional_value) # = calculate_rate(maturity, notional_value * coupon_percentage, -bond_price, notional_value)
    st.metric(f"Rate to Maturity (%)", f"{rate_to_maturity * 100:.2f}%")

    yoy_total_return = (total_return_amount / bond_price)**(1/(investment_horizon-1)) - 1
    st.metric(f"Year-over-Year Total Return (%)", f"{yoy_total_return * 100:.2f}%")

    total_interest = sum(interest_flows_pv - cash_flows[:investment_horizon-1])
    st.metric(f"Total Interest Earned", f"${total_interest:.2f}")

    capital_gain = total_return_amount - bond_price - total_interest
    st.metric(f"Capital Gains", f"${capital_gain:.2f}")

with cols[1]:
    st.subheader("Cash Flows Visualization (Line Charts)")

    # Years for plotting
    full_years = np.arange(1, maturity)

    # Create the figure
    fig = go.Figure()

    # Add original cash flows
    fig.add_trace(
        go.Scatter(
            x=full_years,
            y=cash_flows,
            mode='lines+markers',
            name="Cash Flows",
            line=dict(color='blue')
        )
    )

    # Add present value of cash flows
    fig.add_trace(
        go.Scatter(
            x=full_years,
            y=pv_cash_flow,
            mode='lines+markers',
            name="PV Cash Flows",
            line=dict(color='green')
        )
    )

    # Add remaining PV cash flows and interest flows
    fig.add_trace(
        go.Scatter(
            x=full_years,
            y=new_pv_and_interest_cash_flow,
            mode='lines+markers',
            name="Interest & New PV Cash Flows",
            line=dict(color='orange', dash='dot')
        )
    )

    # Update layout
    fig.update_layout(
        title="Cash Flows and Present Value Visualization",
        xaxis_title="Year",
        yaxis_title="Amount ($)",
        legend_title="Legend",
        template="plotly_white"
    )

    st.plotly_chart(fig, use_container_width=True)
