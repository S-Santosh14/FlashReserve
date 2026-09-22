import streamlit as st

from frontend.components.poster import render_poster
from frontend.utils.api import APIError, make_mock_payment
from frontend.utils.navigation import breadcrumb, page_header
from frontend.utils.session import currency, go


def render():
    booking = st.session_state.booking
    if not booking:
        go("checkout")
        return
    event = booking.get("event") or {}
    total = booking["amount"]
    page_header("DEMO / MOCK PAYMENT", "Complete your booking", "Choose a payment method to reserve your seats.", "← Checkout", "checkout", "🏠 Home", "home")
    breadcrumb(["Home", "Events", event.get("title", "Event"), "Checkout", "Payment"])
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
            try:
                result = make_mock_payment(booking["id"], total, st.session_state.auth_token)
            except APIError as error:
                st.error(error.message)
            else:
                payment = result.get("payment", {})
                booking["status"] = "Confirmed"
                booking["transaction_id"] = payment.get("transactionId", "")
                st.session_state.payment_status = "successful"
                st.session_state.booking = booking
                go("confirmation")
        if st.button("Back to summary", key="pay_back"):
            go("checkout")
    with order_col:
        render_poster(event, key=f"payment-{booking['id']}")
        st.markdown(f"<div class='summary-card'><div class='section-kicker'>YOUR ORDER</div><h3>{event.get('title', 'FlashReserve booking')}</h3><div class='summary-line'><span>{event.get('short_date', '')} · {event.get('time', '')}</span></div><div class='summary-line'><span>Seats</span><b>{', '.join(booking['seats'])}</b></div><div class='summary-total'><span>TO PAY</span><strong>{currency(total)}</strong></div></div>", unsafe_allow_html=True)
        st.markdown("<p class='secure-note'>This is a simulated payment form for the FlashReserve frontend prototype.</p>", unsafe_allow_html=True)
