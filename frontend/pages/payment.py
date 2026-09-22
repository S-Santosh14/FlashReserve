import streamlit as st

from frontend.data.dummy_data import get_event
from frontend.utils.session import currency, go


def render():
    event = get_event(st.session_state.selected_event)
    total = event["price"] * len(st.session_state.selected_seats)
    st.markdown("<div class='page-intro compact'><span class='eyebrow'>SECURE CHECKOUT</span><h1>Complete your booking</h1><p>Choose a payment method to reserve your seats.</p></div>", unsafe_allow_html=True)
    form_col, order_col = st.columns([1.2, 0.8], gap="large")
    with form_col:
        method = st.radio("Payment method", ["UPI", "Card", "Net Banking"], horizontal=True)
        st.markdown("<div class='payment-form'>", unsafe_allow_html=True)
        if method == "UPI":
            st.text_input("UPI ID", placeholder="name@bank")
        elif method == "Card":
            st.text_input("Card number", placeholder="1234  5678  9012  3456")
            expiry, cvv = st.columns(2)
            with expiry:
                st.text_input("Expiry", placeholder="MM / YY")
            with cvv:
                st.text_input("CVV", placeholder="•••", type="password")
        else:
            st.selectbox("Choose your bank", ["Select your bank", "HDFC Bank", "ICICI Bank", "State Bank of India"])
        st.markdown("</div>", unsafe_allow_html=True)
        if st.button(f"Pay {currency(total)}", key="pay_now", type="primary", use_container_width=True):
            st.session_state.payment_status = "successful"
            st.session_state.booking = {
                "id": "FR-6208145",
                "event_id": event["id"],
                "seats": list(st.session_state.selected_seats),
                "amount": total,
                "status": "Confirmed",
                "booked_on": "19 September 2026",
            }
            go("confirmation")
        if st.button("Back to summary", key="pay_back"):
            go("checkout")
    with order_col:
        st.markdown(f"<div class='summary-card'><div class='section-kicker'>YOUR ORDER</div><h3>{event['title']}</h3><div class='summary-line'><span>{event['short_date']} · {event['time']}</span></div><div class='summary-line'><span>Seats</span><b>{', '.join(st.session_state.selected_seats)}</b></div><div class='summary-total'><span>TO PAY</span><strong>{currency(total)}</strong></div></div>", unsafe_allow_html=True)
        st.markdown("<p class='secure-note'>This is a simulated payment form for the FlashReserve frontend prototype.</p>", unsafe_allow_html=True)
