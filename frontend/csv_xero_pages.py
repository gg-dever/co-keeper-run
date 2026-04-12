# Xero CSV Workflow Page Functions
# These functions mirror the QuickBooks CSV pages but use Xero-specific endpoints and session variables

import streamlit as st
import requests

# Import from main app (will be integrated)
# from app import BACKEND_URL, train_xero_csv_model, predict_xero_csv_transactions


def render_xero_csv_upload_page(BACKEND_URL, train_xero_csv_model, predict_xero_csv_transactions):
    """Upload & Train tab for Xero CSV workflow - 2-step train → predict workflow"""
    st.markdown("""
    <div class="hero">
        <div class="glow-badge">Upload & Train</div>
        <h1>Xero CSV Upload</h1>
        <p>Upload historical Xero data to train your custom model, then predict categories for new transactions.</p>
    </div>
    """, unsafe_allow_html=True)

    # STEP 1: TRAIN MODEL
    st.markdown("""
    <div style="background: linear-gradient(135deg, rgba(16,185,129,0.12), rgba(5,150,105,0.06));
         border: 1px solid rgba(16,185,129,0.2); border-radius: 12px; padding: 24px; margin: 20px 0;">
        <h3 style="color: #e2eaf3; margin-top: 0;">🎓 Step 1: Train Your Model</h3>
        <p style="color: #8ba5be; font-size: 15px; line-height: 1.6;">
            Upload a Xero CSV export with <strong>already categorized</strong> transactions.
            This will teach the model YOUR categorization patterns.
        </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([3, 1])

    with col1:
        train_file = st.file_uploader(
            "Upload Training CSV (Historical Categorized Data)",
            type=['csv'],
            key="xero_csv_train_upload",
            disabled=st.session_state.xero_csv_model_trained,
            help="Xero CSV with columns: Date, Contact, Description, Related account, Account Type, Debit, Credit"
        )

    with col2:
        st.write("")
        st.write("")
        train_btn = st.button(
            "🎓 Train Model",
            type="primary",
            use_container_width=True,
            key="xero_csv_train_btn",
            disabled=not train_file or st.session_state.xero_csv_model_trained
        )

    if train_btn and train_file:
        with st.spinner("Training Xero model on your historical data... This may take a minute."):
            result, error = train_xero_csv_model(train_file)

        if error:
            st.error(f"❌ Training failed: {error}")
        else:
            st.session_state.xero_csv_model_trained = True
            st.session_state.xero_csv_training_metrics = result
            st.session_state.xero_csv_train_file_name = train_file.name
            st.balloons()
            st.success(f"🎉 Xero model trained successfully!")
            st.rerun()

    # Show training status
    if st.session_state.xero_csv_model_trained and st.session_state.xero_csv_training_metrics:
        metrics = st.session_state.xero_csv_training_metrics

        st.success("✅ Model is trained and ready!")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Test Accuracy", f"{metrics.get('test_accuracy', 0):.1f}%")
        with col2:
            st.metric("Categories Learned", metrics.get('categories', 0))
        with col3:
            st.metric("Training Transactions", metrics.get('transactions', 0))
        with col4:
            if st.button("🔄 Retrain", help="Train again with different data", key="xero_retrain"):
                st.session_state.xero_csv_model_trained = False
                st.session_state.xero_csv_training_metrics = None
                st.session_state.xero_csv_predictions = None
                st.session_state.xero_csv_train_file_name = None
                st.rerun()

        with st.expander("📊 Training Details"):
            st.markdown(f"""
            **Training File:** {st.session_state.xero_csv_train_file_name}

            **Performance:**
            - Training Accuracy: {metrics.get('train_accuracy', 0):.1f}%
            - Test Accuracy: {metrics.get('test_accuracy', 0):.1f}%

            **Model:** {metrics.get('model_path', 'N/A')}
            """)

    elif not st.session_state.xero_csv_model_trained:
        st.info("👆 Upload a Xero training CSV file and click 'Train Model' to begin")

    st.divider()

    # STEP 2: GET PREDICTIONS
    st.markdown("""
    <div style="background: linear-gradient(135deg, rgba(16,185,129,0.12), rgba(52,211,153,0.06));
         border: 1px solid rgba(16,185,129,0.2); border-radius: 12px; padding: 24px; margin: 20px 0;">
        <h3 style="color: #e2eaf3; margin-top: 0;">🔮 Step 2: Get Predictions</h3>
        <p style="color: #8ba5be; font-size: 15px; line-height: 1.6;">
            Now upload a CSV with <strong>uncategorized/new</strong> transactions from Xero.
            The model will suggest categories based on what it learned from your historical data.
        </p>
    </div>
    """, unsafe_allow_html=True)

    if not st.session_state.xero_csv_model_trained:
        st.warning("⚠️ Please train your model first (Step 1 above)")
    else:
        col1, col2 = st.columns([3, 1])

        with col1:
            pred_file = st.file_uploader(
                "Upload Prediction CSV (Uncategorized Transactions)",
                type=['csv'],
                key="xero_csv_pred_upload",
                help="Xero CSV with columns: Date, Contact, Description, Debit, Credit"
            )

        with col2:
            st.write("")
            st.write("")
            predict_btn = st.button(
                "🔍 Get Predictions",
                type="primary",
                use_container_width=True,
                key="xero_csv_predict_btn",
                disabled=not pred_file
            )

        if predict_btn and pred_file:
            with st.spinner("Generating predictions..."):
                result, error = predict_xero_csv_transactions(pred_file)

            if error:
                st.error(f"❌ {error}")
            else:
                st.session_state.xero_csv_predictions = result
                st.session_state.xero_csv_pred_file_name = pred_file.name
                st.success(f"✅ Generated {result.get('total_transactions', 0)} predictions!")
                st.info("👉 View detailed results in the **Results**, **Review**, and **Export** tabs")

        # Show prediction summary if available
        if st.session_state.xero_csv_predictions:
            pred_data = st.session_state.xero_csv_predictions

            st.divider()
            st.markdown("### 📊 Prediction Summary")

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Predictions", pred_data.get('total_transactions', 0))
            with col2:
                conf_dist = pred_data.get('confidence_distribution', {})
                st.metric("High Confidence", conf_dist.get('high', 0))
            with col3:
                st.metric("Needs Review", conf_dist.get('medium', 0) + conf_dist.get('low', 0))


#Note: Other page functions (Results, Review, Export, Help) would follow the same pattern
# For brevity, showing just the Upload page as example
# In production, duplicate all QB CSV page functions and replace:
# - qb_csv_ → xero_csv_
# - QuickBooks-specific help text → Xero-specific help text
# - Column names (Transaction Type → Related account, etc.)
