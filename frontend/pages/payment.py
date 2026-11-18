import uuid

import streamlit as st

from frontend.components.poster import render_poster
from frontend.utils.api import APIError, make_mock_payment
from frontend.utils.navigation import breadcrumb, page_header
from frontend.utils.session import currency, go, render_reservation_countdown


def render():
    booking = st.session_state.booking
    if not booking:
        go("checkout")
        return
    if booking.get("status") == "Confirmed":
        go("confirmation")
        return
    event = booking.get("event") or {}
    total = booking["amount"]
    payment_record = booking.get("payment") or {}
    payment_pending = payment_record.get("status") == "pending"
    if payment_pending:
        st.session_state.payment_idempotency_key = payment_record.get("idempotencyKey") or st.session_state.payment_idempotency_key
        st.session_state.payment_attempt_signature = (
            f"{booking['id']}:{payment_record.get('method')}:{payment_record.get('mockOutcome')}"
        )
    page_header("DEMO / MOCK PAYMENT", "Complete your booking", "Choose a method and a mock outcome for this test payment.", "← Checkout", "checkout", "🏠 Home", "home")
    breadcrumb(["Home", "Events", event.get("title", "Event"), "Checkout", "Payment"])
    form_col, order_col = st.columns([1.2, 0.8], gap="large")
    with form_col:
        method_options = ["UPI", "Card", "Net Banking", "Wallet"]
        method_names = {"UPI": "UPI", "CARD": "Card", "NET_BANKING": "Net Banking", "WALLET": "Wallet"}
        selected_method = method_names.get(payment_record.get("method"), "UPI")
        method_label = st.radio(
            "Payment method",
            method_options,
            index=method_options.index(selected_method),
            horizontal=True,
            disabled=payment_pending,
        )
        method = {"Card": "CARD", "Net Banking": "NET_BANKING", "Wallet": "WALLET"}.get(method_label, "UPI")
        outcome_options = ["success", "failed", "pending", "timeout"]
        selected_outcome = payment_record.get("mockOutcome", "success") if payment_pending else "success"
        outcome = st.selectbox(
            "Mock payment result",
            outcome_options,
            index=outcome_options.index(selected_outcome),
            disabled=payment_pending,
        )
        st.markdown("<div class='payment-form'>", unsafe_allow_html=True)
        if method == "UPI":
            st.text_input("UPI ID", placeholder="name@bank")
        elif method == "CARD":
            st.text_input("Card number", placeholder="1234  5678  9012  3456")
            expiry, cvv = st.columns(2)
            with expiry:
                st.text_input("Expiry", placeholder="MM / YY")
            with cvv:
                st.text_input("CVV", placeholder="•••", type="password")
        elif method == "NET_BANKING":
            st.selectbox("Choose your bank", ["Select your bank", "HDFC Bank", "ICICI Bank", "State Bank of India"])
        else:
            st.selectbox("Choose your wallet", ["Select your wallet", "Paytm", "PhonePe", "Amazon Pay"])
        st.markdown("</div>", unsafe_allow_html=True)
        render_reservation_countdown(st.session_state.lock_expires_at or booking.get("expires_at"))
        terminal_status = booking.get("status") in {"Failed", "Expired", "Cancelled"}
        action_label = "Check payment status" if payment_pending else f"Pay {currency(total)}"
        if not terminal_status and st.button(action_label, key="pay_now", type="primary", width="stretch"):
            attempt_signature = f"{booking['id']}:{method}:{outcome}"
            if st.session_state.payment_attempt_signature != attempt_signature:
                st.session_state.payment_idempotency_key = uuid.uuid4().hex
                st.session_state.payment_attempt_signature = attempt_signature
            idempotency_key = st.session_state.payment_idempotency_key
            st.session_state.payment_idempotency_key = idempotency_key
            try:
                with st.spinner("Processing the payment response…"):
                    result = make_mock_payment(
                        booking["id"],
                        total,
                        st.session_state.auth_token,
                        method,
                        outcome,
                        idempotency_key,
                    )
            except APIError as error:
                st.error(error.message)
            else:
                payment = result.get("payment", {})
                updated_booking = result.get("booking") or booking
                updated_booking["transaction_id"] = payment.get("transactionId", "")
                updated_booking["payment_status"] = payment.get("status", result.get("status", "pending"))
                st.session_state.booking = updated_booking
                st.session_state.payment_status = updated_booking["payment_status"]
                if payment.get("status") == "success":
                    go("confirmation")
                elif payment.get("status") == "pending" or payment.get("status") == "processing":
                    st.info("Payment is pending. Your seat hold remains active until the countdown expires.")
                else:
                    st.error(f"Mock payment {payment.get('status', 'failed')}. The seats have been released.")
        if terminal_status and st.button("Choose seats again", key="payment_retry_seats", width="stretch"):
            go(
                "seats",
                booking=None,
                reservation_id=None,
                lock_expires_at=None,
                payment_idempotency_key=None,
                payment_attempt_signature=None,
            )
        if st.button("Back to summary", key="pay_back"):
            go("checkout")
    with order_col:
        render_poster(event, key=f"payment-{booking['id']}")
        st.markdown(f"<div class='summary-card'><div class='section-kicker'>YOUR ORDER</div><h3>{event.get('title', 'FlashReserve booking')}</h3><div class='summary-line'><span>{event.get('short_date', '')} · {event.get('time', '')}</span></div><div class='summary-line'><span>Seats</span><b>{', '.join(booking['seats'])}</b></div><div class='summary-total'><span>TO PAY</span><strong>{currency(total)}</strong></div></div>", unsafe_allow_html=True)
        st.markdown("<p class='secure-note'>Mock payment only. Payment input fields are not sent to or stored by the backend.</p>", unsafe_allow_html=True)
